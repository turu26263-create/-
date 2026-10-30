//+------------------------------------------------------------------+
//| Wagamama_Nuke_M5_EA.mq5  5分足わがまま版 v0.2「抜け」              |
//| 研究台(kenkyu_kousoku.py)で 2021〜22 で探し、2023 を1回だけ見た形 |
//|   直近36本の高値/安値を終値で抜けた確定足 → 次の足の始値で抜けた向きへ |
//|   ロンドン〜NYの時間だけ(UTC 7〜17時)                             |
//|   網 ATR14x3、利確 ATR14x4、48本(4時間)で時間切れ                  |
//| 試験機の数字(0.1ロット・スプレッド0.5p):                         |
//|   2021 +317p / 2022 +1843p / 2023(見ていない年)+473p、PF1.11       |
//|   スプレッド1.0pだと 2021 −237p。スプレッドの狭い口座でないと取れない |
//+------------------------------------------------------------------+
#property copyright "takuchin"
#property version   "0.20"

#include <Trade\Trade.mqh>

input double Lots          = 0.10;
input long   Magic         = 5053000;
input int    BreakBars     = 36;     // 直近何本の高安を抜けたか
input double SlAtr         = 3.0;
input double TpAtr         = 4.0;
input int    MaxBars       = 48;
input int    GmtOffset     = 2;      // サーバー時刻 − UTC(冬2・夏3 が多い)
input bool   AutoUsDst     = true;   // 米国の夏時間の間は GmtOffset+1
input int    UtcStart      = 7;
input int    UtcEnd        = 17;
input double MaxSpreadPips = 1.0;

CTrade trade;
int hAtr;
datetime g_lastBar = 0;
double g_pip;
int g_in = 0, g_cnt[4];            // 利確・網・時間切れ・その他
double g_pnl[4];
string RSN[4] = {"利確", "網", "時間切れ", "その他"};
int g_why = 3;

int OnInit()
{
   g_pip = (_Digits == 3 || _Digits == 5) ? _Point * 10 : _Point;
   hAtr = iATR(_Symbol, PERIOD_M5, 14);
   if(hAtr == INVALID_HANDLE) return INIT_FAILED;
   trade.SetExpertMagicNumber(Magic);
   ArrayInitialize(g_cnt, 0); ArrayInitialize(g_pnl, 0.0);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   int tot = 0; double pt = 0;
   for(int r = 0; r < 4; r++) { tot += g_cnt[r]; pt += g_pnl[r]; }
   PrintFormat("カウンター,抜け,入った,%d回", g_in);
   for(int r = 0; r < 4; r++)
      if(g_cnt[r] > 0) PrintFormat("カウンター,抜け,%s,%d回(%.0f%%),%.0f円", RSN[r], g_cnt[r], 100.0 * g_cnt[r] / tot, g_pnl[r]);
   PrintFormat("カウンター,抜け,合計,%d回,%.0f円", tot, pt);
   IndicatorRelease(hAtr);
}

// 米国の夏時間(3月第2日曜〜11月第1日曜)
bool UsDst(datetime t)
{
   MqlDateTime d; TimeToStruct(t, d);
   if(d.mon < 3 || d.mon > 11) return false;
   if(d.mon > 3 && d.mon < 11) return true;
   MqlDateTime f = d; f.day = 1; f.hour = 0; f.min = 0; f.sec = 0;
   MqlDateTime w; TimeToStruct(StructToTime(f), w);
   int firstSun = 1 + (7 - w.day_of_week) % 7;
   if(d.mon == 3) return d.day >= firstSun + 7;
   return d.day < firstSun;
}

int UtcHour(datetime srv)
{
   int off = GmtOffset + ((AutoUsDst && UsDst(srv)) ? 1 : 0);
   MqlDateTime d; TimeToStruct(srv - off * 3600, d);
   return d.hour;
}

void OnTick()
{
   datetime bar = iTime(_Symbol, PERIOD_M5, 0);
   if(bar == g_lastBar) return;
   g_lastBar = bar;
   if(Bars(_Symbol, PERIOD_M5) < BreakBars + 20) return;

   // 持っている玉:時間切れ
   bool have = false;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(!PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      have = true;
      if(iBarShift(_Symbol, PERIOD_M5, (datetime)PositionGetInteger(POSITION_TIME)) >= MaxBars)
      {
         g_why = 2;
         if(trade.PositionClose(t)) have = false;
      }
   }
   if(have) return;

   int uh = UtcHour(bar);
   if(uh < UtcStart || uh >= UtcEnd) return;
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if((ask - bid) / g_pip > MaxSpreadPips) return;

   double c1 = iClose(_Symbol, PERIOD_M5, 1);
   double hi = iHigh(_Symbol, PERIOD_M5, iHighest(_Symbol, PERIOD_M5, MODE_HIGH, BreakBars, 2));   // 確定足の前の36本
   double lo = iLow(_Symbol, PERIOD_M5, iLowest(_Symbol, PERIOD_M5, MODE_LOW, BreakBars, 2));
   double a[1];
   if(CopyBuffer(hAtr, 0, 1, 1, a) != 1) return;
   double atr = a[0];

   if(c1 > hi)
   {
      if(trade.Buy(Lots, _Symbol, 0, NormalizeDouble(ask - SlAtr * atr, _Digits), NormalizeDouble(ask + TpAtr * atr, _Digits), "抜け")) g_in++;
   }
   else if(c1 < lo)
   {
      if(trade.Sell(Lots, _Symbol, 0, NormalizeDouble(bid + SlAtr * atr, _Digits), NormalizeDouble(bid - TpAtr * atr, _Digits), "抜け")) g_in++;
   }
}

void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
{
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD || !HistoryDealSelect(tr.deal)) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_MAGIC) != Magic || HistoryDealGetInteger(tr.deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;
   double p = HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_SWAP) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION);
   long why = HistoryDealGetInteger(tr.deal, DEAL_REASON);
   int r = (why == DEAL_REASON_TP) ? 0 : (why == DEAL_REASON_SL) ? 1 : g_why;
   g_why = 3;
   g_cnt[r]++; g_pnl[r] += p;
}

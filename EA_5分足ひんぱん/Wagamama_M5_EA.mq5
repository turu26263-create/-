//+------------------------------------------------------------------+
//| Wagamama_M5_EA.mq5  5分足わがまま版(クロードの好きに組んだ版)     |
//| たくちん「俺関係なく、わがままに取れるようにつくって」2026-10-30  |
//| 2つのエンジン:                                                    |
//|   A 静かな時間の戻し … 帯の±2σに刺さって戻った足を逆に取る       |
//|   B 動く時間の押し目 … 1時間の流れの向きに、5分の EMA20 の押しで乗る |
//| 判断は確定足(shift=1)。新しい足で1回だけ。数字は試験機で詰める前  |
//| 同じ決まりの Python 試験機:bt_wagamama.py                       |
//+------------------------------------------------------------------+
#property copyright "takuchin"
#property version   "0.10"

#include <Trade\Trade.mqh>

input double Lots          = 0.10;
input long   Magic         = 5052000;
input double MaxSpreadPips = 1.5;
input double DayLossYen    = 5000;   // その日の負けがこれを超えたら、その日は入らない(0で切)
//--- A 静かな時間の戻し
input bool   UseA          = true;
input int    A_StartHour   = 1;      // サーバー時刻。A_StartHour <= 時 < A_EndHour
input int    A_EndHour     = 8;
input int    A_BandPeriod  = 20;
input double A_BandSigma   = 2.0;
input double A_MaxAtrPips  = 4.0;    // 5分の ATR14 がこれ以下=静か
input double A_SlAtr       = 1.5;    // 網=入り値から ATR x 1.5
input double A_MinSlPips   = 5.0;
input int    A_MaxBars     = 12;     // 12本(1時間)で戻らなければ降りる
//--- B 動く時間の押し目
input bool   UseB          = true;
input int    B_StartHour   = 9;
input int    B_EndHour     = 20;
input int    B_H1Ema       = 50;
input int    B_FastEma     = 20;
input int    B_SlowEma     = 50;
input int    B_SwingBars   = 6;
input double B_SlPadPips   = 1.0;
input double B_MaxSlPips   = 15.0;
input double B_RR          = 1.5;    // 利確=網の幅 x 1.5
input double B_BeAtR       = 1.0;    // 1R 進んだら網を建値へ

CTrade trade;
int hBand, hAtr, hEf, hEs, hEh;
datetime g_lastBar = 0;
double   g_pip;
int      g_why = 4;          // A を自分で降ろした理由(OnTradeTransaction は後で来る)
#define MAGIC_A (Magic + 1)
#define MAGIC_B (Magic + 2)

//--- カウンター(エンジン x 降りた理由)
string RSN[5] = {"利確", "網", "時間切れ", "建値", "その他"};
int    g_cnt[2][5];
double g_pnl[2][5];
int    g_in[2];

int OnInit()
{
   g_pip = (_Digits == 3 || _Digits == 5) ? _Point * 10 : _Point;
   hBand = iBands(_Symbol, PERIOD_M5, A_BandPeriod, 0, A_BandSigma, PRICE_CLOSE);
   hAtr  = iATR(_Symbol, PERIOD_M5, 14);
   hEf   = iMA(_Symbol, PERIOD_M5, B_FastEma, 0, MODE_EMA, PRICE_CLOSE);
   hEs   = iMA(_Symbol, PERIOD_M5, B_SlowEma, 0, MODE_EMA, PRICE_CLOSE);
   hEh   = iMA(_Symbol, PERIOD_H1, B_H1Ema, 0, MODE_EMA, PRICE_CLOSE);
   if(hBand == INVALID_HANDLE || hAtr == INVALID_HANDLE || hEf == INVALID_HANDLE || hEs == INVALID_HANDLE || hEh == INVALID_HANDLE)
      return INIT_FAILED;
   ArrayInitialize(g_cnt, 0); ArrayInitialize(g_pnl, 0.0); ArrayInitialize(g_in, 0);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   string nm[2] = {"A戻し", "B押し目"};
   for(int e = 0; e < 2; e++)
   {
      int tot = 0; double pt = 0;
      for(int r = 0; r < 5; r++) { tot += g_cnt[e][r]; pt += g_pnl[e][r]; }
      PrintFormat("カウンター,%s,入った,%d回", nm[e], g_in[e]);
      for(int r = 0; r < 5; r++)
         if(g_cnt[e][r] > 0)
            PrintFormat("カウンター,%s,%s,%d回(%.0f%%),%.0f円", nm[e], RSN[r], g_cnt[e][r], 100.0 * g_cnt[e][r] / tot, g_pnl[e][r]);
      PrintFormat("カウンター,%s,合計,%d回,%.0f円", nm[e], tot, pt);
   }
   IndicatorRelease(hBand); IndicatorRelease(hAtr); IndicatorRelease(hEf); IndicatorRelease(hEs); IndicatorRelease(hEh);
}

double Buf(int h, int b, int s)
{
   double v[1];
   if(CopyBuffer(h, b, s, 1, v) != 1) return EMPTY_VALUE;
   return v[0];
}

bool InHours(int h, int st, int en) { return (st <= en) ? (h >= st && h < en) : (h >= st || h < en); }

// 自分の玉(magic ごと)。1つだけ持つ
bool GetPos(long mg, ulong &tk)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(!PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == mg) { tk = t; return true; }
   }
   return false;
}

double TodayPnl()
{
   MqlDateTime d; TimeToStruct(TimeCurrent(), d);
   d.hour = 0; d.min = 0; d.sec = 0;
   HistorySelect(StructToTime(d), TimeCurrent());
   double p = 0;
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong t = HistoryDealGetTicket(i);
      long mg = HistoryDealGetInteger(t, DEAL_MAGIC);
      if(mg != MAGIC_A && mg != MAGIC_B) continue;
      p += HistoryDealGetDouble(t, DEAL_PROFIT) + HistoryDealGetDouble(t, DEAL_SWAP) + HistoryDealGetDouble(t, DEAL_COMMISSION);
   }
   return p;
}

void OnTick()
{
   datetime bar = iTime(_Symbol, PERIOD_M5, 0);
   if(bar == g_lastBar) return;
   g_lastBar = bar;
   if(Bars(_Symbol, PERIOD_M5) < 300) return;

   MqlDateTime dt; TimeToStruct(bar, dt);
   double o1 = iOpen(_Symbol, PERIOD_M5, 1), h1 = iHigh(_Symbol, PERIOD_M5, 1);
   double l1 = iLow(_Symbol, PERIOD_M5, 1),  c1 = iClose(_Symbol, PERIOD_M5, 1);
   double atr = Buf(hAtr, 0, 1);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   //--- 持っている玉の世話
   ulong tk;
   if(GetPos(MAGIC_A, tk))
   {
      // A:真ん中を利確に置き直す。A_MaxBars 本で時間切れ
      double mid = NormalizeDouble(Buf(hBand, 0, 1), _Digits);
      bool buy = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY;
      int held = iBarShift(_Symbol, PERIOD_M5, (datetime)PositionGetInteger(POSITION_TIME));
      if(held >= A_MaxBars) { g_why = 2; trade.PositionClose(tk); }
      else if((buy && mid > bid) || (!buy && mid < ask))
         trade.PositionModify(tk, PositionGetDouble(POSITION_SL), mid);
      else { g_why = 0; trade.PositionClose(tk); }   // もう真ん中を越えた
   }
   if(GetPos(MAGIC_B, tk))
   {
      // B:1R 進んだら網を建値へ
      bool buy = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY;
      double op = PositionGetDouble(POSITION_PRICE_OPEN), sl = PositionGetDouble(POSITION_SL), tp = PositionGetDouble(POSITION_TP);
      double r = MathAbs(tp - op) / B_RR;
      if(buy && sl < op && c1 >= op + B_BeAtR * r)  trade.PositionModify(tk, op, tp);
      if(!buy && sl > op && c1 <= op - B_BeAtR * r) trade.PositionModify(tk, op, tp);
   }

   //--- 入る前のふるい
   if((ask - bid) / g_pip > MaxSpreadPips) return;
   if(DayLossYen > 0 && TodayPnl() <= -DayLossYen) return;
   if(dt.day_of_week == 5 && dt.hour >= 20) return;          // 金曜の夜は入らない
   if(dt.hour == 23 && dt.min >= 30) return;                   // 0時のスプレッド広がりの前後
   if(dt.hour == 0 && dt.min < 30) return;

   //--- A 静かな時間の戻し
   if(UseA && InHours(dt.hour, A_StartHour, A_EndHour) && !GetPos(MAGIC_A, tk) && atr / g_pip <= A_MaxAtrPips)
   {
      double up = Buf(hBand, 1, 1), dn = Buf(hBand, 2, 1), mid = Buf(hBand, 0, 1);
      double slw = MathMax(A_SlAtr * atr, A_MinSlPips * g_pip);
      trade.SetExpertMagicNumber(MAGIC_A);
      if(h1 >= up && c1 < up && c1 < o1)            // 上に刺さって戻った陰線 → 売り
      {
         if(trade.Sell(Lots, _Symbol, 0, NormalizeDouble(bid + slw, _Digits), NormalizeDouble(mid, _Digits), "A戻し")) g_in[0]++;
      }
      else if(l1 <= dn && c1 > dn && c1 > o1)       // 下に刺さって戻った陽線 → 買い
      {
         if(trade.Buy(Lots, _Symbol, 0, NormalizeDouble(ask - slw, _Digits), NormalizeDouble(mid, _Digits), "A戻し")) g_in[0]++;
      }
   }

   //--- B 動く時間の押し目
   if(UseB && InHours(dt.hour, B_StartHour, B_EndHour) && !GetPos(MAGIC_B, tk))
   {
      double eh1 = Buf(hEh, 0, 1), eh2 = Buf(hEh, 0, 2);
      double hc1 = iClose(_Symbol, PERIOD_H1, 1);
      double ef = Buf(hEf, 0, 1), es = Buf(hEs, 0, 1);
      int up = (hc1 > eh1 && eh1 > eh2) ? 1 : (hc1 < eh1 && eh1 < eh2) ? -1 : 0;
      trade.SetExpertMagicNumber(MAGIC_B);
      if(up > 0 && ef > es && l1 <= ef && c1 > ef && c1 > o1)
      {
         double sl = iLow(_Symbol, PERIOD_M5, iLowest(_Symbol, PERIOD_M5, MODE_LOW, B_SwingBars, 1)) - B_SlPadPips * g_pip;
         double w = ask - sl;
         if(w > 0 && w <= B_MaxSlPips * g_pip)
            if(trade.Buy(Lots, _Symbol, 0, NormalizeDouble(sl, _Digits), NormalizeDouble(ask + B_RR * w, _Digits), "B押し目")) g_in[1]++;
      }
      else if(up < 0 && ef < es && h1 >= ef && c1 < ef && c1 < o1)
      {
         double sl = iHigh(_Symbol, PERIOD_M5, iHighest(_Symbol, PERIOD_M5, MODE_HIGH, B_SwingBars, 1)) + B_SlPadPips * g_pip;
         double w = sl - bid;
         if(w > 0 && w <= B_MaxSlPips * g_pip)
            if(trade.Sell(Lots, _Symbol, 0, NormalizeDouble(sl, _Digits), NormalizeDouble(bid - B_RR * w, _Digits), "B押し目")) g_in[1]++;
      }
   }
}

//--- カウンター:降りた理由
void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
{
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD || !HistoryDealSelect(tr.deal)) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;
   long mg = HistoryDealGetInteger(tr.deal, DEAL_MAGIC);
   int e = (mg == MAGIC_A) ? 0 : (mg == MAGIC_B) ? 1 : -1;
   if(e < 0) return;
   double p = HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_SWAP) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION);
   long why = HistoryDealGetInteger(tr.deal, DEAL_REASON);
   int r;
   if(why == DEAL_REASON_TP) r = 0;
   else if(why == DEAL_REASON_SL) r = (MathAbs(p) < 1.0) ? 3 : 1;   // 建値の網は「建値」
   else { r = g_why; g_why = 4; }
   g_cnt[e][r]++; g_pnl[e][r] += p;
}

//+------------------------------------------------------------------+
//| Hinpan_M5_EA.mq5  5分足ひんぱん(売りも買いも)                      |
//| 決まり帳:決まり帳_5分足ひんぱん_20261030.md                        |
//| 判断はすべて確定足(shift=1以上)。新しい5分足が出た時に1回だけ判定 |
//| 数字はすべて【置き換え】。まだコンパイル・照らしをしていない        |
//+------------------------------------------------------------------+
#property copyright "takuchin"
#property version   "0.10"

#include <Trade\Trade.mqh>

//--- 玉
input double Lots          = 0.10;   // 1単位(25%)の量
input int    MaxAdds       = 3;      // 入3 鳴神の足しの上限(25%x4 の残り3)
input long   Magic         = 5051000;
//--- 線
input int    MaFast        = 9;
input int    MaSlow        = 21;
input ENUM_MA_METHOD MaMethod = MODE_SMA;
input int    BandPeriod    = 21;
input int    ChikouShift   = 26;     // 遅行スパン(5分足スパンモデル側=26本前)
//--- 入1 ポン(貯め)
input int    TameBars      = 12;     // 直近N本
input int    TameMin       = 8;      // うちK本以上で遅行スパンが絡む
input int    WidthLookback = 100;    // 帯の幅を比べる本数
input double WidthRank     = 0.30;   // 下から3割以内=しぼみ
//--- だまし回避
input double AngleMin      = 10.0;   // 入らない1 これ未満はレンジ
input double AngleMax      = 55.0;   // 入らない2 これ超えは竿先
input int    AngleRangeBars= 150;    // 画面の縦=直近150本の高安を500ドット
input int    H1SlopeBars   = 3;      // 入らない3 1時間21の傾きを見る本数
input double MaxSpreadPips = 2.0;    // 入らない4
//--- 入3 鳴神
input double NaruSigma     = 2.0;    // 押し目の帯(±2σ)
input int    NaruLookback  = 6;      // 直近何本の中で帯に触れたか
//--- 出口
input double TpSigma       = 3.5;    // 出1
input int    SwingBars     = 12;     // 出4 揺れの外=直近12本の安値/高値
input double SwingPadPips  = 2.0;    // 出4 その2ピップ外
input bool   ExitNextGoo   = true;   // 出3 次のグーで降りる
input int    FridayCloseHour = 23;   // 出5 金曜この時(サーバー時刻)で全部降りる。-1で切
//--- 記録
input bool   WriteEntryCsv = true;

CTrade trade;
int hMaF, hMaS, hBand, hMaH1;
datetime g_lastBar = 0;
bool     g_ponUsed = false;       // この貯めのポンは使った
int      g_addsBuy = 0, g_addsSell = 0;
bool     g_naruDoneBuy = false, g_naruDoneSell = false; // この押しで鳴神済み
long     g_closeId[];             // 自分で降ろした玉と理由(OnTradeTransaction は後で来るので覚えておく)
string   g_closeWhy[];
double   g_pip;

//--- カウンター(降りた理由 x 種類)
#define NKIND 3
#define NREASON 6
string KIND_NAME[NKIND]     = {"ポン","921_219","鳴神"};
string REASON_NAME[NREASON] = {"利確3.5σ","逆の交差","次のグー","網","金曜","その他"};
int    g_entryCnt[NKIND];
int    g_exitCnt[NKIND][NREASON];
double g_exitPnl[NKIND][NREASON];

//--- ロウソク・カウンター(網に掛かった足は確定してから見る)
struct NetHit { datetime t; double sl; int dir; int kind; };
NetHit g_hits[];
int    g_candleN[NKIND], g_wickOnly[NKIND];
double g_candleLen[NKIND];
int    g_csv = INVALID_HANDLE;

//+------------------------------------------------------------------+
int OnInit()
{
   g_pip = (_Digits == 3 || _Digits == 5) ? _Point * 10 : _Point;
   hMaF  = iMA(_Symbol, PERIOD_M5, MaFast, 0, MaMethod, PRICE_CLOSE);
   hMaS  = iMA(_Symbol, PERIOD_M5, MaSlow, 0, MaMethod, PRICE_CLOSE);
   hBand = iBands(_Symbol, PERIOD_M5, BandPeriod, 0, 1.0, PRICE_CLOSE); // 1σの帯。kσは中心+k*(上-中心)
   hMaH1 = iMA(_Symbol, PERIOD_H1, MaSlow, 0, MaMethod, PRICE_CLOSE);
   if(hMaF == INVALID_HANDLE || hMaS == INVALID_HANDLE || hBand == INVALID_HANDLE || hMaH1 == INVALID_HANDLE)
      return INIT_FAILED;
   trade.SetExpertMagicNumber(Magic);
   ArrayInitialize(g_entryCnt, 0);
   ArrayInitialize(g_exitCnt, 0);
   ArrayInitialize(g_exitPnl, 0.0);
   ArrayInitialize(g_candleN, 0);
   ArrayInitialize(g_wickOnly, 0);
   ArrayInitialize(g_candleLen, 0.0);
   if(WriteEntryCsv)
   {
      g_csv = FileOpen("hinpan_entries.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
      if(g_csv != INVALID_HANDLE)
         FileWrite(g_csv, "時刻", "種類", "向き", "値段", "網", "21角度", "川の位置σ", "遅行", "1時間21");
   }
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   PrintCounters();
   if(g_csv != INVALID_HANDLE) FileClose(g_csv);
   IndicatorRelease(hMaF); IndicatorRelease(hMaS); IndicatorRelease(hBand); IndicatorRelease(hMaH1);
}

//+------------------------------------------------------------------+
//| 線の値(shift の1本)                                               |
//+------------------------------------------------------------------+
double Buf(int h, int buf, int shift)
{
   double v[1];
   if(CopyBuffer(h, buf, shift, 1, v) != 1) return EMPTY_VALUE;
   return v[0];
}
double Mid(int s)   { return Buf(hBand, 0, s); }
double Sig(int s)   { return Buf(hBand, 1, s) - Buf(hBand, 0, s); }   // 1σの幅
double Band(int s, double k) { return Mid(s) + k * Sig(s); }

// 遅行スパン:足 s の終値を、s+ChikouShift 本前の足と比べる。+1上抜け/-1下抜け/0絡み
int Chikou(int s)
{
   double c = iClose(_Symbol, PERIOD_M5, s);
   int    p = s + ChikouShift;
   if(c > iHigh(_Symbol, PERIOD_M5, p)) return 1;
   if(c < iLow(_Symbol, PERIOD_M5, p))  return -1;
   return 0;
}

// 帯の幅(1σ)が直近 WidthLookback 本の下から WidthRank 以内か
bool Squeezed(int s)
{
   double w = Sig(s);
   int below = 0;
   for(int i = s + 1; i <= s + WidthLookback; i++)
      if(Sig(i) < w) below++;
   return below <= WidthRank * WidthLookback;
}

// 21の角度(画面の見た目。横1本6ドット、縦は直近150本の高安=500ドット、3本分)
double Angle21(int s)
{
   double hi = iHigh(_Symbol, PERIOD_M5, iHighest(_Symbol, PERIOD_M5, MODE_HIGH, AngleRangeBars, s));
   double lo = iLow(_Symbol, PERIOD_M5, iLowest(_Symbol, PERIOD_M5, MODE_LOW, AngleRangeBars, s));
   if(hi - lo <= 0) return 0;
   double dy = (Buf(hMaS, 0, s) - Buf(hMaS, 0, s + 3)) / (hi - lo) * 500.0;
   return MathArctan(dy / 18.0) * 180.0 / M_PI;
}

// 1時間21の向き(確定した1時間足で):+1上/-1下/0寝
int H1Dir()
{
   double a = Buf(hMaH1, 0, 1), b = Buf(hMaH1, 0, 1 + H1SlopeBars);
   if(a == EMPTY_VALUE || b == EMPTY_VALUE) return 0;
   if(a > b) return 1;
   if(a < b) return -1;
   return 0;
}

// 貯め:足 s から前 TameBars 本のうち TameMin 本以上で遅行が絡み、帯がしぼんでいる
bool Tame(int s)
{
   int k = 0;
   for(int i = s; i < s + TameBars; i++)
      if(Chikou(i) == 0) k++;
   return k >= TameMin && Squeezed(s);
}

//+------------------------------------------------------------------+
//| 自分の玉                                                          |
//+------------------------------------------------------------------+
int CountPos(int dir)
{
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(!PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      long ty = PositionGetInteger(POSITION_TYPE);
      if((dir > 0 && ty == POSITION_TYPE_BUY) || (dir < 0 && ty == POSITION_TYPE_SELL)) n++;
   }
   return n;
}

void CloseAll(int dir, string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(!PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      long ty = PositionGetInteger(POSITION_TYPE);
      if(dir != 0 && !((dir > 0 && ty == POSITION_TYPE_BUY) || (dir < 0 && ty == POSITION_TYPE_SELL))) continue;
      int n = ArraySize(g_closeId);
      ArrayResize(g_closeId, n + 1); ArrayResize(g_closeWhy, n + 1);
      g_closeId[n] = (long)t; g_closeWhy[n] = reason;
      if(!trade.PositionClose(t)) { ArrayResize(g_closeId, n); ArrayResize(g_closeWhy, n); }
   }
}

// 出1 の利確の値を、確定足の帯に合わせて置き直す
void MoveTp()
{
   double up = Band(1, TpSigma), dn = Band(1, -TpSigma);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong t = PositionGetTicket(i);
      if(!PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      double sl = PositionGetDouble(POSITION_SL);
      double tp = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? up : dn;
      tp = NormalizeDouble(tp, _Digits);
      bool buy = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
      double now = buy ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      if((buy && tp <= now) || (!buy && tp >= now)) continue;   // 置けない所には置かない
      if(MathAbs(tp - PositionGetDouble(POSITION_TP)) >= _Point)
         trade.PositionModify(t, sl, tp);
   }
}

//+------------------------------------------------------------------+
//| 入る                                                             |
//+------------------------------------------------------------------+
bool Open(int dir, int kind)
{
   double sl, tp, price;
   if(dir > 0)
   {
      price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      sl = iLow(_Symbol, PERIOD_M5, iLowest(_Symbol, PERIOD_M5, MODE_LOW, SwingBars, 1)) - SwingPadPips * g_pip;
      tp = Band(1, TpSigma);
      if(sl >= price || tp <= price) return false;
   }
   else
   {
      price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      sl = iHigh(_Symbol, PERIOD_M5, iHighest(_Symbol, PERIOD_M5, MODE_HIGH, SwingBars, 1)) + SwingPadPips * g_pip;
      tp = Band(1, -TpSigma);
      if(sl <= price || tp >= price) return false;
   }
   sl = NormalizeDouble(sl, _Digits);
   tp = NormalizeDouble(tp, _Digits);
   string cm = KIND_NAME[kind];
   bool ok = (dir > 0) ? trade.Buy(Lots, _Symbol, 0, sl, tp, cm) : trade.Sell(Lots, _Symbol, 0, sl, tp, cm);
   if(ok && (trade.ResultRetcode() == TRADE_RETCODE_DONE || trade.ResultRetcode() == TRADE_RETCODE_PLACED))
   {
      g_entryCnt[kind]++;
      if(g_csv != INVALID_HANDLE)
      {
         double sg = Sig(1);
         double pos = (sg > 0) ? (iClose(_Symbol, PERIOD_M5, 1) - Mid(1)) / sg : 0;
         FileWrite(g_csv, TimeToString(iTime(_Symbol, PERIOD_M5, 0), TIME_DATE | TIME_MINUTES), cm,
                   dir > 0 ? "買い" : "売り", DoubleToString(trade.ResultPrice(), _Digits), DoubleToString(sl, _Digits),
                   DoubleToString(Angle21(1), 1), DoubleToString(pos, 2), Chikou(1), H1Dir());
      }
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
void OnTick()
{
   datetime bar = iTime(_Symbol, PERIOD_M5, 0);
   if(bar == g_lastBar) return;          // 新しい足が出た時に1回だけ
   if(Bars(_Symbol, PERIOD_M5) < WidthLookback + ChikouShift + AngleRangeBars + 10) return;
   g_lastBar = bar;

   CheckNetCandles();

   double f1 = Buf(hMaF, 0, 1), f2 = Buf(hMaF, 0, 2);
   double s1 = Buf(hMaS, 0, 1), s2 = Buf(hMaS, 0, 2);
   if(f1 == EMPTY_VALUE || s2 == EMPTY_VALUE || Sig(1) == EMPTY_VALUE) return;
   double c1 = iClose(_Symbol, PERIOD_M5, 1), o1 = iOpen(_Symbol, PERIOD_M5, 1);

   bool cross921 = (f1 > s1 && f2 <= s2);
   bool cross219 = (f1 < s1 && f2 >= s2);
   int  ck1 = Chikou(1);
   bool goo = (ck1 == 0 && Squeezed(1));

   //--- 出5 金曜
   MqlDateTime dt; TimeToStruct(bar, dt);
   if(FridayCloseHour >= 0 && dt.day_of_week == 5 && dt.hour >= FridayCloseHour)
   {
      CloseAll(0, "金曜");
      return;
   }
   //--- 出2 逆の交差 / 出3 次のグー
   if(cross219) CloseAll(1, "逆の交差");
   if(cross921) CloseAll(-1, "逆の交差");
   if(ExitNextGoo && goo) CloseAll(0, "次のグー");

   int nb = CountPos(1), ns = CountPos(-1);
   if(nb == 0) { g_addsBuy = 0;  g_naruDoneBuy = false; }
   if(ns == 0) { g_addsSell = 0; g_naruDoneSell = false; }
   if(nb + ns > 0) MoveTp();

   //--- 貯め(ポンの前)。貯めが切れたら次のポンを待てる
   bool tame = Tame(2);
   if(!tame) g_ponUsed = false;

   //--- だまし回避のふるい
   double spr = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / g_pip;
   if(spr > MaxSpreadPips) return;
   int    h1  = H1Dir();
   double ang = Angle21(1);
   bool okBuy  = (h1 > 0 && ang >= AngleMin && ang <= AngleMax);
   bool okSell = (h1 < 0 && -ang >= AngleMin && -ang <= AngleMax);

   //--- 入1 ポン
   int ck2 = Chikou(2);
   if(tame && !g_ponUsed && ck1 != 0 && ck2 == 0)
   {
      g_ponUsed = true;                  // 1つの貯めにポン1回(ふるいで入らなくても使い切る)
      if(ck1 > 0 && okBuy && nb == 0 && ns == 0)  { Open(1, 0);  return; }
      if(ck1 < 0 && okSell && ns == 0 && nb == 0) { Open(-1, 0); return; }
   }
   //--- 入2 921/219
   if(cross921 && okBuy && nb == 0 && ns == 0 && c1 > f1 && c1 > s1 && ck1 > 0) { Open(1, 1);  return; }
   if(cross219 && okSell && ns == 0 && nb == 0 && c1 < f1 && c1 < s1 && ck1 < 0) { Open(-1, 1); return; }

   //--- 入3 鳴神(持っている向きに、押し目/戻りで1発)
   if(c1 > Mid(1)) g_naruDoneBuy = false;     // 真ん中を取り戻したら次の押しを待つ
   if(c1 < Mid(1)) g_naruDoneSell = false;
   if(nb > 0 && h1 > 0 && !goo && !g_naruDoneBuy && g_addsBuy < MaxAdds && c1 > o1)
   {
      bool touched = false;
      for(int i = 1; i <= NaruLookback; i++)
         if(iLow(_Symbol, PERIOD_M5, i) <= Band(i, -NaruSigma)) { touched = true; break; }
      if(touched && Open(1, 2)) { g_addsBuy++; g_naruDoneBuy = true; }
   }
   if(ns > 0 && h1 < 0 && !goo && !g_naruDoneSell && g_addsSell < MaxAdds && c1 < o1)
   {
      bool touched = false;
      for(int i = 1; i <= NaruLookback; i++)
         if(iHigh(_Symbol, PERIOD_M5, i) >= Band(i, NaruSigma)) { touched = true; break; }
      if(touched && Open(-1, 2)) { g_addsSell++; g_naruDoneSell = true; }
   }
}

//+------------------------------------------------------------------+
//| カウンター:降りた時に種類と理由を数える                           |
//+------------------------------------------------------------------+
int KindOf(string cm)
{
   for(int k = 0; k < NKIND; k++)
      if(StringFind(cm, KIND_NAME[k]) >= 0) return k;
   return 0;
}
int ReasonOf(string r)
{
   for(int i = 0; i < NREASON; i++)
      if(r == REASON_NAME[i]) return i;
   return NREASON - 1;
}

void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
{
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(tr.deal)) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_MAGIC) != Magic) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;

   long   posId = HistoryDealGetInteger(tr.deal, DEAL_POSITION_ID);
   double pnl   = HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_SWAP)
                + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION);
   long   why   = HistoryDealGetInteger(tr.deal, DEAL_REASON);

   // 入った時の注文コメントから種類を取る
   int kind = 0, dir = 1;
   if(HistorySelectByPosition(posId))
      for(int i = 0; i < HistoryDealsTotal(); i++)
      {
         ulong d = HistoryDealGetTicket(i);
         if(HistoryDealGetInteger(d, DEAL_ENTRY) == DEAL_ENTRY_IN)
         {
            kind = KindOf(HistoryDealGetString(d, DEAL_COMMENT));
            dir  = (HistoryDealGetInteger(d, DEAL_TYPE) == DEAL_TYPE_BUY) ? 1 : -1;
         }
      }
   int r;
   if(why == DEAL_REASON_TP)      r = 0;
   else if(why == DEAL_REASON_SL) r = 3;
   else
   {
      r = NREASON - 1;
      for(int i = ArraySize(g_closeId) - 1; i >= 0; i--)
         if(g_closeId[i] == posId)
         {
            r = ReasonOf(g_closeWhy[i]);
            ArrayRemove(g_closeId, i, 1); ArrayRemove(g_closeWhy, i, 1);
            break;
         }
   }
   g_exitCnt[kind][r]++;
   g_exitPnl[kind][r] += pnl;

   if(r == 3)   // 網:掛かった足は、その足が確定してから見る
   {
      int n = ArraySize(g_hits);
      ArrayResize(g_hits, n + 1);
      g_hits[n].t    = (datetime)HistoryDealGetInteger(tr.deal, DEAL_TIME);
      g_hits[n].sl   = HistoryDealGetDouble(tr.deal, DEAL_PRICE);
      g_hits[n].dir  = dir;
      g_hits[n].kind = kind;
   }
}

// ロウソク・カウンター:網に掛かった足が確定したら、長さ・ひげ・位置を見る
void CheckNetCandles()
{
   for(int n = ArraySize(g_hits) - 1; n >= 0; n--)
   {
      int s = iBarShift(_Symbol, PERIOD_M5, g_hits[n].t);
      if(s < 1) continue;                // まだ確定していない
      double o = iOpen(_Symbol, PERIOD_M5, s), h = iHigh(_Symbol, PERIOD_M5, s);
      double l = iLow(_Symbol, PERIOD_M5, s),  c = iClose(_Symbol, PERIOD_M5, s);
      double len = (h - l) / g_pip, body = MathAbs(c - o) / g_pip;
      double up  = (h - MathMax(o, c)) / g_pip, dn = (MathMin(o, c) - l) / g_pip;
      bool wickOnly = (g_hits[n].dir > 0) ? (c > g_hits[n].sl) : (c < g_hits[n].sl);
      double sg = Sig(s), pos = (sg > 0) ? (c - Mid(s)) / sg : 0;
      int lv = (int)MathFloor(pos) + 4; lv = MathMax(0, MathMin(7, lv));   // 8段:-3σの外〜+3σの外
      string ab9 = (c > Buf(hMaF, 0, s)) ? "9の上" : "9の下";
      int k = g_hits[n].kind;
      PrintFormat("ロウソク,1本,%s,%s,長さ%.1f,実体%.1f,上ひげ%.1f,下ひげ%.1f,段%d,%s,%s", KIND_NAME[k],
                  TimeToString(iTime(_Symbol, PERIOD_M5, s)), len, body, up, dn, lv, ab9,
                  wickOnly ? "ひげだけ" : "実体で渡った");
      g_candleN[k]++; g_candleLen[k] += len;
      if(wickOnly) g_wickOnly[k]++;
      ArrayRemove(g_hits, n, 1);
   }
}

void PrintCounters()
{
   for(int k = 0; k < NKIND; k++)
   {
      int tot = 0; double pt = 0;
      for(int r = 0; r < NREASON; r++) { tot += g_exitCnt[k][r]; pt += g_exitPnl[k][r]; }
      PrintFormat("カウンター,%s,入った,%d回", KIND_NAME[k], g_entryCnt[k]);
      for(int r = 0; r < NREASON; r++)
         if(g_exitCnt[k][r] > 0)
            PrintFormat("カウンター,%s,%s,%d回(%.0f%%),%.0f円", KIND_NAME[k], REASON_NAME[r], g_exitCnt[k][r],
                        tot > 0 ? 100.0 * g_exitCnt[k][r] / tot : 0, g_exitPnl[k][r]);
      PrintFormat("カウンター,%s,合計,%d回,%.0f円", KIND_NAME[k], tot, pt);
      if(g_candleN[k] > 0)
         PrintFormat("ロウソク,まとめ,%s,%d本,平均長さ%.1f,ひげだけ%.0f%%", KIND_NAME[k], g_candleN[k],
                     g_candleLen[k] / g_candleN[k], 100.0 * g_wickOnly[k] / g_candleN[k]);
   }
}
//+------------------------------------------------------------------+

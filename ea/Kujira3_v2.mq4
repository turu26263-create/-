//+------------------------------------------------------------------+
//| Kujira3_v2.mq4  今の決まった形(11-12)を MT4 に                    |
//| 2026-11-12 たくちん「mt4で回して」                                  |
//| 中身:クジラの刺身(売り買い)+ドテン買い+鯛の刺身+日足の押し目巡航    |
//|       +しあわせセット(レンジの箱。買い/売りは週足219の間だけ)       |
//| Kujira3_v1.mq5 を MT4 に写し、しあわせセットを足した。決まりは変えない |
//| 【未検証】クラウドに MetaEditor が無いので、コンパイル・テスターはまだ   |
//| 1時間足(H1)のチャートに貼る                                        |
//+------------------------------------------------------------------+
#property copyright "takuchin"
#property version   "2.00"
#property strict

//--- 決まった形(研究台と同じ値。変える時はたくちんの「ご」)
input double Lots          = 0.01;   // クジラ・ドテン・鯛・押し目の1玉のロット(決め打ち)
input int    MaxPos        = 5;      // クジラの同じ向きの玉の上限(5発)
input int    KaiK9         = 3;      // 許しの入りは日足の終値が9の向こうに何本続いてから
input double SaoSigma      = 2.0;    // 竿先:1時間の帯 ±2σ の外では入らない
input double TpSigma       = 4.0;    // 利確:4時間の帯 ±4.0σ(1本前の4時間足が閉じた時の線)
input double TsPips        = 550;    // TS:一番伸びた所から 550p
input bool   UseSell       = true;   // クジラの売り
input bool   UseDoten      = true;   // 売りの利確の後、1時間921を待ってドテン買い
input bool   UseTai        = true;   // 鯛の刺身(買いだけ)
input bool   UseOshime     = true;   // 日足の押し目巡航(売り買い・最大5玉)
input bool   UseShiawase   = true;   // しあわせセット(レンジの箱)
input double ShLots        = 0.01;   // しあわせセットの1単位のロット(1セット=刈る3+ため1)
input bool   ShUseSell     = true;   // しあわせセットの売り(週足219の間だけ)
input bool   UseYasumi     = true;   // GW 4/29-5/6 は新しく入らない
input int    AvoidHour     = 0;      // この時刻(サーバー)の足では入り・合図の降りをしない(次の足へ)
input double MaxSpreadPips = 5.0;    // 入る直前のスプレッドがこれより広ければ入らない(研究台には無い守り)
input int    SlipPoints    = 30;     // 許す滑り(ポイント)
input int    MagicBuy      = 26110901;
input int    MagicSell     = 26110902;
input int    MagicDoten    = 26110903;
input int    MagicTai      = 26110904;
input int    MagicOshB     = 26110905;
input int    MagicOshS     = 26110906;
input int    MagicShBK     = 26111201;   // しあわせ 買い 刈る
input int    MagicShBT     = 26111202;   // しあわせ 買い ため
input int    MagicShSK     = 26111203;   // しあわせ 売り 刈る
input int    MagicShST     = 26111204;   // しあわせ 売り ため

//--- しあわせセットの決まり(研究台 settei_kimari.json の shiawase と同じ)
#define SH_NFLIP 3      // レンジ:日足の遅行スパン(終値と21本前の終値の上下)が直近30日で3回以上入れ替わる
#define SH_WIN   30
#define SH_KAR   3      // 刈る3単位+ため1単位
#define SH_TAME  5      // ためは最大5
#define SH_TPK   2.0    // 刈る=反対の ±2σ
#define SH_TAMEK 3.5    // ため=±3.5σ
#define SH_NAKA  1.0    // 日足200の上下 1σ の中では入らない

//--- 状態
bool oIncr[2] = {false, false}, oArm[2] = {false, false}, oPend[2] = {false, false};
datetime oLastD = 0;
datetime lastBar = 0;
bool pendBuy = false, pendSell = false;
bool armDoten = false;
datetime lastHist = 0;              // ドテンの構え:ここより後に閉じた売りの利確を見る
double PIP;
//--- しあわせセット:日足が閉じるたびに作る値(閉じた日足 shDay の値)
datetime shDay = 0;
bool   shRng = false, shW219 = false;
double shMd = 0, shSd = 0, shE200 = 0, shBhi = 0, shBlo = 0;
//--- カウンター(降りた理由の数)
int cntTP = 0, cntSL = 0, cntSig = 0, cntSkipSpr = 0, cntSkipDup = 0, cntShIn = 0, cntShBox = 0;
string LOG = "Kujira3v2_log.csv";

//+------------------------------------------------------------------+
int OnInit()
{
   PIP = (Digits == 3 || Digits == 5) ? Point * 10 : Point;
   if(Period() != PERIOD_H1) Print("注意:H1 のチャートに貼ってください(今 ", Period(), ")");
   armDoten = GlobalVariableCheck(GVName("arm")) && GlobalVariableGet(GVName("arm")) > 0;
   pendBuy  = GlobalVariableCheck(GVName("pb")) && GlobalVariableGet(GVName("pb")) > 0;
   pendSell = GlobalVariableCheck(GVName("ps")) && GlobalVariableGet(GVName("ps")) > 0;
   oPend[0] = GlobalVariableCheck(GVName("ob")) && GlobalVariableGet(GVName("ob")) > 0;
   oPend[1] = GlobalVariableCheck(GVName("os")) && GlobalVariableGet(GVName("os")) > 0;
   lastHist = GlobalVariableCheck(GVName("lh")) ? (datetime)GlobalVariableGet(GVName("lh")) : TimeCurrent();
   Log("起動", 0, 0, 0, 0, "arm=" + (string)armDoten);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   string s = StringFormat("カウンター 利確=%d 網(TS・箱)=%d 合図で降り=%d スプレッドで見送り=%d 二重を止めた=%d しあわせ入り=%d 箱割れ=%d",
                           cntTP, cntSL, cntSig, cntSkipSpr, cntSkipDup, cntShIn, cntShBox);
   Print(s); Log("終わり", 0, 0, 0, 0, s);
}

//+------------------------------------------------------------------+
//| 道具                                                              |
//+------------------------------------------------------------------+
string GVName(string k) { return "K3v2_" + Symbol() + "_" + k; }
void SaveFlags()
{
   GlobalVariableSet(GVName("arm"), armDoten ? 1 : 0);
   GlobalVariableSet(GVName("pb"), pendBuy ? 1 : 0);
   GlobalVariableSet(GVName("ps"), pendSell ? 1 : 0);
   GlobalVariableSet(GVName("ob"), oPend[0] ? 1 : 0);
   GlobalVariableSet(GVName("os"), oPend[1] ? 1 : 0);
   GlobalVariableSet(GVName("lh"), (double)lastHist);
}

double D9(int s)    { return iMA(NULL, PERIOD_D1, 9, 0, MODE_EMA, PRICE_CLOSE, s); }
double D21(int s)   { return iMA(NULL, PERIOD_D1, 21, 0, MODE_EMA, PRICE_CLOSE, s); }
double D200(int s)  { return iMA(NULL, PERIOD_D1, 200, 0, MODE_EMA, PRICE_CLOSE, s); }
double H4_9(int s)  { return iMA(NULL, PERIOD_H4, 9, 0, MODE_EMA, PRICE_CLOSE, s); }
double H4_21(int s) { return iMA(NULL, PERIOD_H4, 21, 0, MODE_EMA, PRICE_CLOSE, s); }
double H1_9(int s)  { return iMA(NULL, PERIOD_H1, 9, 0, MODE_EMA, PRICE_CLOSE, s); }
double H1_21(int s) { return iMA(NULL, PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE, s); }
double BB(int tf, double dev, int mode, int s) { return iBands(NULL, tf, 20, dev, 0, PRICE_CLOSE, mode, s); }   // 20本・母標準偏差(研究台と同じ)

// 時刻 t に「閉じている」一番新しい足の番号(t ちょうどに閉じた足も入る)
int Done(int tf, datetime t)
{
   int s = iBarShift(NULL, tf, t - 1, false);
   if(s < 0) return(-1);
   if(iTime(NULL, tf, s) + PeriodSeconds(tf) <= t) return(s);
   return(s + 1);
}

bool Perm(datetime t, int d)
{
   int h = Done(PERIOD_H4, t);
   datetime hc = iTime(NULL, PERIOD_H4, h) + PeriodSeconds(PERIOD_H4);
   int dd = Done(PERIOD_D1, hc);
   double dc = iClose(NULL, PERIOD_D1, dd), d9 = D9(dd);
   double hcl = iClose(NULL, PERIOD_H4, h), h21 = H4_21(h);
   if(d9 <= 0 || h21 <= 0) return(false);
   return(d > 0 ? (dc > d9 && hcl > h21) : (dc < d9 && hcl < h21));
}

int K9(int dd, int d)
{
   int n = 0;
   for(int k = dd; k < dd + 400; k++)
   {
      double c = iClose(NULL, PERIOD_D1, k), e = D9(k);
      if(e <= 0 || c == 0) break;
      if(d > 0 ? (c > e) : (c < e)) n++; else break;
   }
   return(n);
}

bool Yasumi(datetime t)
{
   int md = TimeMonth(t) * 100 + TimeDay(t);
   return(md >= 429 && md <= 506);
}

int CountPos(int magic)
{
   int n = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES) && OrderSymbol() == Symbol() && OrderMagicNumber() == magic && OrderType() <= OP_SELL) n++;
   return(n);
}

void Log(string kind, datetime bar, int dir, double req, double fill, string note)
{
   int f = FileOpen(LOG, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_SHARE_READ, ',');
   if(f == INVALID_HANDLE) return;
   FileSeek(f, 0, SEEK_END);
   FileWrite(f, TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), kind, TimeToString(bar, TIME_DATE | TIME_MINUTES), dir,
             DoubleToString(Bid, Digits), DoubleToString(Ask, Digits), DoubleToString((Ask - Bid) / PIP, 1),
             DoubleToString(req, Digits), DoubleToString(fill, Digits), note);
   FileClose(f);
}

//+------------------------------------------------------------------+
//| 注文(合図の名札で二重を止める・直前にスプレッドを見る・結果を残す)    |
//+------------------------------------------------------------------+
int Open(int d, int magic, double lots, datetime bar, string why, int unit)
{
   string sid = StringFormat("K3v2_%d_%d_%d_%d", (int)bar, d, magic, unit);
   if(GlobalVariableCheck(sid)) { cntSkipDup++; Log("二重を止めた", bar, d, 0, 0, sid); return(-1); }
   RefreshRates();
   double spr = (Ask - Bid) / PIP;
   if(spr > MaxSpreadPips) { cntSkipSpr++; Log("スプレッドで見送り", bar, d, 0, 0, DoubleToString(spr, 1)); return(-1); }
   double px = d > 0 ? Ask : Bid;
   GlobalVariableSet(sid, (double)TimeCurrent());            // 送る前に名札(失敗しても同じ合図で打ち直さない)
   int tk = OrderSend(Symbol(), d > 0 ? OP_BUY : OP_SELL, lots, px, SlipPoints, 0, 0, why, magic, 0, d > 0 ? clrBlue : clrRed);
   double fill = 0; if(tk >= 0 && OrderSelect(tk, SELECT_BY_TICKET)) fill = OrderOpenPrice();
   Log(tk >= 0 ? "入り" : "入り失敗", bar, d, px, fill, why + (tk >= 0 ? " ticket=" + (string)tk : " err=" + (string)GetLastError()));
   return(tk);
}

bool ClosePos(int ticket, string why)
{
   if(!OrderSelect(ticket, SELECT_BY_TICKET)) return(false);
   RefreshRates();
   int d = OrderType() == OP_BUY ? 1 : -1;
   double px = d > 0 ? Bid : Ask;
   bool ok = OrderClose(ticket, OrderLots(), px, SlipPoints, clrGray);
   Log(ok ? "降り" : "降り失敗", 0, d, px, 0, why + (ok ? "" : " err=" + (string)GetLastError()));
   if(ok) cntSig++;
   return(ok);
}

void Modify(int ticket, double sl, double tp)
{
   if(!OrderSelect(ticket, SELECT_BY_TICKET)) return;
   sl = NormalizeDouble(sl, Digits); tp = NormalizeDouble(tp, Digits);
   if(MathAbs(OrderStopLoss() - sl) < Point / 2 && MathAbs(OrderTakeProfit() - tp) < Point / 2) return;
   if(!OrderModify(ticket, OrderOpenPrice(), sl, tp, 0, clrNONE)) Log("網・利確の付け替え失敗", 0, 0, sl, tp, "err=" + (string)GetLastError());
}

// 持っている玉の番号を集める(回しながら閉じても抜けないように先に集める)
int Tickets(int magic, int &out[])
{
   ArrayResize(out, 0);
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES) && OrderSymbol() == Symbol() && OrderMagicNumber() == magic && OrderType() <= OP_SELL)
      { int n = ArraySize(out); ArrayResize(out, n + 1); out[n] = OrderTicket(); }
   return(ArraySize(out));
}

//+------------------------------------------------------------------+
//| クジラの刺身:降り(合図)・利確・TS                                  |
//+------------------------------------------------------------------+
void ManageMain(int d, int magic, datetime T, datetime TS1)
{
   int dx = Done(PERIOD_D1, TS1);
   double d9 = D9(dx), d21 = D21(dx);
   datetime dclose = iTime(NULL, PERIOD_D1, dx) + PeriodSeconds(PERIOD_D1);
   bool sig = (d9 > 0 && d21 > 0) && (d > 0 ? !(d9 > d21) : (d9 > d21));
   bool avoid = (TimeHour(T) == AvoidHour);
   int h = Done(PERIOD_H4, TS1);
   double tpl = BB(PERIOD_H4, TpSigma, d > 0 ? MODE_UPPER : MODE_LOWER, h);
   double spr = Ask - Bid;
   int tks[]; int n = Tickets(magic, tks);
   for(int i = 0; i < n; i++)
   {
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      datetime ot = OrderOpenTime(); double op = OrderOpenPrice();
      if(sig && !avoid && dclose > ot) { if(ClosePos(tks[i], d > 0 ? "日足219" : "日足921")) continue; }
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      int eb = iBarShift(NULL, PERIOD_H1, ot, false);
      double sl = OrderStopLoss(), tp = 0;
      if(eb >= 1)
      {
         if(d > 0) { double mx = iHigh(NULL, PERIOD_H1, iHighest(NULL, PERIOD_H1, MODE_HIGH, eb, 1)); double ns = mx - TsPips * PIP; if(sl == 0 || ns > sl) sl = ns; }
         else      { double mn = iLow(NULL, PERIOD_H1, iLowest(NULL, PERIOD_H1, MODE_LOW, eb, 1));  double ns = mn + TsPips * PIP + spr; if(sl == 0 || ns < sl) sl = ns; }
      }
      if(tpl > 0)
      {
         if(d > 0 && tpl > op) tp = tpl;
         if(d < 0 && tpl < op - spr) tp = tpl + spr;
      }
      Modify(tks[i], sl, tp);
   }
}

void ManageDoten(datetime TS1)
{
   int h = Done(PERIOD_H4, TS1);
   double a9 = H4_9(h), a21 = H4_21(h), b9 = H4_9(h + 1), b21 = H4_21(h + 1);
   bool x219 = (a9 > 0 && b9 > 0) && (b9 > b21) && !(a9 > a21);
   datetime hc = iTime(NULL, PERIOD_H4, h) + PeriodSeconds(PERIOD_H4);
   int tks[]; int n = Tickets(MagicDoten, tks);
   for(int i = 0; i < n; i++)
   {
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      datetime ot = OrderOpenTime();
      if(x219 && hc > ot) { if(ClosePos(tks[i], "ドテン 4h219")) continue; }
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      int eb = iBarShift(NULL, PERIOD_H1, ot, false);
      if(eb >= 1)
      {
         double mx = iHigh(NULL, PERIOD_H1, iHighest(NULL, PERIOD_H1, MODE_HIGH, eb, 1));
         double sl = OrderStopLoss(), ns = mx - TsPips * PIP;
         if(sl == 0 || ns > sl) Modify(tks[i], ns, 0);
      }
   }
}

void ManageTai(datetime T, datetime TS1)
{
   int h = Done(PERIOD_H4, TS1);
   double o = iOpen(NULL, PERIOD_H4, h), c = iClose(NULL, PERIOD_H4, h), e9 = H4_9(h);
   bool ware = (e9 > 0) && ((o + c) / 2 < e9) && (c < e9);
   datetime hc = iTime(NULL, PERIOD_H4, h) + PeriodSeconds(PERIOD_H4);
   int tks[]; int n = Tickets(MagicTai, tks);
   for(int i = 0; i < n; i++)
   {
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      datetime ot = OrderOpenTime();
      if(ware && TimeHour(T) != AvoidHour && hc > ot) { if(ClosePos(tks[i], "鯛 4h9割れ")) continue; }
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      int eb = iBarShift(NULL, PERIOD_H1, ot, false);
      if(eb >= 1)
      {
         double mx = iHigh(NULL, PERIOD_H1, iHighest(NULL, PERIOD_H1, MODE_HIGH, eb, 1));
         double sl = OrderStopLoss(), ns = mx - TsPips * PIP;
         if(sl == 0 || ns > sl) Modify(tks[i], ns, 0);
      }
   }
}

//+------------------------------------------------------------------+
//| 日足の押し目巡航(かがみ無限 抜1・無1・出1)                           |
//+------------------------------------------------------------------+
bool OshStep(int s, int d)
{
   int k = d > 0 ? 0 : 1;
   double e9 = D9(s), e21 = D21(s);
   if(e9 <= 0 || e21 <= 0) return(false);
   bool up = d > 0 ? (e9 > e21) : (e9 < e21);
   if(!up) { oIncr[k] = false; oArm[k] = false; return(false); }
   double c = iClose(NULL, PERIOD_D1, s), o = iOpen(NULL, PERIOD_D1, s), h = iHigh(NULL, PERIOD_D1, s), l = iLow(NULL, PERIOD_D1, s);
   int pk = s + 1; double prev = d > 0 ? iHigh(NULL, PERIOD_D1, s + 1) : iLow(NULL, PERIOD_D1, s + 1);
   for(int j = s + 1; j <= s + 10; j++)
   {
      double v = d > 0 ? iHigh(NULL, PERIOD_D1, j) : iLow(NULL, PERIOD_D1, j);
      if(d > 0 ? (v >= prev) : (v <= prev)) { prev = v; pk = j; }
   }
   bool pulled = false;
   for(int j = pk; j >= s + 1; j--)
   {
      double e = D9(j);
      if(d > 0 ? (iLow(NULL, PERIOD_D1, j) <= e) : (iHigh(NULL, PERIOD_D1, j) >= e)) { pulled = true; break; }
   }
   bool brk = d > 0 ? (c > prev) : (c < prev);
   double wNow = BB(PERIOD_D1, 2.0, MODE_UPPER, s) - BB(PERIOD_D1, 2.0, MODE_LOWER, s);
   double wOld = BB(PERIOD_D1, 2.0, MODE_UPPER, s + 3) - BB(PERIOD_D1, 2.0, MODE_LOWER, s + 3);
   if(!oIncr[k] && wNow > wOld && pulled && brk) { oIncr[k] = true; oArm[k] = false; return(true); }
   if(oIncr[k])
   {
      if(d > 0 ? (c > e9) : (c < e9)) oArm[k] = true;
      bool touch = d > 0 ? (l <= e21) : (h >= e21);
      bool yang  = d > 0 ? (c > o) : (c < o);
      if(oArm[k] && touch && yang) { oArm[k] = false; return(true); }
   }
   return(false);
}

void OshimeDaily(datetime TS1)
{
   int dd = Done(PERIOD_D1, TS1);
   datetime dt = iTime(NULL, PERIOD_D1, dd);
   if(dd < 0 || dt == oLastD) return;
   if(oLastD == 0) { for(int s = dd + 300; s > dd; s--) { OshStep(s, 1); OshStep(s, -1); } }
   bool b = OshStep(dd, 1), sl = OshStep(dd, -1);
   if(oLastD != 0) { if(b) oPend[0] = true; if(sl) oPend[1] = true; }
   oLastD = dt;
}

void ManageOshime(int d, int magic, datetime T, datetime TS1)
{
   int dx = Done(PERIOD_D1, TS1);
   double d9 = D9(dx), d21 = D21(dx);
   datetime dclose = iTime(NULL, PERIOD_D1, dx) + PeriodSeconds(PERIOD_D1);
   bool sig = (d9 > 0 && d21 > 0) && (d > 0 ? !(d9 > d21) : (d9 > d21));
   double tpl = BB(PERIOD_D1, 3.5, d > 0 ? MODE_UPPER : MODE_LOWER, dx);
   double spr = Ask - Bid;
   double net = d > 0 ? iLow(NULL, PERIOD_D1, dx) : iHigh(NULL, PERIOD_D1, dx) + spr;
   int tks[]; int n = Tickets(magic, tks);
   for(int i = 0; i < n; i++)
   {
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      datetime ot = OrderOpenTime(); double op = OrderOpenPrice();
      if(sig && TimeHour(T) != AvoidHour && dclose > ot) { if(ClosePos(tks[i], d > 0 ? "押し目 日足219" : "押し目 日足921")) continue; }
      if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
      double sl = OrderStopLoss(), tp = 0;
      if(sl == 0 || (d > 0 ? net > sl : net < sl)) sl = net;
      if(tpl > 0) { if(d > 0 && tpl > op) tp = tpl; if(d < 0 && tpl < op - spr) tp = tpl + spr; }
      Modify(tks[i], sl, tp);
   }
}

//+------------------------------------------------------------------+
//| クジラの入り(1時間921 か 許しの瞬間)                                 |
//+------------------------------------------------------------------+
bool EntrySignal(int d, datetime TS1, datetime TS2)
{
   double e9a = H1_9(1), e21a = H1_21(1), e9b = H1_9(2), e21b = H1_21(2);
   double up1 = BB(PERIOD_H1, 1.0, MODE_UPPER, 1), lo1 = BB(PERIOD_H1, 1.0, MODE_LOWER, 1);
   double up2 = BB(PERIOD_H1, SaoSigma, MODE_UPPER, 1), lo2 = BB(PERIOD_H1, SaoSigma, MODE_LOWER, 1);
   if(e9a <= 0 || e9b <= 0 || up1 <= 0 || up2 <= 0) return(false);
   double c = iClose(NULL, PERIOD_H1, 1);
   bool upA = e9a > e21a, upB = e9b > e21b;
   bool side  = d > 0 ? upA : !upA;
   bool cross = d > 0 ? (upA && !upB) : (!upA && upB);
   bool p = Perm(TS1, d), pp = Perm(TS2, d);
   int dq = Done(PERIOD_D1, TS1);
   double dc = iClose(NULL, PERIOD_D1, dq), d21 = D21(dq), d21b = D21(dq + 3);
   if(d21 <= 0 || d21b <= 0) return(false);
   bool qq = d > 0 ? dc > d21 : dc < d21;
   bool big21 = d > 0 ? (d21 - d21b) > 0 : (d21 - d21b) < 0;
   bool kawa = d > 0 ? c > up1 : c < lo1;
   bool chi  = d > 0 ? c > iHigh(NULL, PERIOD_H1, 1 + 21) : c < iLow(NULL, PERIOD_H1, 1 + 21);
   bool ns   = d > 0 ? c <= up2 : c >= lo2;
   bool e921 = cross && p;
   bool kai  = p && !pp && side && !cross;
   int k9 = K9(dq, d), k9p = K9(Done(PERIOD_D1, TS2), d);
   kai = kai && (k9 >= KaiK9);
   bool first = (k9 >= KaiK9) && !(k9p >= KaiK9) && p && side && !cross && (k9 == KaiK9);
   kai = kai || first;
   return(((e921 && kawa && chi) || (kai && qq)) && ns && big21);
}

//+------------------------------------------------------------------+
//| しあわせセット(レンジの箱)                                          |
//+------------------------------------------------------------------+
// 日足 s の遅行スパンの向き(終値と21本前の終値の上下)。足りなければ 9 を返す
int ShSg(int s)
{
   double a = iClose(NULL, PERIOD_D1, s), b = iClose(NULL, PERIOD_D1, s + 21);
   if(a == 0 || b == 0) return(9);
   return(a > b ? 1 : (a < b ? -1 : 0));
}
// 日足 s で「レンジ」か:s から30本の中で遅行スパンの向きが入れ替わった日が3回以上(0 になった日は数えない)
bool ShRngAt(int s)
{
   int n = 0;
   for(int t = s; t < s + SH_WIN; t++)
   {
      int a = ShSg(t), b = ShSg(t + 1);
      if(a == 9 || b == 9) return(false);
      if(a != b && a != 0) n++;
   }
   return(n >= SH_NFLIP);
}
// 日足 dd が閉じた時の値を作る(箱=続いているレンジの1日目の30日前〜dd。レンジでない日は30日)
void ShDaily(datetime TS1)
{
   int dd = Done(PERIOD_D1, TS1);
   if(dd < 0) return;
   datetime dt = iTime(NULL, PERIOD_D1, dd);
   if(dt == shDay) return;
   shDay = dt;
   shRng = ShRngAt(dd);
   int fr = dd + SH_WIN - 1;
   if(shRng)
   {
      int f = dd;
      while(f + 1 < iBars(NULL, PERIOD_D1) - 60 && ShRngAt(f + 1)) f++;
      fr = f + SH_WIN - 1;
   }
   shBhi = iHigh(NULL, PERIOD_D1, iHighest(NULL, PERIOD_D1, MODE_HIGH, fr - dd + 1, dd));
   shBlo = iLow(NULL, PERIOD_D1, iLowest(NULL, PERIOD_D1, MODE_LOW, fr - dd + 1, dd));
   shMd = BB(PERIOD_D1, 2.0, MODE_MAIN, dd);
   shSd = (BB(PERIOD_D1, 2.0, MODE_UPPER, dd) - shMd) / 2.0;
   shE200 = D200(dd);
   int w = Done(PERIOD_W1, TS1);
   double w9 = iMA(NULL, PERIOD_W1, 9, 0, MODE_EMA, PRICE_CLOSE, w), w21 = iMA(NULL, PERIOD_W1, 21, 0, MODE_EMA, PRICE_CLOSE, w);
   shW219 = (w9 > 0 && w21 > 0 && w9 < w21);
   Log("しあわせ 日足", dt, 0, shBlo, shBhi, StringFormat("レンジ=%d 真ん中=%.3f 1σ=%.3f 200=%.3f 週219=%d", shRng, shMd, shSd, shE200, shW219));
}

// 毎ティック:しあわせセットの入り(研究台:前の日足の −2σ に値が届いたら、その値で4単位。売りは鏡うつし)
void ShEntry(datetime T)
{
   if(shDay == 0 || !shRng || shSd <= 0) return;
   if(TimeHour(T) == AvoidHour) return;
   if(UseYasumi && Yasumi(T)) return;
   for(int k = 0; k < 2; k++)
   {
      int d = k == 0 ? 1 : -1;
      if(d < 0 && (!ShUseSell || !shW219)) continue;
      int mk = d > 0 ? MagicShBK : MagicShSK, mt = d > 0 ? MagicShBT : MagicShST;
      if(CountPos(mk) > 0) continue;                                   // 前のセットの刈るが残っている間は次のセットなし
      if(CountPos(mt) >= SH_TAME) continue;
      string gv = StringFormat("K3v2_sh_%d_%d", (int)T, d);             // 1本の足で1セットまで
      if(GlobalVariableCheck(gv)) continue;
      double lv = shMd - 2.0 * d * shSd;
      if(d > 0 ? (Bid > lv) : (Bid < lv)) continue;
      double e = d > 0 ? Ask : Bid;
      double bx = d > 0 ? shBlo : shBhi;
      if(!(d > 0 ? e > bx : e < bx)) continue;                         // 箱の外では入らない
      if(MathAbs(e - shE200) <= SH_NAKA * shSd) continue;              // 200の上下1σ(箱の真ん中)では入らない
      GlobalVariableSet(gv, (double)TimeCurrent());
      string cm = StringFormat("SH bx=%.3f", bx);                       // 箱の底(売りは天井)を玉に書いておく
      for(int u = 0; u < SH_KAR + 1; u++) Open(d, u < SH_KAR ? mk : mt, ShLots, T, cm, u);
      cntShIn++;
   }
}

// 足ごと:しあわせセットの降り(箱割れ)と利確の付け替え
void ShManage(datetime T, datetime TS1)
{
   int dx = Done(PERIOD_D1, TS1);
   double dc = iClose(NULL, PERIOD_D1, dx);
   datetime dclose = iTime(NULL, PERIOD_D1, dx) + PeriodSeconds(PERIOD_D1);
   double spr = Ask - Bid;
   for(int k = 0; k < 4; k++)
   {
      int magic = k == 0 ? MagicShBK : (k == 1 ? MagicShBT : (k == 2 ? MagicShSK : MagicShST));
      int d = k < 2 ? 1 : -1;
      double sig = (k == 0 || k == 2) ? SH_TPK : SH_TAMEK;
      double tv = shMd + sig * d * shSd;
      int tks[]; int n = Tickets(magic, tks);
      for(int i = 0; i < n; i++)
      {
         if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
         datetime ot = OrderOpenTime(); double op = OrderOpenPrice();
         string cm = OrderComment(); int p = StringFind(cm, "bx=");
         double bx = p >= 0 ? StringToDouble(StringSubstr(cm, p + 3)) : 0;
         // 箱割れ:入った後に閉じた日足の終値が、入った時の箱の外。0時はよけて次の足
         if(bx > 0 && dclose > ot && (d > 0 ? dc < bx : dc > bx) && TimeHour(T) != AvoidHour)
         { if(ClosePos(tks[i], "しあわせ 箱割れ")) { cntShBox++; continue; } }
         if(!OrderSelect(tks[i], SELECT_BY_TICKET)) continue;
         double tp = 0;
         if(shSd > 0) { if(d > 0 && tv > op) tp = tv; if(d < 0 && tv < op - spr) tp = tv + spr; }
         Modify(tks[i], 0, tp);
      }
   }
}

//+------------------------------------------------------------------+
//| ドテンの構え:売りの利確を、閉じた玉の履歴から見る(MT4 は約定の知らせが無い) |
//+------------------------------------------------------------------+
void CheckHistory()
{
   datetime newest = lastHist;
   for(int i = OrdersHistoryTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(OrderSymbol() != Symbol() || OrderType() > OP_SELL) continue;
      if(OrderCloseTime() <= lastHist) continue;
      if(OrderCloseTime() > newest) newest = OrderCloseTime();
      bool tp = StringFind(OrderComment(), "[tp]") >= 0 || (OrderTakeProfit() > 0 && MathAbs(OrderClosePrice() - OrderTakeProfit()) < 3 * Point);
      bool sl = StringFind(OrderComment(), "[sl]") >= 0 || (OrderStopLoss() > 0 && MathAbs(OrderClosePrice() - OrderStopLoss()) < 3 * Point);
      if(tp) cntTP++; else if(sl) cntSL++;
      if(OrderMagicNumber() == MagicSell && tp && UseDoten) { armDoten = true; Log("ドテンを構えた", 0, -1, 0, OrderClosePrice(), "ticket=" + (string)OrderTicket()); }
   }
   lastHist = newest;
}

//+------------------------------------------------------------------+
void OnTick()
{
   datetime T = iTime(NULL, PERIOD_H1, 0);
   if(T <= 0) return;
   if(T == lastBar) { if(UseShiawase) ShEntry(T); return; }        // 足の途中:しあわせの入り(値が線に届いたか)だけ見る
   if(lastBar == 0) { lastBar = T; if(lastHist == 0) lastHist = TimeCurrent(); return; }   // 起動した直後は撃たない
   lastBar = T;
   datetime TS1 = iTime(NULL, PERIOD_H1, 1) + PeriodSeconds(PERIOD_H1);   // 合図の足(1本前)が閉じた時刻
   datetime TS2 = iTime(NULL, PERIOD_H1, 2) + PeriodSeconds(PERIOD_H1);
   bool avoid = (TimeHour(T) == AvoidHour);
   bool yas = UseYasumi && Yasumi(T);

   // 0. 閉じた玉の履歴(ドテンの構え・カウンター)
   CheckHistory();

   // 1. 降り(合図)と、利確・TS の付け替え
   ManageMain(1, MagicBuy, T, TS1);
   if(UseSell) ManageMain(-1, MagicSell, T, TS1);
   if(UseDoten) ManageDoten(TS1);
   if(UseTai) ManageTai(T, TS1);
   if(UseOshime) { ManageOshime(1, MagicOshB, T, TS1); ManageOshime(-1, MagicOshS, T, TS1); OshimeDaily(TS1); }
   if(UseShiawase) { ShDaily(TS1); ShManage(T, TS1); }

   // 2. クジラ・鯛の入り
   for(int k = 0; k < 2; k++)
   {
      int d = k == 0 ? 1 : -1;
      if(d < 0 && !UseSell) continue;
      int mg = d > 0 ? MagicBuy : MagicSell;
      bool sig = EntrySignal(d, TS1, TS2) && !yas;
      bool pend = d > 0 ? pendBuy : pendSell;
      bool go = false;
      if(avoid) { if(sig) { if(d > 0) pendBuy = true; else pendSell = true; Log("0時をよけて次の足へ", T, d, 0, 0, ""); } }
      else { go = sig || pend; if(d > 0) pendBuy = false; else pendSell = false; }
      if(go && CountPos(mg) < MaxPos) Open(d, mg, Lots, T, sig ? "入り" : "0時をよけた入り", 0);
      if(go && d > 0 && UseTai && CountPos(MagicTai) < 1) Open(1, MagicTai, Lots, T, "鯛の刺身", 0);
   }

   // 2b. 日足の押し目巡航
   if(UseOshime && !avoid)
   {
      for(int k = 0; k < 2; k++)
      {
         if(!oPend[k]) continue;
         oPend[k] = false;
         int d = k == 0 ? 1 : -1; int mg = d > 0 ? MagicOshB : MagicOshS;
         if(yas || CountPos(mg) >= 5) continue;
         int dl = Done(PERIOD_D1, TS1);
         RefreshRates();
         double sl = d > 0 ? iLow(NULL, PERIOD_D1, dl) : iHigh(NULL, PERIOD_D1, dl) + (Ask - Bid);
         if(d > 0 ? (sl >= Ask) : (sl <= Ask)) continue;
         Open(d, mg, Lots, T, "押し目巡航", 0);
      }
   }

   // 3. ドテン買い:売りの利確で構え、1時間の921が出た次の足で入る
   if(UseDoten && armDoten)
   {
      double e9a = H1_9(1), e21a = H1_21(1), e9b = H1_9(2), e21b = H1_21(2);
      if(e9a > 0 && e9b > 0 && (e9a > e21a) && !(e9b > e21b))
      {
         armDoten = false;
         if(!yas && CountPos(MagicDoten) < 1) Open(1, MagicDoten, Lots, T, "ドテン買い", 0);
      }
   }

   // 4. しあわせセットの入り(足の始まりの値でも見る)
   if(UseShiawase) ShEntry(T);
   SaveFlags();
}
//+------------------------------------------------------------------+

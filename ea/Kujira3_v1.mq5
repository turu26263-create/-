//+------------------------------------------------------------------+
//| Kujira3_v1.mq5  決まった形3+鯛の刺身+日足の押し目巡航(ブレンド 11-10)      |
//| 2026-11-09 たくちん「mt5でやって」                                     |
//| 研究台(engine/nyu)の決まった形3を、そのまま MT5 に写した物。決まりは変えない |
//| 未検証:コンパイル・テスター・デモはまだ(クラウドに MetaEditor が無い)      |
//+------------------------------------------------------------------+
#property copyright "takuchin"
#property version   "1.00"

//--- 決まった形3(研究台と同じ値。変える時はたくちんの「ご」)
input double Lots          = 0.01;   // 1玉のロット(決め打ち)
input int    MaxPos        = 5;      // 同じ向きで持つ玉の上限(クジラ5発)
input int    KaiK9         = 3;      // 許しの入りは日足の終値が9の向こうに何本続いてから
input double SaoSigma      = 2.0;    // 竿先:1時間の帯 ±2σ の外では入らない
input double TpSigma       = 3.5;    // 利確:4時間の帯 ±3.5σ(1本前の4時間足が閉じた時の値)
input double TsPips        = 550;    // TS:一番伸びた所から 550p
input bool   UseSell       = true;   // 売りも入れる
input bool   UseDoten      = true;   // 売りの利確の後、1時間921を待ってドテン買い
input bool   UseTai        = true;   // 鯛の刺身(買いだけ):同じ入りで1玉、4時間の9割れで降り、TS550、利確なし
input bool   UseOshime     = true;   // かがみ無限の日足の巡航・押し目の無限リーチ(売り買い・最大5玉・日足3.5σ利確・日足219で降り・網は前の日のひげ先)
input bool   UseYasumi     = true;   // GW 4/29-5/6 は新しく入らない(11-10 サンタ・寝正月はやめた)
input int    AvoidHour     = 0;      // この時刻(サーバー)の足では入り・降りしない(次の足へ)
input double MaxSpreadPips = 5.0;    // 入る直前のスプレッドがこれより広ければ入らない(研究台には無い守り)
input int    SlipPoints    = 30;     // 許す滑り(ポイント)
input long   MagicBuy      = 26110901;
input long   MagicSell     = 26110902;
input long   MagicDoten    = 26110903;
input long   MagicTai      = 26110904;
input long   MagicOshB     = 26110905;
input long   MagicOshS     = 26110906;

//--- 線
int hD9, hD21, hH4_9, hH4_21, hH4bb, hH1_9, hH1_21, hH1bb1, hH1bb2, hDbb2, hDbb35;
//--- 日足の押し目巡航の状態(買い[0]・売り[1])
bool oIncr[2] = {false, false}, oArm[2] = {false, false}, oPend[2] = {false, false};
datetime oLastD = 0;
datetime lastBar = 0;
bool pendBuy = false, pendSell = false;   // 0時をよけて次の足で入る
bool armDoten = false;                    // 売りの利確でドテンを構えている
double PIP;
//--- カウンター(降りた理由の数)
int cntTP = 0, cntSL = 0, cntSig = 0, cntOther = 0, cntSkipSpr = 0, cntSkipDup = 0;
string LOG = "Kujira3_log.csv";

//+------------------------------------------------------------------+
int OnInit()
{
   if((ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
   {
      Print("両建てできない口座です(ネッティング)。形3は売りとドテン買いを同時に持つので止めます");
      return(INIT_FAILED);
   }
   PIP = (_Digits == 3 || _Digits == 5) ? _Point * 10 : _Point;
   hD9    = iMA(_Symbol, PERIOD_D1, 9, 0, MODE_EMA, PRICE_CLOSE);
   hD21   = iMA(_Symbol, PERIOD_D1, 21, 0, MODE_EMA, PRICE_CLOSE);
   hH4_9  = iMA(_Symbol, PERIOD_H4, 9, 0, MODE_EMA, PRICE_CLOSE);
   hH4_21 = iMA(_Symbol, PERIOD_H4, 21, 0, MODE_EMA, PRICE_CLOSE);
   hH4bb  = iBands(_Symbol, PERIOD_H4, 20, 0, TpSigma, PRICE_CLOSE);
   hH1_9  = iMA(_Symbol, PERIOD_H1, 9, 0, MODE_EMA, PRICE_CLOSE);
   hH1_21 = iMA(_Symbol, PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE);
   hH1bb1 = iBands(_Symbol, PERIOD_H1, 20, 0, 1.0, PRICE_CLOSE);
   hH1bb2 = iBands(_Symbol, PERIOD_H1, 20, 0, SaoSigma, PRICE_CLOSE);
   hDbb2  = iBands(_Symbol, PERIOD_D1, 20, 0, 2.0, PRICE_CLOSE);
   hDbb35 = iBands(_Symbol, PERIOD_D1, 20, 0, 3.5, PRICE_CLOSE);
   if(hD9 == INVALID_HANDLE || hD21 == INVALID_HANDLE || hH4_9 == INVALID_HANDLE || hH4_21 == INVALID_HANDLE || hH4bb == INVALID_HANDLE ||
      hH1_9 == INVALID_HANDLE || hH1_21 == INVALID_HANDLE || hH1bb1 == INVALID_HANDLE || hH1bb2 == INVALID_HANDLE || hDbb2 == INVALID_HANDLE || hDbb35 == INVALID_HANDLE)
      return(INIT_FAILED);
   // 再起動しても戻す
   armDoten = GlobalVariableCheck(GVName("arm")) && GlobalVariableGet(GVName("arm")) > 0;
   pendBuy  = GlobalVariableCheck(GVName("pb")) && GlobalVariableGet(GVName("pb")) > 0;
   pendSell = GlobalVariableCheck(GVName("ps")) && GlobalVariableGet(GVName("ps")) > 0;
   Log("起動", 0, 0, 0, 0, "arm=" + (string)armDoten);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   string s = StringFormat("カウンター 利確=%d 網(TS)=%d 合図で降り=%d ほか=%d スプレッドで見送り=%d 二重を止めた=%d", cntTP, cntSL, cntSig, cntOther, cntSkipSpr, cntSkipDup);
   Print(s); Log("終わり", 0, 0, 0, 0, s);
}

//+------------------------------------------------------------------+
//| 道具                                                              |
//+------------------------------------------------------------------+
string GVName(string k) { return "K3_" + _Symbol + "_" + k; }
void   SaveFlags()
{
   GlobalVariableSet(GVName("arm"), armDoten ? 1 : 0);
   GlobalVariableSet(GVName("pb"), pendBuy ? 1 : 0);
   GlobalVariableSet(GVName("ps"), pendSell ? 1 : 0);
}

double V(int h, int buf, int shift)
{
   double a[1];
   if(CopyBuffer(h, buf, shift, 1, a) != 1) return(EMPTY_VALUE);
   return(a[0]);
}

// 時刻 t に「閉じている」一番新しい足の番号(t ちょうどに閉じた足も入る)
int Done(ENUM_TIMEFRAMES tf, datetime t)
{
   int s = iBarShift(_Symbol, tf, t - 1, false);              // t の1秒前を含む足(週末の穴では手前の足)
   if(s < 0) return(-1);
   if(iTime(_Symbol, tf, s) + PeriodSeconds(tf) <= t) return(s); // その足が t までに閉じていればそれ
   return(s + 1);                                              // まだ動いている足なら1本前
}

// 許し:大きい足(日足)の終値が9の向こう かつ 中の足(4時間)の終値が21の向こう(時刻 t で閉じている足で見る)
bool Perm(datetime t, int d)
{
   int h = Done(PERIOD_H4, t);
   datetime hc = iTime(_Symbol, PERIOD_H4, h) + PeriodSeconds(PERIOD_H4);
   int dd = Done(PERIOD_D1, hc);
   double dc = iClose(_Symbol, PERIOD_D1, dd), d9 = V(hD9, 0, dd);
   double hcl = iClose(_Symbol, PERIOD_H4, h), h21 = V(hH4_21, 0, h);
   if(d9 == EMPTY_VALUE || h21 == EMPTY_VALUE) return(false);
   return(d > 0 ? (dc > d9 && hcl > h21) : (dc < d9 && hcl < h21));
}

// 日足の終値が9の向こうに何本続いているか(dd の足から過去へ)
int K9(int dd, int d)
{
   int n = 0;
   for(int k = dd; k < dd + 400; k++)
   {
      double c = iClose(_Symbol, PERIOD_D1, k), e = V(hD9, 0, k);
      if(e == EMPTY_VALUE || c == 0) break;
      if(d > 0 ? (c > e) : (c < e)) n++; else break;
   }
   return(n);
}

bool Yasumi(datetime t)
{
   MqlDateTime m; TimeToStruct(t, m); int md = m.mon * 100 + m.day;
   return(md >= 429 && md <= 506);                            // 11-10 たくちん「さんたと寝正月やめる」→ GW だけ
}

int CountPos(long magic)
{
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tk = PositionGetTicket(i);
      if(tk > 0 && PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == magic) n++;
   }
   return(n);
}

void Log(string kind, datetime bar, int dir, double req, double fill, string note)
{
   int f = FileOpen(LOG, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_SHARE_READ, ',');
   if(f == INVALID_HANDLE) return;
   FileSeek(f, 0, SEEK_END);
   MqlTick tk; SymbolInfoTick(_Symbol, tk);
   FileWrite(f, TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), kind, TimeToString(bar, TIME_DATE | TIME_MINUTES), dir,
             DoubleToString(tk.bid, _Digits), DoubleToString(tk.ask, _Digits), DoubleToString((tk.ask - tk.bid) / PIP, 1),
             DoubleToString(req, _Digits), DoubleToString(fill, _Digits), note);
   FileClose(f);
}

//+------------------------------------------------------------------+
//| 注文(fx-entry-sync:合図の名札で二重を止める・直前にスプレッドを見る・結果を残す) |
//+------------------------------------------------------------------+
bool Open(int d, long magic, datetime bar, string why)
{
   string sid = StringFormat("K3_%s_%d_%d_%I64d", _Symbol, (int)bar, d, magic);
   if(StringLen(sid) > 63) sid = StringSubstr(sid, 0, 63);
   if(GlobalVariableCheck(sid)) { cntSkipDup++; Log("二重を止めた", bar, d, 0, 0, sid); return(false); }
   MqlTick tk;
   if(!SymbolInfoTick(_Symbol, tk)) return(false);
   double spr = (tk.ask - tk.bid) / PIP;
   if(spr > MaxSpreadPips) { cntSkipSpr++; Log("スプレッドで見送り", bar, d, 0, 0, DoubleToString(spr, 1)); return(false); }
   MqlTradeRequest rq; MqlTradeResult rs; ZeroMemory(rq); ZeroMemory(rs);
   rq.action = TRADE_ACTION_DEAL; rq.symbol = _Symbol; rq.volume = Lots; rq.magic = magic; rq.deviation = SlipPoints;
   rq.type = d > 0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   rq.price = d > 0 ? tk.ask : tk.bid;
   rq.type_filling = ORDER_FILLING_IOC;
   long fm = SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((fm & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK) rq.type_filling = ORDER_FILLING_FOK;
   rq.comment = why;
   GlobalVariableSet(sid, (double)TimeCurrent());             // 送る前に名札を立てる(失敗しても同じ合図で打ち直さない)
   bool ok = OrderSend(rq, rs);
   Log(ok ? "入り" : "入り失敗", bar, d, rq.price, rs.price, why + " retcode=" + (string)rs.retcode + " deal=" + (string)rs.deal);
   return(ok && (rs.retcode == TRADE_RETCODE_DONE || rs.retcode == TRADE_RETCODE_PLACED));
}

bool ClosePos(ulong ticket, string why)
{
   if(!PositionSelectByTicket(ticket)) return(false);
   MqlTick tk; SymbolInfoTick(_Symbol, tk);
   long type = PositionGetInteger(POSITION_TYPE);
   MqlTradeRequest rq; MqlTradeResult rs; ZeroMemory(rq); ZeroMemory(rs);
   rq.action = TRADE_ACTION_DEAL; rq.symbol = _Symbol; rq.position = ticket; rq.volume = PositionGetDouble(POSITION_VOLUME);
   rq.magic = PositionGetInteger(POSITION_MAGIC); rq.deviation = SlipPoints;
   rq.type = type == POSITION_TYPE_BUY ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   rq.price = type == POSITION_TYPE_BUY ? tk.bid : tk.ask;
   rq.type_filling = ORDER_FILLING_IOC;
   long fm = SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((fm & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK) rq.type_filling = ORDER_FILLING_FOK;
   rq.comment = why;
   bool ok = OrderSend(rq, rs);
   Log(ok ? "降り" : "降り失敗", 0, type == POSITION_TYPE_BUY ? 1 : -1, rq.price, rs.price, why + " retcode=" + (string)rs.retcode);
   return(ok);
}

void Modify(ulong ticket, double sl, double tp)
{
   if(!PositionSelectByTicket(ticket)) return;
   double osl = PositionGetDouble(POSITION_SL), otp = PositionGetDouble(POSITION_TP);
   sl = NormalizeDouble(sl, _Digits); tp = NormalizeDouble(tp, _Digits);
   if(MathAbs(osl - sl) < _Point / 2 && MathAbs(otp - tp) < _Point / 2) return;
   MqlTradeRequest rq; MqlTradeResult rs; ZeroMemory(rq); ZeroMemory(rs);
   rq.action = TRADE_ACTION_SLTP; rq.symbol = _Symbol; rq.position = ticket; rq.sl = sl; rq.tp = tp;
   if(!OrderSend(rq, rs)) Log("網・利確の付け替え失敗", 0, 0, sl, tp, "retcode=" + (string)rs.retcode);
}

//+------------------------------------------------------------------+
//| 持っている玉の 降り(合図)・利確・TS                                 |
//+------------------------------------------------------------------+
void ManageMain(int d, long magic, datetime T, datetime TS1)
{
   // 日足の219(売りは921):時刻 T で閉じている日足で 9 と 21 の並びが逆。その日足が閉じたのが入った後なら降りる
   int dx = Done(PERIOD_D1, TS1);
   double d9 = V(hD9, 0, dx), d21 = V(hD21, 0, dx);
   datetime dclose = iTime(_Symbol, PERIOD_D1, dx) + PeriodSeconds(PERIOD_D1);
   bool sig = (d9 != EMPTY_VALUE && d21 != EMPTY_VALUE) && (d > 0 ? !(d9 > d21) : (d9 > d21));
   MqlDateTime m; TimeToStruct(T, m);
   bool avoid = (m.hour == AvoidHour);
   // 利確の線:1本前の4時間足が閉じた時の ±3.5σ
   int h = Done(PERIOD_H4, TS1);
   double tpl = d > 0 ? V(hH4bb, 1, h) : V(hH4bb, 2, h);
   MqlTick tk; SymbolInfoTick(_Symbol, tk); double spr = tk.ask - tk.bid;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tkt = PositionGetTicket(i);
      if(tkt == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != magic) continue;
      datetime ot = (datetime)PositionGetInteger(POSITION_TIME);
      double op = PositionGetDouble(POSITION_PRICE_OPEN);
      if(sig && !avoid && dclose > ot) { if(ClosePos(tkt, d > 0 ? "日足219" : "日足921")) continue; }
      // TS:入った足から閉じた足までで一番伸びた所から 550p(売りは買い戻しのスプレッド分上に置く)
      int eb = iBarShift(_Symbol, PERIOD_H1, ot, false);
      double sl = PositionGetDouble(POSITION_SL), tp = 0;
      if(eb >= 1)
      {
         if(d > 0) { double mx = iHigh(_Symbol, PERIOD_H1, iHighest(_Symbol, PERIOD_H1, MODE_HIGH, eb, 1)); double ns = mx - TsPips * PIP; if(sl == 0 || ns > sl) sl = ns; }
         else      { double mn = iLow(_Symbol, PERIOD_H1, iLowest(_Symbol, PERIOD_H1, MODE_LOW, eb, 1));  double ns = mn + TsPips * PIP + spr; if(sl == 0 || ns < sl) sl = ns; }
      }
      // 利確は入り値より向こうにある時だけ(売りはスプレッド分も)
      if(tpl != EMPTY_VALUE)
      {
         if(d > 0 && tpl > op) tp = tpl;
         if(d < 0 && tpl < op - spr) tp = tpl + spr;
      }
      Modify(tkt, sl, tp);
   }
}

void ManageDoten(datetime T)
{
   // 降り:4時間足の新しく出た219(入った後に閉じた4時間足)+ TS550
   int h = Done(PERIOD_H4, T);
   double a9 = V(hH4_9, 0, h), a21 = V(hH4_21, 0, h), b9 = V(hH4_9, 0, h + 1), b21 = V(hH4_21, 0, h + 1);
   bool x219 = (a9 != EMPTY_VALUE && b9 != EMPTY_VALUE) && (b9 > b21) && !(a9 > a21);
   datetime hc = iTime(_Symbol, PERIOD_H4, h) + PeriodSeconds(PERIOD_H4);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tkt = PositionGetTicket(i);
      if(tkt == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != MagicDoten) continue;
      datetime ot = (datetime)PositionGetInteger(POSITION_TIME);
      if(x219 && hc > ot) { if(ClosePos(tkt, "ドテン 4h219")) continue; }
      int eb = iBarShift(_Symbol, PERIOD_H1, ot, false);
      if(eb >= 1)
      {
         double mx = iHigh(_Symbol, PERIOD_H1, iHighest(_Symbol, PERIOD_H1, MODE_HIGH, eb, 1));
         double sl = PositionGetDouble(POSITION_SL), ns = mx - TsPips * PIP;
         if(sl == 0 || ns > sl) Modify(tkt, ns, 0);
      }
   }
}

void ManageTai(datetime T, datetime TS1)
{
   // 降り:4時間の9割れ(実体の真ん中と終値が9の下)の4時間足が、入った後に閉じたら + TS550。0時の足では降りない
   int h = Done(PERIOD_H4, TS1);
   double o = iOpen(_Symbol, PERIOD_H4, h), c = iClose(_Symbol, PERIOD_H4, h), e9 = V(hH4_9, 0, h);
   bool ware = (e9 != EMPTY_VALUE) && ((o + c) / 2 < e9) && (c < e9);
   datetime hc = iTime(_Symbol, PERIOD_H4, h) + PeriodSeconds(PERIOD_H4);
   MqlDateTime m; TimeToStruct(T, m);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tkt = PositionGetTicket(i);
      if(tkt == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != MagicTai) continue;
      datetime ot = (datetime)PositionGetInteger(POSITION_TIME);
      if(ware && m.hour != AvoidHour && hc > ot) { if(ClosePos(tkt, "鯛 4h9割れ")) continue; }
      int eb = iBarShift(_Symbol, PERIOD_H1, ot, false);
      if(eb >= 1)
      {
         double mx = iHigh(_Symbol, PERIOD_H1, iHighest(_Symbol, PERIOD_H1, MODE_HIGH, eb, 1));
         double sl = PositionGetDouble(POSITION_SL), ns = mx - TsPips * PIP;
         if(sl == 0 || ns > sl) Modify(tkt, ns, 0);
      }
   }
}

//+------------------------------------------------------------------+
//| 日足の押し目巡航(かがみ無限 抜1・無1・出1)                           |
//+------------------------------------------------------------------+
// 日足の足 s(閉じた足)で、巡航の始まり・押し目の合図が出たか。状態は oIncr/oArm に持つ
bool OshStep(int s, int d)
{
   int k = d > 0 ? 0 : 1;
   double e9 = V(hD9, 0, s), e21 = V(hD21, 0, s);
   if(e9 == EMPTY_VALUE || e21 == EMPTY_VALUE) return(false);
   bool up = d > 0 ? (e9 > e21) : (e9 < e21);
   if(!up) { oIncr[k] = false; oArm[k] = false; return(false); }
   double c = iClose(_Symbol, PERIOD_D1, s), o = iOpen(_Symbol, PERIOD_D1, s), h = iHigh(_Symbol, PERIOD_D1, s), l = iLow(_Symbol, PERIOD_D1, s);
   // 前の山:1本前から10本の高値(売りは安値)。同じ値なら古い方
   int pk = s + 1; double prev = d > 0 ? iHigh(_Symbol, PERIOD_D1, s + 1) : iLow(_Symbol, PERIOD_D1, s + 1);
   for(int j = s + 1; j <= s + 10; j++)
   {
      double v = d > 0 ? iHigh(_Symbol, PERIOD_D1, j) : iLow(_Symbol, PERIOD_D1, j);
      if(d > 0 ? (v >= prev) : (v <= prev)) { prev = v; pk = j; }
   }
   bool pulled = false;                                          // 前の山の後に9まで押した
   for(int j = pk; j >= s + 1; j--)
   {
      double e = V(hD9, 0, j);
      if(d > 0 ? (iLow(_Symbol, PERIOD_D1, j) <= e) : (iHigh(_Symbol, PERIOD_D1, j) >= e)) { pulled = true; break; }
   }
   bool brk = d > 0 ? (c > prev) : (c < prev);
   double wNow = V(hDbb2, 1, s) - V(hDbb2, 2, s), wOld = V(hDbb2, 1, s + 3) - V(hDbb2, 2, s + 3);
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
   datetime dt = iTime(_Symbol, PERIOD_D1, dd);
   if(dd < 0 || dt == oLastD) return;
   if(oLastD == 0)                                              // 起動した時:過去の日足で状態だけ作る(撃たない)
   {
      for(int s = dd + 300; s > dd; s--) { OshStep(s, 1); OshStep(s, -1); }
   }
   bool b = OshStep(dd, 1), sl = OshStep(dd, -1);
   if(oLastD != 0) { if(b) oPend[0] = true; if(sl) oPend[1] = true; }
   oLastD = dt;
}

void ApplySL(long magic, double sl)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tkt = PositionGetTicket(i);
      if(tkt == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != magic) continue;
      if(PositionGetDouble(POSITION_SL) == 0) Modify(tkt, sl, PositionGetDouble(POSITION_TP));
   }
}

void ManageOshime(int d, long magic, datetime T, datetime TS1)
{
   int dx = Done(PERIOD_D1, TS1);
   double d9 = V(hD9, 0, dx), d21 = V(hD21, 0, dx);
   datetime dclose = iTime(_Symbol, PERIOD_D1, dx) + PeriodSeconds(PERIOD_D1);
   bool sig = (d9 != EMPTY_VALUE && d21 != EMPTY_VALUE) && (d > 0 ? !(d9 > d21) : (d9 > d21));
   MqlDateTime m; TimeToStruct(T, m);
   double tpl = d > 0 ? V(hDbb35, 1, dx) : V(hDbb35, 2, dx);
   MqlTick tk; SymbolInfoTick(_Symbol, tk); double spr = tk.ask - tk.bid;
   double net = d > 0 ? iLow(_Symbol, PERIOD_D1, dx) : iHigh(_Symbol, PERIOD_D1, dx) + spr;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong tkt = PositionGetTicket(i);
      if(tkt == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != magic) continue;
      datetime ot = (datetime)PositionGetInteger(POSITION_TIME);
      double op = PositionGetDouble(POSITION_PRICE_OPEN);
      if(sig && m.hour != AvoidHour && dclose > ot) { if(ClosePos(tkt, d > 0 ? "押し目 日足219" : "押し目 日足921")) continue; }
      double sl = PositionGetDouble(POSITION_SL), tp = 0;
      if(sl == 0 || (d > 0 ? net > sl : net < sl)) sl = net;      // 網は寄せるだけ(戻さない)
      if(tpl != EMPTY_VALUE) { if(d > 0 && tpl > op) tp = tpl; if(d < 0 && tpl < op - spr) tp = tpl + spr; }
      Modify(tkt, sl, tp);
   }
}

//+------------------------------------------------------------------+
//| 入り(研究台の入りと同じ:1時間921 か 許しの瞬間)                      |
//+------------------------------------------------------------------+
bool EntrySignal(int d, datetime TS1, datetime TS2)
{
   double e9a = V(hH1_9, 0, 1), e21a = V(hH1_21, 0, 1), e9b = V(hH1_9, 0, 2), e21b = V(hH1_21, 0, 2);
   double md = V(hH1bb1, 0, 1), up1 = V(hH1bb1, 1, 1), lo1 = V(hH1bb1, 2, 1), up2 = V(hH1bb2, 1, 1), lo2 = V(hH1bb2, 2, 1);
   if(e9a == EMPTY_VALUE || e9b == EMPTY_VALUE || md == EMPTY_VALUE || up2 == EMPTY_VALUE) return(false);
   double c = iClose(_Symbol, PERIOD_H1, 1);
   bool upA = e9a > e21a, upB = e9b > e21b;
   bool side  = d > 0 ? upA : !upA;
   bool cross = d > 0 ? (upA && !upB) : (!upA && upB);
   bool p = Perm(TS1, d), pp = Perm(TS2, d);
   int dq = Done(PERIOD_D1, TS1);
   double dc = iClose(_Symbol, PERIOD_D1, dq), d21 = V(hD21, 0, dq), d21b = V(hD21, 0, dq + 3);
   if(d21 == EMPTY_VALUE || d21b == EMPTY_VALUE) return(false);
   bool qq = d > 0 ? dc > d21 : dc < d21;
   bool big21 = d > 0 ? (d21 - d21b) > 0 : (d21 - d21b) < 0;           // 日足21の向き(3本前と比べる)
   bool kawa = d > 0 ? c > up1 : c < lo1;                                // 川の外(±1σ)
   bool chi  = d > 0 ? c > iHigh(_Symbol, PERIOD_H1, 1 + 21) : c < iLow(_Symbol, PERIOD_H1, 1 + 21);   // 遅行スパン:21本前の高値(安値)の向こう
   bool ns   = d > 0 ? c <= up2 : c >= lo2;                               // 竿先(±2σの外)では入らない
   bool e921 = cross && p;
   bool kai  = p && !pp && side && !cross;
   int k9 = K9(dq, d), k9p = K9(Done(PERIOD_D1, TS2), d);
   kai = kai && (k9 >= KaiK9);
   bool first = (k9 >= KaiK9) && !(k9p >= KaiK9) && p && side && !cross && (k9 == KaiK9);
   kai = kai || first;
   return(((e921 && kawa && chi) || (kai && qq)) && ns && big21);
}

//+------------------------------------------------------------------+
void OnTick()
{
   datetime T = iTime(_Symbol, PERIOD_H1, 0);
   if(T <= 0 || T == lastBar) return;
   if(lastBar == 0) { lastBar = T; return; }                 // 起動した直後は過去の足で撃たない
   lastBar = T;
   // 合図の足(1本前)が閉じた時刻。週末をまたぐと新しい足の始まり T とは違う(11-09 写しの照らしで見つけた)
   datetime TS1 = iTime(_Symbol, PERIOD_H1, 1) + PeriodSeconds(PERIOD_H1);
   datetime TS2 = iTime(_Symbol, PERIOD_H1, 2) + PeriodSeconds(PERIOD_H1);
   MqlDateTime m; TimeToStruct(T, m);
   bool avoid = (m.hour == AvoidHour);
   bool yas = UseYasumi && Yasumi(T);

   // 1. 降り(合図)と、利確・TS の付け替え
   ManageMain(1, MagicBuy, T, TS1);
   if(UseSell) ManageMain(-1, MagicSell, T, TS1);
   if(UseDoten) ManageDoten(TS1);
   if(UseTai) ManageTai(T, TS1);
   if(UseOshime) { ManageOshime(1, MagicOshB, T, TS1); ManageOshime(-1, MagicOshS, T, TS1); OshimeDaily(TS1); }

   // 2. 入り
   for(int k = 0; k < 2; k++)
   {
      int d = k == 0 ? 1 : -1;
      if(d < 0 && !UseSell) continue;
      long mg = d > 0 ? MagicBuy : MagicSell;
      bool sig = EntrySignal(d, TS1, TS2) && !yas;
      bool pend = d > 0 ? pendBuy : pendSell;
      bool go = false;
      if(avoid) { if(sig) { if(d > 0) pendBuy = true; else pendSell = true; Log("0時をよけて次の足へ", T, d, 0, 0, ""); } }
      else { go = sig || pend; if(d > 0) pendBuy = false; else pendSell = false; }
      if(go && CountPos(mg) < MaxPos) Open(d, mg, T, sig ? "入り" : "0時をよけた入り");
      if(go && d > 0 && UseTai && CountPos(MagicTai) < 1) Open(1, MagicTai, T, "鯛の刺身");
   }

   // 2b. 日足の押し目巡航:日足が閉じた後の最初の足(0時はよけて1時)で入る。網は前の日足のひげ先
   if(UseOshime && !avoid)
   {
      for(int k = 0; k < 2; k++)
      {
         if(!oPend[k]) continue;
         oPend[k] = false;
         int d = k == 0 ? 1 : -1; long mg = d > 0 ? MagicOshB : MagicOshS;
         if(yas || CountPos(mg) >= 5) continue;
         int dl = Done(PERIOD_D1, TS1);
         MqlTick tk; SymbolInfoTick(_Symbol, tk);
         double sl = d > 0 ? iLow(_Symbol, PERIOD_D1, dl) : iHigh(_Symbol, PERIOD_D1, dl) + (tk.ask - tk.bid);
         if(d > 0 ? (sl >= tk.ask) : (sl <= tk.ask)) continue;   // 網が入り値の向こうなら入らない(研究台と同じ)
         Open(d, mg, T, "押し目巡航");                          // 網は次の足から(研究台と同じ:入った足では網を見ない)
      }
   }

   // 3. ドテン買い:売りの利確で構え、1時間の921が出た次の足で入る
   if(UseDoten && armDoten)
   {
      double e9a = V(hH1_9, 0, 1), e21a = V(hH1_21, 0, 1), e9b = V(hH1_9, 0, 2), e21b = V(hH1_21, 0, 2);
      if(e9a != EMPTY_VALUE && e9b != EMPTY_VALUE && (e9a > e21a) && !(e9b > e21b))
      {
         armDoten = false;
         if(!yas && CountPos(MagicDoten) < 1) Open(1, MagicDoten, T, "ドテン買い");
      }
   }
   SaveFlags();
}

//+------------------------------------------------------------------+
//| 約定の確かめ・カウンター・ドテンの構え                               |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &request, const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol) return;
   long mg = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
   if(mg != MagicBuy && mg != MagicSell && mg != MagicDoten && mg != MagicTai && mg != MagicOshB && mg != MagicOshS) return;
   long entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   double px = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
   if(entry == DEAL_ENTRY_IN) { Log("約定(入り)", 0, (mg == MagicSell || mg == MagicOshS) ? -1 : 1, 0, px, "deal=" + (string)trans.deal); return; }
   if(entry != DEAL_ENTRY_OUT) return;
   long rsn = HistoryDealGetInteger(trans.deal, DEAL_REASON);
   string w = "ほか";
   if(rsn == DEAL_REASON_TP) { cntTP++; w = "利確"; }
   else if(rsn == DEAL_REASON_SL) { cntSL++; w = "TS"; }
   else if(rsn == DEAL_REASON_EXPERT) { cntSig++; w = "合図"; }
   else cntOther++;
   Log("約定(降り)", 0, (mg == MagicSell || mg == MagicOshS) ? -1 : 1, 0, px, w + " 損益=" + DoubleToString(HistoryDealGetDouble(trans.deal, DEAL_PROFIT), 0) + " deal=" + (string)trans.deal);
   if(mg == MagicSell && rsn == DEAL_REASON_TP && UseDoten) { armDoten = true; SaveFlags(); }
}
//+------------------------------------------------------------------+

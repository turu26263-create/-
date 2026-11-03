//+------------------------------------------------------------------+
//|                                       PERFECT_MINADEIN_KIWAMI.mq4|
//|                                            Skill Host Strategist |
//| v10.2 (2026-11-03) たくちん「直して」で決まりを3つ直した:           |
//|   ①斥候は一度9MAの上に出てから死神の対象(生まれてすぐ刈られない)  |
//|     斥候は1本の足で1回まで                                        |
//|   ②本隊の条件 ma9>ma5 → ma5>ma9(上向きの並び)                    |
//|   ③bb丸まりは確定足で見る(+2σの足1 < 足2)                        |
//| v10.1 売り買いの決まりは v10.0 のまま。                             |
//|   直した所: コンパイルが通らない所(Time/Close の [ ])、戻り値の確認、 |
//|   注文コメントの読み方(後ろに付け足されても読める)、建値網の StopLevel、|
//|   カウンター常備(降りた理由・網に掛かった足)を OnDeinit で書き出し。  |
//|   決まりを変えるかもしれない所は input にして、既定値=v10.0 と同じ動き。|
//+------------------------------------------------------------------+
#property copyright "Skill Host Strategist"
#property version   "10.2"
#property strict

//--- 外部パラメータ(v10.0 と同じ)
input double ScoutLots   = 0.05;       // 【斥候4】の偵察ロット数（完全無限リーチ化）
input double MainLots    = 0.10;       // 【バンドブレイク】本隊1本あたりのロット（×4本投入）
input int    MagicNumber = 888999;     // 究極ミナデイン識別番号
//--- たくちんの「ご」待ちのスイッチ(既定値は v10.0 と同じ動き)
input bool   ScoutDieBy9MA   = true;   // 斥候も9MA割れで死神に刈らせる
input bool   ScoutArmAbove9  = true;   // ↑は斥候が一度9MAの上に出てから(v10.0=false)
input bool   ScoutOncePerBar = true;   // 斥候は1本の足で1回まで(v10.0=false)

#define C_SCOUT "Scout_4"
#define C_MAIN  "Main_BrakEOUT"

//--- 内部制御用変数
static datetime last_bar_time  = 0;
static datetime last_scout_bar = 0;
static bool     scout_armed    = false;   // 斥候が一度9MAの上に出たか

//--- カウンター用(売り買いには使わない)
int    g_tk[];      // 自分で閉じた玉のチケット
string g_rs[];      // その理由
int    g_in_scout = 0, g_in_main = 0;

void Remember(int ticket, string reason)
{
   int n = ArraySize(g_tk);
   ArrayResize(g_tk, n + 1); ArrayResize(g_rs, n + 1);
   g_tk[n] = ticket; g_rs[n] = reason;
}
string ReasonOf(int ticket)
{
   for(int i = 0; i < ArraySize(g_tk); i++) if(g_tk[i] == ticket) return g_rs[i];
   return "";
}
bool IsScout(string c) { return StringFind(c, C_SCOUT) == 0; }
bool IsMain (string c) { return StringFind(c, C_MAIN)  == 0; }
double Pip() { return (Digits == 3 || Digits == 5) ? Point * 10 : Point; }

bool CloseSelected(string reason)
{
   RefreshRates();
   double price = (OrderType() == OP_BUY) ? Bid : Ask;
   int tk = OrderTicket();
   if(OrderClose(tk, OrderLots(), price, 3, clrRed)) { Remember(tk, reason); return true; }
   Print("決済失敗 ", tk, " ", reason, " err=", GetLastError());
   return false;
}

int OnInit()
{
   if(Period() != PERIOD_H4)
      Print("注意: 決まりは4時間足。いまのチャートは ", Period(), " 分足。4時間足に付けてください");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. ポジションのリアルタイム追跡と識別
   int scout_ticket = -1;
   int main_count = 0;
   int total_positions = 0;

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber || OrderSymbol() != Symbol()) continue;
      total_positions++;
      if(IsScout(OrderComment()))     scout_ticket = OrderTicket();
      else if(IsMain(OrderComment())) main_count++;
   }

   double ma9_current = iMA(NULL, 0, 9, 0, MODE_SMA, PRICE_CLOSE, 0);
   double bb_upper_1  = iBands(NULL, 0, 20, 2, 0, PRICE_CLOSE, MODE_UPPER, 1);
   double bb_upper_2  = iBands(NULL, 0, 20, 2, 0, PRICE_CLOSE, MODE_UPPER, 2);

   // 斥候の「死神の対象になったか」: 一度9MAの上に出たら対象。建値網が付いていれば(再起動後も)対象
   if(scout_ticket < 0) scout_armed = false;
   else if(!scout_armed)
   {
      if(Bid > ma9_current) scout_armed = true;
      else if(OrderSelect(scout_ticket, SELECT_BY_TICKET) && OrderStopLoss() > 0) scout_armed = true;
   }
   bool scout_die = ScoutDieBy9MA && (!ScoutArmAbove9 || scout_armed);

   // 💀【スペル：はやぶさの死神】現在値が9MAを割ったら一括全決済
   if(total_positions > 0 && Bid < ma9_current)
   {
      bool closed_any = false;
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
         if(OrderMagicNumber() != MagicNumber || OrderSymbol() != Symbol()) continue;
         if(!scout_die && IsScout(OrderComment())) continue;
         if(CloseSelected("死神9MA割れ")) closed_any = true;
      }
      if(scout_die || closed_any) return;
   }

   // 🛡️【スペル：しあわせセット（建値即座ロック） ＆ 竿先bb丸まりポジコン】
   if(scout_ticket > 0)
   {
      if(OrderSelect(scout_ticket, SELECT_BY_TICKET))
      {
         double stop_level = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
         if(OrderStopLoss() == 0 && Bid > OrderOpenPrice() + (10 * Point)
            && Bid - OrderOpenPrice() > stop_level)
         {
            if(!OrderModify(OrderTicket(), OrderOpenPrice(), OrderOpenPrice(), OrderTakeProfit(), 0, clrGreen))
               Print("建値ロック失敗 err=", GetLastError());
         }
      }

      // 💡【スペル：竿先bb丸まりポジコン】確定足で+2σが1本前より下がった→本隊4本だけ利確
      if(main_count > 0 && bb_upper_1 < bb_upper_2)
      {
         for(int i = OrdersTotal() - 1; i >= 0; i--)
         {
            if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
            if(OrderMagicNumber() == MagicNumber && OrderSymbol() == Symbol() && IsMain(OrderComment()))
               CloseSelected("竿先bb丸まり");
         }
         return;
      }
   }

   // 💡【リアルタイムひげ先取り（斥候4）】
   if(total_positions == 0 && !(ScoutOncePerBar && last_scout_bar == Time[0]))
   {
      double ma200_live = iMA(NULL, 0, 200, 0, MODE_SMA, PRICE_CLOSE, 0);
      double ma200_prev = iMA(NULL, 0, 200, 0, MODE_SMA, PRICE_CLOSE, 1);
      double rsi_live   = iRSI(NULL, 0, 14, PRICE_CLOSE, 0);

      if(ma200_live > ma200_prev && rsi_live <= 35.0 && Bid <= ma200_live + (2 * Point))
      {
         RefreshRates();
         int t_scout = OrderSend(Symbol(), OP_BUY, ScoutLots, Ask, 3, 0, 0, C_SCOUT, MagicNumber, 0, clrYellow);
         if(t_scout > 0) { g_in_scout++; last_scout_bar = Time[0]; return; }
         Print("斥候 発注失敗 err=", GetLastError());
      }
   }

   // ここから先は「確定足の切り替わり時」のみ本隊のバンドブレイクを判定する
   if(Time[0] == last_bar_time) return;

   double ma5_1    = iMA(NULL, 0, 5, 0, MODE_SMA, PRICE_CLOSE, 1);
   double ma9_1    = iMA(NULL, 0, 9, 0, MODE_SMA, PRICE_CLOSE, 1);
   double ma21_1   = iMA(NULL, 0, 21, 0, MODE_SMA, PRICE_CLOSE, 1);
   double ma200_1  = iMA(NULL, 0, 200, 0, MODE_SMA, PRICE_CLOSE, 1);
   double close_1  = Close[1];
   double bb_up_1  = iBands(NULL, 0, 20, 2, 0, PRICE_CLOSE, MODE_UPPER, 1);

   // 🐎【スペル：押し目買い無限4 バンドブレイクで4】
   if(total_positions == 1 && scout_ticket > 0 && main_count == 0)
   {
      if(close_1 > bb_up_1 && ma5_1 > ma9_1 && ma21_1 > ma200_1)   // v10.2: ma9>ma5 → ma5>ma9
      {
         int ok = 0;
         for(int k = 0; k < 4; k++)
         {
            RefreshRates();
            int t = OrderSend(Symbol(), OP_BUY, MainLots, Ask, 3, 0, 0, C_MAIN, MagicNumber, 0, clrBlue);
            if(t > 0) ok++; else Print("本隊 発注失敗 ", k + 1, "本目 err=", GetLastError());
         }
         g_in_main += ok;
         if(ok > 0) last_bar_time = Time[0];
      }
   }
}

//+------------------------------------------------------------------+
//| カウンター常備: 降りた理由 と 網に掛かった足(書き出すだけ)            |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   string kinds[2] = {"斥候4", "本隊"};
   string rsn[4]   = {"死神9MA割れ", "竿先bb丸まり", "網(建値)", "その他"};
   int    cnt[2][4]; double pl[2][4];
   ArrayInitialize(cnt, 0); ArrayInitialize(pl, 0);
   double pip = Pip();
   int    wick_only = 0, body_cross = 0;

   for(int i = 0; i < OrdersHistoryTotal(); i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(OrderMagicNumber() != MagicNumber || OrderSymbol() != Symbol()) continue;
      if(OrderType() != OP_BUY) continue;
      int k = IsScout(OrderComment()) ? 0 : 1;
      string r = ReasonOf(OrderTicket());
      int ri = 3;
      if(r == rsn[0]) ri = 0; else if(r == rsn[1]) ri = 1;
      else if(OrderStopLoss() > 0 && MathAbs(OrderClosePrice() - OrderStopLoss()) <= 5 * Point) ri = 2;
      cnt[k][ri]++;
      pl[k][ri] += OrderProfit() + OrderSwap() + OrderCommission();

      if(ri == 2)   // ロウソク・カウンター: 網に掛かった足(確定した足として見る)
      {
         int sh = iBarShift(NULL, 0, OrderCloseTime());
         double o = iOpen(NULL, 0, sh), h = iHigh(NULL, 0, sh), l = iLow(NULL, 0, sh), c = iClose(NULL, 0, sh);
         bool wick = (c > OrderStopLoss());   // 買いの網: 終値が網の上に戻った=ひげだけ
         if(wick) wick_only++; else body_cross++;
         PrintFormat("ロウソク,1本,%s,%s,長さ%.1f,実体%.1f,上ひげ%.1f,下ひげ%.1f,%s",
            kinds[k], TimeToString(OrderCloseTime()), (h - l) / pip, MathAbs(c - o) / pip,
            (h - MathMax(o, c)) / pip, (MathMin(o, c) - l) / pip, wick ? "ひげだけ" : "実体で渡った");
      }
   }
   PrintFormat("カウンター,入った回数,斥候4,%d,本隊,%d", g_in_scout, g_in_main);
   for(int k = 0; k < 2; k++)
   {
      int tot = 0; double tpl = 0;
      for(int r = 0; r < 4; r++) { tot += cnt[k][r]; tpl += pl[k][r]; }
      for(int r = 0; r < 4; r++)
         if(cnt[k][r] > 0)
            PrintFormat("カウンター,%s,%s,%d回(%.0f%%),損益%.0f", kinds[k], rsn[r], cnt[k][r],
                        100.0 * cnt[k][r] / MathMax(tot, 1), pl[k][r]);
      PrintFormat("カウンター,%s,合計,%d回,損益%.0f", kinds[k], tot, tpl);
   }
   PrintFormat("ロウソク,網,ひげだけ%d,実体で渡った%d", wick_only, body_cross);
}

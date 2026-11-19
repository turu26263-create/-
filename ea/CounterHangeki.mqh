//+------------------------------------------------------------------+
//| CounterHangeki.mqh  カウンター反撃(7段回収)ロット部品  2026-11-19     |
//| 元帳:12_エントリー手法の皿/カウンター反撃_元帳.md(旧 カウンター反撃)                      |
//| MT4・MT5 どちらでも #include して使う                             |
//|                                                                  |
//| 決まり(固定):                                                    |
//|  ロット 0.01→0.03→0.06→0.15→0.3→0.6→1.2                          |
//|  1玉が負けて降りたら次は1段上。1.2で止める(戻さない)               |
//|  勝って降りたら0.01に戻す                                        |
//|  段は全部の玉で1本(CH_MAGICS に入れた全部のマジック・同じ通貨)     |
//| 研究台(nanpin7.py)と同じ数え方にそろえた所(11-19):                 |
//|  ・勝ち負けは値の損益(OrderProfit/DEAL_PROFIT)で見る。スワップ・    |
//|    手数料は入れない(研究台は pips で見る)                          |
//|  ・入る足の始まり(before)より前に閉じた玉だけ数える。同じ足で閉じた |
//|    玉は次の入りから効く(研究台は同じ時刻なら入りを先に数える)       |
//| 使い方: OnInit で CH_SetMagics(配列, 数) → 入る時に                 |
//|         double lot = CH_Lot(足の始まりの時刻);                      |
//+------------------------------------------------------------------+
#ifndef COUNTER_HANGEKI_MQH
#define COUNTER_HANGEKI_MQH

double CH_DAN[7] = {0.01, 0.03, 0.06, 0.15, 0.30, 0.60, 1.20};
int    CH_MAGICS[];
int    CH_NMAG = 0;

void CH_SetMagics(const int &m[], int n)
{
   CH_NMAG = n; ArrayResize(CH_MAGICS, n);
   for(int i = 0; i < n; i++) CH_MAGICS[i] = m[i];
}

bool CH_Mine(long magic)
{
   for(int i = 0; i < CH_NMAG; i++) if(CH_MAGICS[i] == magic) return(true);
   return(false);
}

// before より前に閉じた玉を、閉じた順にたどって段(0〜6)を出す
int CH_Dan(datetime before)
{
   int lv = 0;
#ifdef __MQL5__
   if(!HistorySelect(0, before)) return 0;
   int n = HistoryDealsTotal();
   for(int i = 0; i < n; i++)
   {
      ulong tk = HistoryDealGetTicket(i);
      if(tk == 0) continue;
      if(HistoryDealGetString(tk, DEAL_SYMBOL) != _Symbol) continue;
      if(!CH_Mine(HistoryDealGetInteger(tk, DEAL_MAGIC))) continue;
      long ent = HistoryDealGetInteger(tk, DEAL_ENTRY);
      if(ent != DEAL_ENTRY_OUT && ent != DEAL_ENTRY_INOUT && ent != DEAL_ENTRY_OUT_BY) continue;
      if((datetime)HistoryDealGetInteger(tk, DEAL_TIME) >= before) continue;
      double p = HistoryDealGetDouble(tk, DEAL_PROFIT);
      lv = (p > 0) ? 0 : MathMin(lv + 1, 6);
   }
#else
   int n = OrdersHistoryTotal();
   datetime ct[]; double pf[]; int m = 0;
   ArrayResize(ct, n); ArrayResize(pf, n);
   for(int i = 0; i < n; i++)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(OrderSymbol() != _Symbol || !CH_Mine(OrderMagicNumber())) continue;
      if(OrderType() != OP_BUY && OrderType() != OP_SELL) continue;
      if(OrderCloseTime() >= before) continue;
      ct[m] = OrderCloseTime(); pf[m] = OrderProfit(); m++;
   }
   for(int a = 1; a < m; a++)   // 閉じた時刻の順に並べる(履歴の並びは順番どおりとは限らない)
   {
      datetime kt = ct[a]; double kp = pf[a]; int b = a - 1;
      while(b >= 0 && ct[b] > kt) { ct[b + 1] = ct[b]; pf[b + 1] = pf[b]; b--; }
      ct[b + 1] = kt; pf[b + 1] = kp;
   }
   for(int j = 0; j < m; j++) lv = (pf[j] > 0) ? 0 : MathMin(lv + 1, 6);
#endif
   return lv;
}

// 業者のロットの刻み・上下限に合わせた、次に入る玉のロット
double CH_Lot(datetime before)
{
   double lot  = CH_DAN[CH_Dan(before)];
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double mx   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step > 0) lot = MathFloor(lot / step + 1e-9) * step;
   lot = MathMax(mn, MathMin(mx, lot));
   return NormalizeDouble(lot, 2);
}

#endif

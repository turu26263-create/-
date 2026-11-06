//+------------------------------------------------------------------+
//| TaiSashimi_v1.mq4  鯛の刺身EA(たくちん 11-06「ご」)              |
//| 中身は engine/engine_tai2.py と同じ(買い=縄8あり/売り=縄8なし)   |
//| 5分足チャートに貼る。判断は確定足だけ(新しい5分足の最初のティック) |
//|                                                                  |
//| 縄1 4時間の9上   : 確定4h足の終値 > 4hEMA9(売りは <)            |
//| 縄2 1時間の21上  : 確定1h足の終値 > 1hEMA21(売りは <)           |
//| 縄3 5分の921     : 確定5分足で EMA9 が EMA21 を上抜け(売りは219)  |
//|                   +その時の許し(縄1+縄2)→ 次の足の始値で入る    |
//| 縄3改            : 許しが×→○になった最初の5分足で 9>21(売り 9<21)|
//|                   なら入る                                       |
//| 縄4 だまし回避    : (921の入り)終値が+1σの外 かつ 21本前の高値を上抜け|
//|                   (売り:−1σの外 かつ 21本前の安値を下抜け)       |
//| 縄4改            : (縄3改の入り)確定4h足の終値 > 4hEMA21(売り <)  |
//| 縄5 竿先で入らない: 終値が+2σの外なら入らない(売り −2σの外)      |
//| 縄8 4時間の竿先   : 買いだけ。確定4h足の21の角度が55度超なら入らない|
//|                   角度=横1本6ドット、縦=直近150本の高安を500ドット、 |
//|                   21の3本分の傾き【置き換え】                       |
//| 縄7 降り          : 入った後に確定した1h足が9割れ(実体の真ん中と   |
//|                   終値が1hEMA9の下。売りは上)→ 次の5分足の始値で降り|
//| 玉は向きごとに1つ。遅行スパンは21本前(たくちんの記憶)               |
//|                                                                  |
//| 【未検証】このファイルはクラウドで書いた。MetaEditor でのコンパイル・ |
//|  テスター・デモはまだ。研究台(HistData・EST)の4時間足の区切りと、    |
//|  業者のサーバー時刻の4時間足の区切りは違うので、入りがずれる所がある |
//+------------------------------------------------------------------+
#property strict
#property version "1.00"

input double Lots            = 0.10;
input int    MagicBuy        = 92101;
input int    MagicSell       = 92102;
input bool   UseBuy          = true;
input bool   UseSell         = true;
input int    MaxSpreadPoints = 30;     // これより広いと新規を止める(3桁ならpoint=0.001 → 30=3.0p)
input int    SlippagePoints  = 10;
input int    MaxTickAgeSec   = 10;     // 最新ティックがこれより古いと新規を止める
input string StrategyVer     = "tai_v1";

#define LAG 21                 // 遅行スパン 21本前(変えない)
#define SAO 2.0                // 竿先 2σ
#define ANG_SAO 55.0           // 縄8 4hの竿先 55度

datetime lastBar=0;
bool     prevPermB=false, prevPermS=false, prevInit=false;
string   logFile;

// ---- カウンター(売り買いは変えない。数えるだけ) ----
int    cntEnt[2][2];           // [向き 0買い/1売り][種類 0=921 1=改]
int    cntExit[2][2];          // [向き][理由 0=9割れ 1=その他]
double sumExit[2][2];

//+------------------------------------------------------------------+
int OnInit()
{
   if(Period()!=PERIOD_M5){ Print("5分足チャートに貼ってください"); return(INIT_FAILED); }
   logFile="TaiSashimi_"+Symbol()+"_log.csv";
   int h=FileOpen(logFile,FILE_CSV|FILE_READ|FILE_WRITE|FILE_SHARE_READ,',');
   if(h!=INVALID_HANDLE){
      if(FileSize(h)==0) FileWrite(h,"kind","signal_id","bar_open_time","bar_close_time","decision_time","tick_time","O","H","L","C","Bid","Ask","spread_pt","requested","filled","slippage_pt","ticket","retcode","reason");
      FileClose(h);
   }
   ArrayInitialize(cntEnt,0); ArrayInitialize(cntExit,0); ArrayInitialize(sumExit,0.0);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   string nm[2]={"買い","売り"};
   for(int d=0; d<2; d++){
      Print("カウンター,",nm[d],",入り,921=",cntEnt[d][0]," 改=",cntEnt[d][1]);
      int n=cntExit[d][0]+cntExit[d][1];
      for(int r=0; r<2; r++){
         string rn=(r==0?"9割れ":"その他");
         double pc=(n>0?100.0*cntExit[d][r]/n:0);
         Print("カウンター,",nm[d],",玉,",rn,",",cntExit[d][r],"回(",DoubleToString(pc,1),"%),",DoubleToString(sumExit[d][r],0),"円");
      }
      Print("カウンター,",nm[d],",玉,合計,",n,"回,",DoubleToString(sumExit[d][0]+sumExit[d][1],0),"円");
   }
}

//+------------------------------------------------------------------+
void Log(string kind,string sid,double req,double fill,int ticket,int ret,string why)
{
   int h=FileOpen(logFile,FILE_CSV|FILE_READ|FILE_WRITE|FILE_SHARE_READ,',');
   if(h==INVALID_HANDLE) return;
   FileSeek(h,0,SEEK_END);
   MqlTick tk; SymbolInfoTick(Symbol(),tk);
   double slip=(fill>0&&req>0)?(fill-req)/Point:0;
   FileWrite(h,kind,sid,TimeToString(Time[1],TIME_DATE|TIME_SECONDS),TimeToString(Time[1]+300,TIME_DATE|TIME_SECONDS),
             TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),TimeToString(tk.time,TIME_DATE|TIME_SECONDS),
             DoubleToString(Open[1],Digits),DoubleToString(High[1],Digits),DoubleToString(Low[1],Digits),DoubleToString(Close[1],Digits),
             DoubleToString(tk.bid,Digits),DoubleToString(tk.ask,Digits),IntegerToString((int)MarketInfo(Symbol(),MODE_SPREAD)),
             DoubleToString(req,Digits),DoubleToString(fill,Digits),DoubleToString(slip,1),IntegerToString(ticket),IntegerToString(ret),why);
   FileClose(h);
}

// 4h の21の角度(engine_ichi.angle21 と同じ測り方)。sh=見る確定足
double Angle21H4(int sh)
{
   double e0=iMA(NULL,PERIOD_H4,21,0,MODE_EMA,PRICE_CLOSE,sh);
   double e3=iMA(NULL,PERIOD_H4,21,0,MODE_EMA,PRICE_CLOSE,sh+3);
   int hi=iHighest(NULL,PERIOD_H4,MODE_HIGH,150,sh), lo=iLowest(NULL,PERIOD_H4,MODE_LOW,150,sh);
   if(hi<0||lo<0) return(0);
   double rng=iHigh(NULL,PERIOD_H4,hi)-iLow(NULL,PERIOD_H4,lo);
   if(rng<=0) return(0);
   return(MathArctan(((e0-e3)/rng*500.0)/18.0)*180.0/M_PI);
}

// 許し(縄1+縄2)。d=+1買い/-1売り。いま確定している 4h・1h の足(shift=1)で見る
bool Perm(int d)
{
   double c4=iClose(NULL,PERIOD_H4,1), e9_4=iMA(NULL,PERIOD_H4,9,0,MODE_EMA,PRICE_CLOSE,1);
   double c1=iClose(NULL,PERIOD_H1,1), e21_1=iMA(NULL,PERIOD_H1,21,0,MODE_EMA,PRICE_CLOSE,1);
   if(c4<=0||c1<=0) return(false);
   if(d>0) return(c4>e9_4 && c1>e21_1);
   return(c4<e9_4 && c1<e21_1);
}

// 入りの合図。kind に 0=921/1=改 を返す
bool Entry(int d,bool perm,bool prevPerm,int &kind)
{
   double e9_1=iMA(NULL,0,9,0,MODE_EMA,PRICE_CLOSE,1),  e21_1=iMA(NULL,0,21,0,MODE_EMA,PRICE_CLOSE,1);
   double e9_2=iMA(NULL,0,9,0,MODE_EMA,PRICE_CLOSE,2),  e21_2=iMA(NULL,0,21,0,MODE_EMA,PRICE_CLOSE,2);
   double u1=iBands(NULL,0,20,1.0,0,PRICE_CLOSE,MODE_UPPER,1), l1=iBands(NULL,0,20,1.0,0,PRICE_CLOSE,MODE_LOWER,1);
   double u2=iBands(NULL,0,20,SAO,0,PRICE_CLOSE,MODE_UPPER,1), l2=iBands(NULL,0,20,SAO,0,PRICE_CLOSE,MODE_LOWER,1);
   double c=Close[1];
   double c4=iClose(NULL,PERIOD_H4,1), e21_4=iMA(NULL,PERIOD_H4,21,0,MODE_EMA,PRICE_CLOSE,1);
   bool up1=e9_1>e21_1, up2=e9_2>e21_2;
   bool cross=(d>0)?(up1&&!up2):(!up1&&up2);
   bool side =(d>0)?up1:!up1;
   bool kawa =(d>0)?(c>u1):(c<l1);
   bool chi  =(d>0)?(c>High[1+LAG]):(c<Low[1+LAG]);
   bool q    =(d>0)?(c4>e21_4):(c4<e21_4);
   bool ns   =(d>0)?(c<=u2):(c>=l2);
   bool e921 = cross && perm && kawa && chi;
   bool kai  = perm && !prevPerm && side && !cross && q;
   if(!((e921||kai)&&ns)) return(false);
   if(d>0 && Angle21H4(1)>ANG_SAO) return(false);    // 縄8 は買いだけ
   kind=e921?0:1;
   return(true);
}

// 縄7:入った後に確定した 1h 足の9割れ
bool Ware(int d,datetime openTime)
{
   datetime t1=iTime(NULL,PERIOD_H1,1);
   if(t1+3600<=openTime) return(false);              // 入る前に確定していた足は見ない
   double o=iOpen(NULL,PERIOD_H1,1), c=iClose(NULL,PERIOD_H1,1), e9=iMA(NULL,PERIOD_H1,9,0,MODE_EMA,PRICE_CLOSE,1);
   double mid=(o+c)/2.0;
   if(d>0) return(mid<e9 && c<e9);
   return(mid>e9 && c>e9);
}

int FindPos(int magic)
{
   for(int i=OrdersTotal()-1;i>=0;i--)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==Symbol() && OrderMagicNumber()==magic) return(OrderTicket());
   return(-1);
}

bool TradeOK(string &why)
{
   MqlTick tk; if(!SymbolInfoTick(Symbol(),tk)){ why="ティックなし"; return(false); }
   if(TimeCurrent()-tk.time>MaxTickAgeSec){ why="ティックが古い"; return(false); }
   if((int)MarketInfo(Symbol(),MODE_SPREAD)>MaxSpreadPoints){ why="スプレッド広い"; return(false); }
   if(!IsTradeAllowed()){ why="売買不可"; return(false); }
   if(AccountFreeMarginCheck(Symbol(),OP_BUY,Lots)<=0){ why="証拠金不足"; return(false); }
   return(true);
}

void Open(int d,int kind)
{
   int magic=(d>0?MagicBuy:MagicSell);
   string sid=Symbol()+"|"+IntegerToString(Period())+"|"+IntegerToString((int)Time[1])+"|"+(d>0?"B":"S")+"|"+StrategyVer;
   string gv="tai_"+IntegerToString(magic)+"_"+IntegerToString((int)Time[1]);
   if(GlobalVariableCheck(gv)){ Log("skip",sid,0,0,-1,0,"同じsignal_id"); return; }
   string why="";
   if(!TradeOK(why)){ Log("skip",sid,0,0,-1,0,why); return; }
   RefreshRates();
   double px=(d>0?Ask:Bid);
   string cm=(kind==0?"tai921":"taiKai");
   GlobalVariableSet(gv,TimeCurrent());               // 打つ前に印(再起動しても同じ合図で2回撃たない)
   int tk=OrderSend(Symbol(),(d>0?OP_BUY:OP_SELL),Lots,px,SlippagePoints,0,0,cm,magic,0,(d>0?clrBlue:clrRed));
   if(tk<0){
      int err=GetLastError(); Log("fail",sid,px,0,-1,err,"新規失敗(打ち直さない。次の合図を待つ)");
      return;
   }
   double fill=0; if(OrderSelect(tk,SELECT_BY_TICKET)) fill=OrderOpenPrice();
   Log("open",sid,px,fill,tk,0,cm);
   cntEnt[d>0?0:1][kind]++;
}

void Close(int d,int ticket,string why)
{
   if(!OrderSelect(ticket,SELECT_BY_TICKET)) return;
   RefreshRates();
   double px=(d>0?Bid:Ask);
   string sid=Symbol()+"|"+IntegerToString(Period())+"|"+IntegerToString((int)Time[1])+"|X"+(d>0?"B":"S")+"|"+StrategyVer;
   if(!OrderClose(ticket,OrderLots(),px,SlippagePoints,clrGray)){
      int err=GetLastError(); Log("fail",sid,px,0,ticket,err,"決済失敗(次の足でもう一度見る)"); return;
   }
   double pl=0; if(OrderSelect(ticket,SELECT_BY_TICKET,MODE_HISTORY)) pl=OrderProfit()+OrderSwap()+OrderCommission();
   Log("close",sid,px,OrderClosePrice(),ticket,0,why);
   int di=(d>0?0:1); int r=(why=="9割れ"?0:1); cntExit[di][r]++; sumExit[di][r]+=pl;
}

//+------------------------------------------------------------------+
void OnTick()
{
   datetime cur=iTime(Symbol(),Period(),0);
   if(cur<=0||cur==lastBar) return;
   if(lastBar==0){                                   // 起動直後は撃たない。許しの前の値だけ覚える
      lastBar=cur; prevPermB=Perm(1); prevPermS=Perm(-1); prevInit=true; return;
   }
   lastBar=cur;
   if(Bars<200) return;

   bool pb=Perm(1), ps=Perm(-1);
   for(int k=0;k<2;k++){
      int d=(k==0?1:-1); bool use=(k==0?UseBuy:UseSell); int magic=(k==0?MagicBuy:MagicSell);
      bool perm=(k==0?pb:ps), prev=(k==0?prevPermB:prevPermS);
      int tk=FindPos(magic);
      if(tk>=0){
         if(OrderSelect(tk,SELECT_BY_TICKET) && Ware(d,OrderOpenTime())) Close(d,tk,"9割れ");
      } else if(use){
         int kind=0;
         if(Entry(d,perm,prev,kind)) Open(d,kind);
      }
   }
   prevPermB=pb; prevPermS=ps;
}
//+------------------------------------------------------------------+

# 鯛の刺身 v2: v1(H4終値>9・H1終値>21・M5の921・川の上の外・遅行21本前上抜け)に A/B/C を1つずつ足す
# A 差し込み型【置き換え:だまし回避の手本】直近6本の1時間足の安値が4時間21の5p内、1時間21の傾きが上、4時間21が寝ていない(上向き)
# B 起き上がり型【置き換え】5分足21の角度が0〜30度(起き始め)、直近12本のうちに0度以下(寝ていた)があった
#    角度=MT4画面の見た目:横1本6ドット、縦は直近150本の高安を500ドット、21の3本分の傾き
# C 降り方:5分足の終値が+1σの内側へ戻って確定したら次の足の始値で降りる(219の代わり)
import pandas as pd, numpy as np, sys
S=sys.argv[1]; LAG=21
d=pd.read_csv(S+'/data/USDJPY5.csv',header=None,names='d t o h l c v'.split())
d.index=pd.to_datetime(d.d+' '+d.t,format='%Y.%m.%d %H:%M'); d=d[['o','h','l','c']]
def rs(r):
    x=d.resample(r,label='left',closed='left').agg({'o':'first','h':'max','l':'min','c':'last'}).dropna()
    x['m9']=x.c.rolling(9).mean(); x['m21']=x.c.rolling(21).mean(); return x
h4=rs('4h'); h1=rs('1h')
h4['end']=h4.index+pd.Timedelta('4h'); h1['end']=h1.index+pd.Timedelta('1h')
# 1時間足の各足に、その足が閉じた時の4時間21(確定足)を付ける
h1=pd.merge_asof(h1.sort_values('end'),h4[['end','m21']].rename(columns={'m21':'h4m21'}).sort_values('end'),on='end',direction='backward')
h1['touch']=((h1.l-h1.h4m21).abs()<=0.05)
h1['touch6']=h1.touch.rolling(6,min_periods=1).max().astype(bool)
h1['up21']=h1.m21>h1.m21.shift()
h4['up21']=h4.m21>h4.m21.shift()
m=d.copy(); m['m9']=m.c.rolling(9).mean(); m['m21']=m.c.rolling(21).mean()
mid=m.c.rolling(20).mean(); sd=m.c.rolling(20).std(ddof=0); m['bu']=mid+sd; m['bl']=mid-sd
rng=(m.h.rolling(150).max()-m.l.rolling(150).min())
m['ang']=np.degrees(np.arctan(((m.m21-m.m21.shift(3))/rng*500)/(3*6)))
m['end']=m.index+pd.Timedelta('5min')
a=h4[['end','c','m9','m21','up21']].add_prefix('h4_').rename(columns={'h4_end':'end'})
b=h1[['end','c','m21','touch6','up21','h4m21']].add_prefix('h1_').rename(columns={'h1_end':'end'})
ix=m.index
m=pd.merge_asof(m.sort_values('end'),a.sort_values('end'),on='end',direction='backward')
m=pd.merge_asof(m,b.sort_values('end'),on='end',direction='backward'); m.index=ix
base=(m.h4_c>m.h4_m9)&(m.h1_c>m.h1_m21)&(m.c>m.bu)&(m.c>m.h.shift(LAG))
x921=(m.m9>m.m21)&(m.m9.shift()<=m.m21.shift()); x219=(m.m9<m.m21)&(m.m9.shift()>=m.m21.shift())
A=m.h1_touch6.astype(bool)&m.h1_up21.astype(bool)&m.h4_up21.astype(bool)
B=(m.ang>0)&(m.ang<=30)&((m.ang<=0).rolling(12).max()>0)
def run(entry,exitc,name):
    tr=[];pos=None
    for i in range(160,len(m)-1):
        if pos is None and entry.iloc[i]: pos=(ix[i],ix[i+1],m.o.iloc[i+1])
        elif pos and exitc.iloc[i]: tr.append(pos+(ix[i+1],m.o.iloc[i+1])); pos=None
    t=pd.DataFrame(tr,columns=['sig','in_t','in','out_t','out']); t['pips']=(t.out-t['in'])*100
    w=t.pips[t.pips>0].sum(); l=-t.pips[t.pips<0].sum()
    print(f"{name}: 件数{len(t)} 勝ち{(t.pips>0).sum()} 合計{t.pips.sum():.1f}p スプ1.0引き{(t.pips-1).sum():.1f}p PF{(w/l if l else float('nan')):.2f} 平均{t.pips.mean():.2f} 最大{t.pips.max():.1f} 最小{t.pips.min():.1f}")
    t.to_csv(S+f'/tai_trades_{name}.csv',index=False); return t
outC=(m.c<m.bu)
res={'A':run(base&x921&A,x219,'A'),'B':run(base&x921&B,x219,'B'),'C':run(base&x921,outC,'C')}
for k,t in res.items():
    if not len(t): continue
    s=t.sig.iloc[0]; r=m.loc[s]; lg=m.iloc[ix.get_loc(s)-LAG]
    print(f"[{k}の1件目] {s} O{r.o:.3f} H{r.h:.3f} L{r.l:.3f} C{r.c:.3f} {'陽' if r.c>=r.o else '陰'} 川+1σ={r.bu:.3f} 9={r.m9:.3f} 21={r.m21:.3f} 遅行21本前({ix[ix.get_loc(s)-LAG]:%H:%M})高値{lg.h:.3f} 5分21角度{r.ang:.1f}度 | H1 C{r.h1_c:.3f} 21={r.h1_m21:.3f} H4 21={r.h4_m21:.3f} | 入{t['in'].iloc[0]:.3f}@{t.in_t.iloc[0]:%m-%d %H:%M} 出{t.out.iloc[0]:.3f}@{t.out_t.iloc[0]:%m-%d %H:%M} {t.pips.iloc[0]:+.1f}p")

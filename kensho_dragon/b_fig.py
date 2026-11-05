import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
from sim3 import *
m5,h1=load(); lg=pd.read_pickle('blog.pkl'); h4=bigbars(h1,'4h'); c=h4.c
e9,e21,e200=ema(c,9),ema(c,21),ema(c,200); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
fig,axs=plt.subplots(2,1,figsize=(24,15),dpi=100)
for ax,y in zip(axs,(2017,2018)):
    w=h4.loc[str(y)]; x=np.arange(len(w)); pos={t:i for i,t in enumerate(w.index)}
    ax.fill_between(x,(mid-sd).loc[w.index],(mid+sd).loc[w.index],color='#9ecae1',alpha=.35,label='川(4時間 ボリ帯±1σ)')
    for i,(o,h,l,cl) in enumerate(w[['o','h','l','c']].values):
        col='#d62728' if cl>=o else '#1f77b4'; ax.vlines(i,l,h,color=col,lw=.7); ax.add_patch(plt.Rectangle((i-.35,min(o,cl)),.7,max(abs(cl-o),.005),color=col))
    for s,col,lab in ((e9,'orange','4時間 EMA9'),(e21,'green','4時間 EMA21'),(e200,'purple','4時間 EMA200')): ax.plot(x,s.loc[w.index],color=col,lw=1.2,label=lab)
    cc=lg[(lg.open>=f'{y}-01-01')&(lg.open<f'{y+1}-01-01')].groupby('camp').agg(pips=('pips','sum'),n=('n','max'),dir=('dir','first'),open=('open','min'),close=('close','max'),entry=('entry','first'),exit=('exit','last'))
    for cp,r in cc.iterrows():
        i0=pos.get(r.open.floor('4h')); i1=pos.get(r.close.floor('4h'))
        if i0 is None or i1 is None: continue
        col='#2ca02c' if r.pips>0 else '#d62728'
        ax.plot([i0,i1],[r.entry,r.exit],color=col,lw=2.2,alpha=.85)
        ax.plot(i0,r.entry,'^' if r.dir=='買' else 'v',color='black',ms=6)
        if abs(r.pips)>=400 or r.n>=11: ax.text(i1,r.exit+(0.35 if r.pips>0 else -0.45),f'{int(r.n)}発\n{r.pips:+.0f}',fontsize=8,ha='center',color=col,fontweight='bold')
    ticks=[i for i,t in enumerate(w.index) if t.day==1 and t.hour==0]; ax.set_xticks(ticks); ax.set_xticklabels([w.index[i].strftime('%Y/%m') for i in ticks])
    tot=lg[(lg.close>=f'{y}-01-01')&(lg.close<f'{y+1}-01-01')].pips.sum()
    ax.set_title(f'{y}年 ドル円 4時間足 B(4h200ドテン) — 戦{len(cc)}  合計{tot:+.0f}pips (▲買い ▼売り、緑線=勝った戦・赤線=負けた戦、入った値→降りた値、400p以上か11発以上に札)',fontsize=12)
    ax.legend(loc='upper right',fontsize=9); ax.grid(alpha=.2)
plt.tight_layout(); plt.savefig('b1718.png'); print('ok')

import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
from sim4 import *
m5,h1=load(); h4=bigbars(h1,'4h'); c=h4.c; E={p:ema(c,p) for p in (5,9,21,200)}; mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
JST=pd.Timedelta(hours=14); w=h4.loc['2016-12-28':'2017-02-01']; x=np.arange(len(w)); pos={t:i for i,t in enumerate(w.index)}
ticks=[]
for i,t in enumerate(w.index):
    if (t+JST).hour==6 and (not ticks or i-ticks[-1]>=4): ticks.append(i)
def panel(ax,logf,name):
    lg=pd.read_pickle(logf)
    for k,a in ((2,.10),(1,.22)): ax.fill_between(x,(mid-k*sd).loc[w.index],(mid+k*sd).loc[w.index],color='#9ecae1',alpha=a,lw=0,label=f'ボリ帯±{k}σ'+('(川)' if k==1 else ''))
    for i,(o,h,l,cl) in enumerate(w[['o','h','l','c']].values):
        col='#d62728' if cl>=o else '#1f77b4'; ax.vlines(i,l,h,color=col,lw=1); ax.add_patch(plt.Rectangle((i-.35,min(o,cl)),.7,max(abs(cl-o),.005),color=col))
    for p,col in ((5,'#ff7f0e'),(9,'#e6b800'),(21,'green'),(200,'purple')): ax.plot(x,E[p].loc[w.index],color=col,lw=2 if p==200 else 1.1,label=f'EMA{p}')
    cc=lg[(lg.close>='2017-01-01')&(lg.close<'2017-02-01')].groupby('camp').agg(p=('pips','sum'),n=('n','max'),dir=('dir','first'),k=('kind','first'),open=('open','min'),close=('close','max'),entry=('entry','first'),exit=('exit','last'),why=('why','last'))
    used=[]; rows=[]
    for no,(cp,r) in enumerate(cc.iterrows(),1):
        i0=pos.get(r.open.floor('4h')); i1=pos.get(r.close.floor('4h')); col='#2ca02c' if r.p>0 else '#d62728'
        if i0 is not None and i1 is not None: ax.plot([i0,i1],[r.entry,r.exit],color=col,lw=2.2,alpha=.75)
        if i1 is not None: ax.plot(i1,r.exit,'x',color=col,ms=9,mew=2.2)
        if i0 is not None:
            ax.plot(i0,r.entry,'^' if r.dir=='買' else 'v',color='black',ms=9,zorder=5)
            lvl=sum(1 for u in used if abs(u-i0)<4); used.append(i0)   # 近い番号は段をずらす
            dy=(0.45+0.32*lvl)*(-1 if r.dir=='買' else 1)
            ax.annotate(str(no),(i0,r.entry),xytext=(i0,r.entry+dy),ha='center',va='center',fontsize=12,fontweight='bold',
                        bbox=dict(boxstyle='circle,pad=0.2',fc='white',ec='black',lw=.8),arrowprops=dict(arrowstyle='-',color='gray',lw=.7),zorder=6)
        rows.append(f"{no}:{r.dir}{'(ド)' if 'ドテン' in r.k else ''} {int(r.n)}発 {r.p:+.0f}")
    ax.set_xticks(ticks); ax.set_xticklabels([(w.index[i]+JST).strftime('%m/%d') for i in ticks],fontsize=10)
    ax.set_xlim(-1,len(w)); ax.set_ylim(111.6,119.2); ax.grid(alpha=.25)
    ax.set_title(f'{name}  2017年1月 {cc.p.sum():+.0f}pips・{len(cc)}戦',fontsize=14,loc='left')
    ax.text(1.002,1,'\n'.join(rows),transform=ax.transAxes,va='top',fontsize=10,family='WenQuanYi Zen Hei')
    return cc
fig,axs=plt.subplots(2,1,figsize=(28,17),dpi=100)
panel(axs[0],'blog.pkl','B(4h終値が200を越えたらすぐドテン・入りは5分だけ)')
panel(axs[1],'b2log.pkl','B2(4h終値が200の同じ側に3本続いたらドテン+入り・足しは4hの9と21も同じ向きの時だけ)')
axs[0].legend(loc='upper center',fontsize=10,ncol=6)
fig.suptitle('ドル円 4時間足 2017年1月  ▲買い ▼売り=戦の1発目(丸数字=右の一覧)、×=全部降りた所、線=入った値→降りた値(赤=負け 緑=勝ち)  日付は日本時間',fontsize=14)
plt.tight_layout(rect=(0,0,0.9,0.97)); plt.savefig('jan2017_4h_B_B2.png'); print('ok')

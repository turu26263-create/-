import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
from sim3 import *
m5,h1=load(); lg=pd.read_pickle('log_4h1h_20.pkl'); tb=pd.read_csv('aug2017_table.csv')
w=h1.loc['2017-07-31':'2017-08-31'].copy(); c=h1.c
e9,e21=ema(c,9).loc[w.index],ema(c,21).loc[w.index]; mid=c.rolling(20).mean().loc[w.index]; sd=c.rolling(20).std(ddof=0).loc[w.index]
x=np.arange(len(w)); pos={t:i for i,t in enumerate(w.index)}
def xi(t): return pos[t.floor('1h')] if t.floor('1h') in pos else None
fig,ax=plt.subplots(figsize=(22,9),dpi=110)
ax.fill_between(x,mid-sd,mid+sd,color='#9ecae1',alpha=.35,label='川(1時間 ボリ帯±1σ)')
for i,(o,h,l,cl) in enumerate(w[['o','h','l','c']].values):
    col='#d62728' if cl>=o else '#1f77b4'
    ax.vlines(i,l,h,color=col,lw=.8); ax.add_patch(plt.Rectangle((i-.35,min(o,cl)),.7,max(abs(cl-o),.002),color=col))
ax.plot(x,e9,color='orange',lw=1.3,label='1時間 EMA9'); ax.plot(x,e21,color='green',lw=1.3,label='1時間 EMA21')
a=lg[(lg.open>='2017-08-01')&(lg.open<'2017-09-01')].reset_index(drop=True)
for k,t in a.iterrows():
    i=xi(pd.Timestamp(t.open))
    if i is None: continue
    ax.annotate(str(k+1),(i,t.entry),xytext=(i,t.entry+0.12+0.05*(k%3)),ha='center',fontsize=9,color='#7b2cbf',arrowprops=dict(arrowstyle='->',color='#7b2cbf',lw=.8))
camps=a.groupby('camp').agg(close=('close','max'),exit=('exit','first'),why=('why','first'),pips=('pips','sum'),n=('n','max'))
for cp,r in camps.iterrows():
    i=xi(pd.Timestamp(r.close))
    if i is None: continue
    ax.plot(i,r.exit,'kx',ms=10,mew=2)
    ax.text(i,r.exit-0.18,f'戦{cp} {r.why}\n{int(r.n)}発 {r.pips:+.0f}p',ha='center',fontsize=9,bbox=dict(fc='white',ec='gray',alpha=.85))
ticks=[i for i,t in enumerate(w.index) if t.hour==0]; ax.set_xticks(ticks); ax.set_xticklabels([w.index[i].strftime('%m/%d') for i in ticks],fontsize=8)
ax.set_title('ドル円 1時間足 2017年8月 — 4時間5>9>21>200 + 1時間5>9>21 の売り(番号=入った玉、×=全部降りた所) 時刻は HistData(EST)',fontsize=12)
ax.legend(loc='upper right'); ax.grid(alpha=.2); plt.tight_layout(); plt.savefig('aug2017.png')
print(camps)

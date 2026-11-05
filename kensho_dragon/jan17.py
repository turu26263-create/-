import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
from sim4 import *
m5,h1=load(); lg=pd.read_pickle('blog.pkl'); h4=bigbars(h1,'4h'); c=h4.c
E={p:ema(c,p) for p in (5,9,21,200)}; mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
JST=pd.Timedelta(hours=14)
w=h4.loc['2016-12-28':'2017-02-01']; x=np.arange(len(w)); pos={t:i for i,t in enumerate(w.index)}
fig,ax=plt.subplots(figsize=(26,13),dpi=100)
for k,a in ((2,.12),(1,.25)): ax.fill_between(x,(mid-k*sd).loc[w.index],(mid+k*sd).loc[w.index],color='#9ecae1',alpha=a,label=f'ボリ帯±{k}σ' + ('(川)' if k==1 else ''))
for i,(o,h,l,cl) in enumerate(w[['o','h','l','c']].values):
    col='#d62728' if cl>=o else '#1f77b4'; ax.vlines(i,l,h,color=col,lw=1); ax.add_patch(plt.Rectangle((i-.35,min(o,cl)),.7,max(abs(cl-o),.005),color=col))
for p,col in ((5,'#ff7f0e'),(9,'#e6b800'),(21,'green'),(200,'purple')): ax.plot(x,E[p].loc[w.index],color=col,lw=1.6 if p==200 else 1.1,label=f'EMA{p}')
cc=lg[(lg.close>='2017-01-01')&(lg.close<'2017-02-01')].groupby('camp').agg(p=('pips','sum'),n=('n','max'),dir=('dir','first'),k=('kind','first'),open=('open','min'),close=('close','max'),entry=('entry','first'),exit=('exit','last'),why=('why','last'))
rows=[]
for no,(cp,r) in enumerate(cc.iterrows(),1):
    i0=pos.get(r.open.floor('4h')); i1=pos.get(r.close.floor('4h'))
    col='#2ca02c' if r.p>0 else '#d62728'
    if i0 is not None:
        ax.plot(i0,r.entry,'^' if r.dir=='買' else 'v',color='black',ms=9)
        ax.annotate(str(no),(i0,r.entry),xytext=(i0,r.entry+(-0.35 if r.dir=='買' else 0.35)),ha='center',fontsize=12,fontweight='bold',color='black',arrowprops=dict(arrowstyle='-',color='gray',lw=.6))
    if i0 is not None and i1 is not None: ax.plot([i0,i1],[r.entry,r.exit],color=col,lw=2.4,alpha=.8)
    if i1 is not None: ax.plot(i1,r.exit,'x',color=col,ms=10,mew=2.5)
    rows.append(dict(番号=no,向き=r.dir,入り=('ドテン' if 'ドテン' in r.k else '一番槍'),入った日時_日本=(r.open+JST).strftime('%m/%d %H:%M'),入値=round(r.entry,3),
                     降りた日時_日本=(r.close+JST).strftime('%m/%d %H:%M'),降値=round(r.exit,3),降り方=r.why,発数=int(r.n),pips=round(r.p)))
ticks=[]
for i,t in enumerate(w.index):
    if (t+JST).hour==6 and (not ticks or i-ticks[-1]>=4): ticks.append(i)
ax.set_xticks(ticks); ax.set_xticklabels([(w.index[i]+JST).strftime('%m/%d') for i in ticks],fontsize=9,rotation=0)
ax.set_xlim(-1,len(w)); ax.grid(alpha=.25)
tot=cc.p.sum()
ax.set_title(f'ドル円 4時間足 2017年1月(B 4h200ドテン の一番悪い月 {tot:+.0f}pips・{len(cc)}戦)  ▲買い ▼売り=戦の1発目、×=全部降りた所、番号=下の表  日付は日本時間',fontsize=14)
ax.legend(loc='upper right',fontsize=10,ncol=2); plt.tight_layout(); plt.savefig('jan2017_4h.png')
t=pd.DataFrame(rows); t.to_csv('jan2017_4h_ikusa.csv',index=False,encoding='utf-8-sig'); print(t.to_string(index=False)); print('合計',round(tot))
o=w.copy(); o.index=o.index+JST; o['EMA5']=E[5].loc[w.index].values; o['EMA9']=E[9].loc[w.index].values; o['EMA21']=E[21].loc[w.index].values; o['EMA200']=E[200].loc[w.index].values
o.round(3).to_csv('jan2017_4h_ashi.csv',encoding='utf-8-sig',index_label='日時_日本')

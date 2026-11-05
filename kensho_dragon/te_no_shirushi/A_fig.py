import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
from sim4 import *
m5,h1=load(); h4=bigbars(h1,'4h'); c=h4.c; J=pd.Timedelta(hours=14)
E={p:ema(c,p) for p in (5,9,21,200)}; mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
w=h4.loc['2017-01-03 12:00':'2017-01-09 20:00']; x=np.arange(len(w)); pos={t:i for i,t in enumerate(w.index)}
lg=pd.read_pickle('blog.pkl'); a=lg[(lg.open>='2017-01-03 14:00')&(lg.open<'2017-01-08')]
fig,ax=plt.subplots(figsize=(22,11),dpi=100)
for k,al in ((2,.10),(1,.25)): ax.fill_between(x,(mid-k*sd).loc[w.index],(mid+k*sd).loc[w.index],color='#9ecae1',alpha=al,lw=0,label=f'ボリ帯±{k}σ'+('(川)' if k==1 else '(魚道)'))
for i,(o,h,l,cl) in enumerate(w[['o','h','l','c']].values):
    col='#d62728' if cl>=o else '#1f77b4'; ax.vlines(i,l,h,color=col,lw=1.5); ax.add_patch(plt.Rectangle((i-.35,min(o,cl)),.7,max(abs(cl-o),.004),color=col))
for p,col in ((9,'#e6b800'),(21,'green'),(200,'purple')): ax.plot(x,E[p].loc[w.index],color=col,lw=2,label=f'EMA{p}')
# 札(4時間足の番号)
for i,t in enumerate(w.index): ax.text(i,w.l.iloc[i]-0.08,f'{i+1}',ha='center',va='top',fontsize=9,color='dimgray')
for _,k in a.iterrows():
    i=pos.get(k.open.floor('4h'))
    if i is None: continue
    ax.annotate('',xy=(i,k.entry),xytext=(i,k.entry-0.55),arrowprops=dict(arrowstyle='simple,head_length=1.4,head_width=1.4,tail_width=0.55',fc='#0050ff',ec='black'))
    ax.text(i,k.entry-0.65,f"戦{k.camp}-{k.n}\n{k.entry:.2f}",ha='center',va='top',fontsize=10,color='#0050ff',fontweight='bold')
for cp in a.camp.unique():
    g=lg[lg.camp==cp]; i=pos.get(g.close.max().floor('4h'))
    if i is not None: ax.plot(i,g.exit.iloc[0],'X',color='#d62728',ms=20,mec='black'); ax.text(i+.3,g.exit.iloc[0]-0.12,f"戦{cp} {len(g)}発 網 {g.pips.sum():+.0f}p",fontsize=11,color='#d62728',fontweight='bold')
def note(i,y,s,dx=0.6,dy=0.55): ax.annotate(s,(i,y),xytext=(i+dx,y+dy),fontsize=11,bbox=dict(fc='#fff6d5',ec='#b8860b'),arrowprops=dict(arrowstyle='->',color='#b8860b',lw=1.5))
ti={(t+J).strftime('%m/%d %H'):i for i,t in enumerate(w.index)}
note(ti['01/05 06'],116.36,dx=-4.5,dy=1.9,s='①01/05 06時 大陰線が川の下へ渡り切って確定\n 9が21を下抜け・遅行も下 = 魚は下の川へ')
note(ti['01/05 10'],116.39,dx=0.8,dy=-1.75,s='②ここで B は買い(200の上だから)\n 川の下の外・9<21・遅行下 → ×')
note(ti['01/05 22'],115.47,dx=1.5,dy=-0.9,s='③下の川を泳ぐ(115.07まで)\n B は売れない(200の上)')
note(ti['01/06 22'],116.86,'④戻りで足し3発\n 9<21のまま → ×')
ticks=[]
for i,t in enumerate(w.index):
    if (t+J).hour==6 and (not ticks or i-ticks[-1]>=4): ticks.append(i)
ax.set_xticks(ticks); ax.set_xticklabels([(w.index[i]+J).strftime('%m/%d 6時') for i in ticks]); ax.grid(alpha=.25)
ax.set_title('A(たくちんの丸) ドル円4時間足 2017/01/04〜01/09  青い矢印=B の買い(戦と何発目) ×=網  灰色の数字=4時間足の番号  日本時間',fontsize=14)
ax.legend(loc='upper right',fontsize=11); ax.set_ylim(113.4,118.9); plt.tight_layout(); plt.savefig('A_2017_01_05.png'); print('ok')

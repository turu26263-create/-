# 11-11 たくちん「出して うりかいしたとこ」:上から921・5分で合わす(3本目=4時間の帯が開いている時だけ)の2017年の売り買いをチャートに
import sys,io,contextlib,runpy,warnings; warnings.filterwarnings('ignore')
sys.argv=[sys.argv[0],sys.argv[1]]
with contextlib.redirect_stdout(io.StringIO()): g=runpy.run_path('/home/user/-/engine/nyu/kenkyu/ue_kara_5fun.py')
t=g['t']; mk=g['mk']; pd=g['pd']; np=g['np']
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
t=t[(pd.to_datetime(t.ent)>='2017-01-01')&(pd.to_datetime(t.ent)<'2018-01-01')].copy()
g2=t.groupby(['d','ext']).agg(玉=('pips','size'),合計=('pips','sum'),最初=('ent','min'),e=('e','first'),x=('x','first')).reset_index().sort_values('最初')
print(g2.to_string(index=False))
def candles(ax,X,w):
    up=X.c>=X.o; ax.vlines(X.index,X.l,X.h,color='#555',lw=0.6)
    ax.bar(X.index[up],(X.c-X.o)[up],bottom=X.o[up],width=w,color='#e8f0ff',edgecolor='#1f5fe0',lw=0.6)
    ax.bar(X.index[~up],(X.o-X.c)[~up],bottom=X.c[~up],width=w,color='#1f2a44',edgecolor='#1f2a44',lw=0.6)
def lines(ax,X):
    ax.plot(X.index,X.e9,color='#1f77b4',lw=1.5,label='9(青)'); ax.plot(X.index,X.e21,color='#d62728',lw=1.5,label='21(赤)')
    for k in (1,2): ax.plot(X.index,X.md+k*X.sd,color='#888',lw=0.8,ls='--' if k==1 else '-'); ax.plot(X.index,X.md-k*X.sd,color='#888',lw=0.8,ls='--' if k==1 else '-')
D=mk.feat('1D')['2016-12-01':'2018-01-15']
fig,ax=plt.subplots(figsize=(20,9)); candles(ax,D,0.7); lines(ax,D)
for r in t.itertuples():
    ax.scatter(r.ent,r.e,marker='^' if r.d>0 else 'v',color='green' if r.d>0 else 'magenta',s=45,zorder=5)
for r in g2.itertuples():
    col='#1a9e3a' if r.合計>0 else '#d62728'
    ax.scatter(r.ext,r.x,marker='X',color=col,s=110,zorder=6)
    ax.annotate(f"{'買' if r.d>0 else '売'}{r.玉}発 {r.合計:+,.0f}p",xy=(r.最初,r.e),xytext=(0,18 if r.d>0 else -24),textcoords='offset points',fontsize=9,color=col,ha='left',fontweight='bold')
ax.set_title('2017年 日足:緑▲=買い・桃▼=売り(5分の921で入った所)/✕=日足21割れで降りた所(緑=勝ち・赤=負け)',fontsize=13)
ax.legend(loc='upper right'); ax.grid(alpha=0.25)
fig.tight_layout(); out='/home/user/-/engine/kekka_tai/nyu/chart_saomoto/2017年_売り買いした所_日足.png'; fig.savefig(out,dpi=100); print(out)
# 負けの大きい4つの流れを4時間足で
worst=g2.nsmallest(4,'合計'); F=mk.feat('4h')
fig,axs=plt.subplots(2,2,figsize=(20,11))
for a,r in zip(axs.flat,worst.itertuples()):
    s=pd.Timestamp(r.最初)-pd.Timedelta(days=12); e=pd.Timestamp(r.ext)+pd.Timedelta(days=4)
    X=F[s:e]; candles(a,X,0.12); lines(a,X)
    q=t[(t.d==r.d)&(t.ext==r.ext)]
    for z in q.itertuples(): a.scatter(z.ent,z.e,marker='^' if r.d>0 else 'v',color='green' if r.d>0 else 'magenta',s=70,zorder=5)
    a.scatter(r.ext,r.x,marker='X',color='#d62728',s=120,zorder=6)
    a.set_title(f"4時間足:{'買い' if r.d>0 else '売り'} {pd.Timestamp(r.最初):%m/%d} から{r.玉}発 → {pd.Timestamp(r.ext):%m/%d} 日足21割れで降り {r.合計:+,.0f}p",fontsize=12); a.grid(alpha=0.25)
fig.suptitle('2017年 負けの大きい4つを4時間足で(▲▼=入った所・✕=降りた所)',fontsize=14)
fig.tight_layout(); out='/home/user/-/engine/kekka_tai/nyu/chart_saomoto/2017年_負け4つ_4時間足.png'; fig.savefig(out,dpi=100); print(out)

# 11-11 たくちん「意味がわからん チャートにだして」:取れた竿元 2022/02/10 と負けた竿元 2022/07/14 を、週足と日足で並べて描く
import sys,io,contextlib,runpy,warnings; warnings.filterwarnings('ignore')
sys.argv=[sys.argv[0],sys.argv[1]]
with contextlib.redirect_stdout(io.StringIO()): g=runpy.run_path('/home/user/-/engine/nyu/kenkyu/saomoto_oshime.py')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
pd=g['pd']; np=g['np']; raw=g['raw']; D=g['D']; run=g['run']
t=pd.concat([run(1,'oshime'),run(-1,'oshime')],ignore_index=True)
AGG={'o':'first','h':'max','l':'min','c':'last'}
W=raw.resample('7D',origin=pd.Timestamp('2016-03-07')).agg(AGG).dropna()
for X in (W,):
    X['e9']=X.c.ewm(span=9,adjust=False).mean(); X['e21']=X.c.ewm(span=21,adjust=False).mean(); X['md']=X.c.rolling(20).mean(); X['sd']=X.c.rolling(20).std(ddof=0)
def candles(ax,X,w):
    up=X.c>=X.o
    ax.vlines(X.index,X.l,X.h,color='#555',lw=0.6)
    ax.bar(X.index[up],(X.c-X.o)[up],bottom=X.o[up],width=w,color='#e8f0ff',edgecolor='#1f5fe0',lw=0.6)
    ax.bar(X.index[~up],(X.o-X.c)[~up],bottom=X.c[~up],width=w,color='#1f2a44',edgecolor='#1f2a44',lw=0.6)
def lines(ax,X):
    ax.plot(X.index,X.e9,color='#1f77b4',lw=1.6,label='9(青)'); ax.plot(X.index,X.e21,color='#d62728',lw=1.6,label='21(赤)')
    for k,a in [(1,0.5),(2,0.8)]:
        ax.plot(X.index,X.md+k*X.sd,color='#888',lw=0.8,ls='--' if k==1 else '-',alpha=a); ax.plot(X.index,X.md-k*X.sd,color='#888',lw=0.8,ls='--' if k==1 else '-',alpha=a)
def panel(axw,axd,sao,title):
    s=pd.Timestamp(sao); q=t[(t.sao==s)]
    Wx=W[s-pd.Timedelta(weeks=60):s+pd.Timedelta(weeks=20)]; candles(axw,Wx,4.5); lines(axw,Wx)
    axw.axvline(s,color='orange',lw=2); axw.set_title(f'{title} ― 週足(帯は週の±1σ点線・±2σ実線)',fontsize=11)
    axw.annotate('ここで日足の竿元',xy=(s,Wx.h.max()),xytext=(s,Wx.h.max()),color='orange',fontsize=10,ha='center',va='bottom')
    Dx=D[s-pd.Timedelta(days=90):max(pd.to_datetime(q.ext).max(),s)+pd.Timedelta(days=15)]; candles(axd,Dx,0.7); lines(axd,Dx)
    for r in q.itertuples(): axd.scatter(r.ent,r.e,marker='^',color='green',s=60,zorder=5)
    x=q.iloc[0]; axd.scatter(x.ext,x.x,marker='v',color='red',s=90,zorder=5)
    axd.axvline(s,color='orange',lw=2)
    axd.set_title(f'日足:▲入った5発 / ▼日足219で降り → 5発で {q.pips.sum():+,.0f}p',fontsize=11)
    for ax in (axw,axd): ax.grid(alpha=0.25); ax.tick_params(labelsize=8)
    axw.legend(fontsize=8,loc='upper left')
fig,ax=plt.subplots(2,2,figsize=(16,10))
panel(ax[0][0],ax[1][0],'2022-02-10','取れた竿元 2022/02/10 買い')
panel(ax[0][1],ax[1][1],'2022-07-14','負けた竿元 2022/07/14 買い')
fig.suptitle('日足の竿元(しぼんだ後のバンドブレイク):取れた所と負けた所',fontsize=14)
fig.tight_layout(); out='/home/user/-/engine/kekka_tai/nyu/chart_saomoto/竿元_2022年2月と7月.png'; fig.savefig(out,dpi=110); print(out)

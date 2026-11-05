import os, glob
from sim4 import *
from logger import run_log
m5,h1=load()
picks=[('A 1h200ドテン+5分合図+網4hATR×5(全期間の最大・台地)','1h',5),('B 4h200ドテン+5分合図+網4hATR×3(3期間とも+)','4h',3)]
for tag,tf,k in picks:
    m=prep4(m5,h1,tf,LOC='m5',NET=('4h',k)); r=sim3(m,0.3,MAXPOS=20); r1=sim3(m,1.0,MAXPOS=20)
    lg=run_log(m,MAXPOS=20); lg.to_pickle(f'wlog_{tf}.pkl')
    cc=lg.groupby('camp').agg(p=('pips','sum'),n=('n','max'),why=('why','last'))
    print(tag); print(f"  spr0.3 {r['pips']:+d} PF{r['PF']} DD{r['DD']} 戦{r['ikusa']} 勝率{r['win']}% / spr1.0 {r1['pips']:+d}  素Python合計 {lg.pips.sum():+.0f}")
    print('  年ごと',r['year']); print('  買',r['buy'],'売',r['sell'],' 一番槍だけ',round(lg[lg.n==1].pips.sum()),' 足し',round(lg[lg.n>1].pips.sum()))
    print('  上位10戦',round(cc.p.nlargest(10).sum()),' 終わり方',cc.groupby('why').p.agg(['size','sum']).round().to_dict())
# 照らし: 1h と 4h の「200より上/下」を別の道で計算(1分→直に足を組み、EMA手回し)して全5分足で比べる
dfs=[pd.read_csv(f,header=None,names=['d','t','o','h','l','c','v']) for f in sorted(glob.glob(os.environ.get('M1DIR','../dl/m1')+'/*.csv'))]
d=pd.concat(dfs); d.index=pd.to_datetime(d.d+' '+d.t,format='%Y.%m.%d %H:%M'); d=d[~d.index.duplicated()].sort_index()
for tf,hrs in (('1h',1),('4h',4)):
    m=prep4(m5,h1,tf,LOC='m5',NET=('4h',3)); c=d.c.resample(tf).last().dropna(); x=c.values
    a=2/201; e=np.empty(len(x)); e[0]=x[0]
    for i in range(1,len(x)): e[i]=a*x[i]+(1-a)*e[i-1]
    s=np.where(x>e,1,-1); s[:201]=0
    closed=(c.index+pd.Timedelta(hours=hrs)).values; p=np.searchsorted(closed,m.index.values,side='right')-1
    ref=np.where(p>=0,s[np.clip(p,0,None)],0)
    print(f'照らし {tf} 200の上下: 5分足{len(m)}本で食い違い',int((ref!=m.trend.values).sum()))

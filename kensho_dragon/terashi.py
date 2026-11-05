# 照らし: sim2 の「4時間足 200/21/9/5 並び」を、別の道で計算し直して5分足の全部の足で比べる
import os, glob, numpy as np, pandas as pd
from sim2 import *
m5,h1=load(); m=prep2(m5,h1,'4h')
# 別の道: 1分足から直接4時間足を組み、EMAは手で回す
dfs=[pd.read_csv(f,header=None,names=['d','t','o','h','l','c','v']) for f in sorted(glob.glob(os.environ.get('M1DIR','../dl/m1')+'/*.csv'))]
d=pd.concat(dfs); d.index=pd.to_datetime(d.d+' '+d.t,format='%Y.%m.%d %H:%M'); d=d[~d.index.duplicated()].sort_index()
c4=d.c.resample('4h').last().dropna()
def ema_loop(x,p):
    a=2/(p+1); out=np.empty(len(x)); out[0]=x[0]
    for i in range(1,len(x)): out[i]=a*x[i]+(1-a)*out[i-1]
    return out
x=c4.values; e={p:ema_loop(x,p) for p in (5,9,21,200)}
sig=np.zeros(len(x),int)
for i in range(200,len(x)):
    if e[5][i]>e[9][i]>e[21][i]>e[200][i]: sig[i]=1
    elif e[5][i]<e[9][i]<e[21][i]<e[200][i]: sig[i]=-1
closed=c4.index+pd.Timedelta(hours=4)          # 足が閉じた時刻
pos=np.searchsorted(closed.values, m.index.values, side='right')-1   # t 以前に閉じた最後の4時間足
ref=np.where(pos>=0, sig[np.clip(pos,0,None)], 0)
got=m.trend.values.astype(int)
diff=(ref!=got)
print('5分足の数',len(m),' 並びが食い違った足',int(diff.sum()))
if diff.any(): print(m.index[diff][:10])
# 先読みしていないか: 4時間足が閉じる直前の5分足は、まだ前の足の並び
k=np.where(np.diff(got)!=0)[0][:5]+1
for j in k: print('並びが変わった5分足', m.index[j], '→ その4時間足が閉じた時刻', closed[pos[j]], ' 値', got[j-1],'→',got[j])

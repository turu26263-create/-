# 鯛の刺身のぶん回し(11-06 たくちん「ac ぶん回す ご」)。選ぶ年=2022〜2024、確かめる年=2015〜2021・2025(1〜4月)。spr0.3p
# 回す物:向き(買い/売り)×降りの足(5分/15分/1時間/4時間の9割れ)×竿先の幅(2σ/2.5σ)。遅行は21本前で固定
import sys; sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai2 import *
m1=load(sys.argv[1]); base=prep(m1); rows=[]
for tf in ('5min','15min','1h','4h'):
    x=add_exit(base,m1,tf)
    for d in (1,-1):
        for sao in (2.0,2.5):
            t=run(x,d,signals(x,d,sao)); y=pd.to_datetime(t.ent).dt.year
            r=dict(向き='買い' if d>0 else '売り',降り=tf+'の9割れ',竿先=f'{sao}σ')
            for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
                s=stat(t[msk]); r[k+'_p']=s['sum']; r[k+'_pf']=s['pf']
            s=stat(t); r['戦']=s['n']; r['DD']=s['dd']; rows.append(r)
            t.to_csv(f"{sys.argv[2]}/{'buy' if d>0 else 'sell'}_{tf}_{sao}.csv",index=False)
df=pd.DataFrame(rows).sort_values(['向き','選22-24_p'],ascending=[True,False])
print(df.to_string(index=False))

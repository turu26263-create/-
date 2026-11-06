# 縄8(4時間の竿先で入らない)の照らし+売りも(11-06 たくちん「うりもして 1と」)。形は完成形:1hの9割れで降り・竿先2σ・spr0.3。選ぶ年 2022-24/確かめる年 2015-21・2025
import sys; sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai2 import *
m1=load(sys.argv[1]); x=add_exit(prep(m1),m1,'1h'); out=sys.argv[2]; rows=[]; keep={}
for n8 in (False,True):
    ts=[]
    for d in (1,-1):
        t=run(x,d,signals(x,d,2.0,n8)); t['向き']='買い' if d>0 else '売り'; ts.append(t)
        t.to_csv(f"{out}/{'buy' if d>0 else 'sell'}_1h_2.0_縄8{'あり' if n8 else 'なし'}.csv",index=False)
    ts.append(pd.concat(ts[:2]).sort_values('ent').assign(向き='買い+売り'))
    for t in ts:
        y=pd.to_datetime(t.ent).dt.year; r=dict(縄8='あり' if n8 else 'なし',向き=t.向き.iloc[0])
        for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
            s_=stat(t[msk]); r[k+'_p']=s_['sum']; r[k+'_pf']=s_['pf']
        s_=stat(t); r['戦']=s_['n']; r['DD']=s_['dd']; rows.append(r)
        if t.向き.iloc[0]=='買い+売り': keep[n8]=t
print(pd.DataFrame(rows).to_string(index=False))
for n8 in (False,True):
    t=keep[n8]; t['年']=pd.to_datetime(t.ent).dt.year
    print(f"\n年ごと 買い+売り 縄8{'あり' if n8 else 'なし'}"); print(t.groupby(['年','向き']).pips.sum().unstack().round(1).assign(計=lambda g:g.sum(axis=1)).to_string())

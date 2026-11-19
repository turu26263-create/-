# 日足の鯛の刺身のぶん回し(11-06 たくちん「許可なしぶん回しエンジン 同じように日足やって」)
# 形:日足の9上(縄1)・4時間の21上(縄2)・1時間で入る(縄3〜5)・縄4改と縄8は日足。spr0.3。選ぶ年 2022-24/確かめる年 2015-21・2025
# 回す物:向き×降りの足(1h/4h/日足の9割れ)×竿先(2σ/2.5σ)×縄8(なし/あり)=24通り
import sys; sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
m1=load(sys.argv[1]); out=sys.argv[2]; base=prep(m1,'1D','4h','1h'); rows=[]
for tf in ('1h','4h','1D'):
    x=add_exit(base,m1,tf)
    for d in (1,-1):
        for sao in (2.0,2.5):
            for n8 in (False,True):
                t=run(x,d,signals(x,d,sao,n8)); y=pd.to_datetime(t.ent).dt.year
                r=dict(向き='買い' if d>0 else '売り',降り=tf+'の9割れ',竿先=f'{sao}σ',縄8='あり' if n8 else 'なし')
                for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
                    s=stat(t[msk]); r[k+'_p']=s['sum']; r[k+'_pf']=s['pf']
                s=stat(t); r['戦']=s['n']; r['DD']=s['dd']; rows.append(r)
                t.to_csv(f"{out}/D_{'buy' if d>0 else 'sell'}_{tf}_{sao}_縄8{r['縄8']}.csv",index=False)
df=pd.DataFrame(rows).sort_values(['向き','選22-24_p'],ascending=[True,False]); print(df.to_string(index=False))

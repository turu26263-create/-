# クジラ3 のぶん回し:網(前の日/4h9/4h21)×巡航の見方(4h21角度30度が直近120本の1hにあった/日足9上4本目からだけ)×2発目から4h9割れ。合図=1hの9戻し。spr0.3
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_kujira2 import *
from engine_kujira import dd_open
m1=load(sys.argv[1]); out=sys.argv[2]; x=prep2(m1); rows=[]
for d in (1,-1):
    g=(x.F_e9-x.F_e21)*d; a=x.F_ang*d; sashi=((g<=0.05)&(g>=-0.10)).rolling(8).max()>0
    if d>0: zone=(x.D_c>x.D_e9)&(x.D_ku>=4); t=(x.c>x.e9)&(x.c.shift()<=x.e9.shift()); ns=x.c<=x.md+2*x.sd
    else: zone=(x.D_c<x.D_e9)&(x.D_kd>=4); t=(x.c<x.e9)&(x.c.shift()>=x.e9.shift()); ns=x.c>=x.md-2*x.sd
    for cname,cr in (('4h21角度',(a>=30).rolling(120).max()>0),('日足9上4本目',pd.Series(True,index=x.index))):
        ent=zone&sashi&cr&t&ns
        for net in ('day','f9','f21'):
            for tai4h in (False,True):
                tr=run2(x,d,ent,5,tai4h,net=net); y=pd.to_datetime(tr.ent).dt.year
                r=dict(向き='買い' if d>0 else '売り',巡航=cname,網={'day':'前の日','f9':'4h9','f21':'4h21'}[net],鯛の降り='4h9割れ' if tai4h else 'なし')
                for k,msk in (('選22-24',y.between(2022,2024)),('確15-21',y.between(2015,2021)),('確25',y==2025),('全',y>0)):
                    s_=stat(tr[msk]); r[k+'_p']=s_['sum']; r[k+'_pf']=s_['pf']
                r['玉']=len(tr); r['DD']=dd_open(tr); r['網%']=round(100*(tr.why=='網').mean(),1); rows.append(r)
                tr.to_csv(f"{out}/K3b_{'buy' if d>0 else 'sell'}_{'ang' if cname.startswith('4h') else 'day'}_{net}_{'tai' if tai4h else 'nashi'}.csv",index=False)
df=pd.DataFrame(rows); print(df.sort_values(['向き','確15-21_p'],ascending=[True,False]).to_string(index=False))

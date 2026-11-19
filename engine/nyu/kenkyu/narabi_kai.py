import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def blend(nb):
    KB={**K,'narabi':nb}
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**KB); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**KB,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d
    return pd.concat([b,s,dt,tb,ob,os_],ignore_index=True),base
print('決め方(先に決めた):確かめる年の合計が上がり、落ち込み率が上がらなければ残す')
for nm,nb in [('今',False),('買いと鯛は、日足が921の並び(青が赤の上)の時だけ入る',True)]:
    t,base=blend(nb); y=pd.to_datetime(t.ent).dt.year; T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); ye=pd.to_datetime(t.ext).dt.year
    f=lambda k: f"{int((t.kind==k).sum())}玉 {t.pips[t.kind==k].sum():+,.0f}p"
    print(f"  {nm}: 買い {f('買い')} / 鯛 {f('鯛')} / 全部 {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% | 2019年 {t.pips[ye==2019].sum():+,.0f} 2020年 {t.pips[ye==2020].sum():+,.0f}")

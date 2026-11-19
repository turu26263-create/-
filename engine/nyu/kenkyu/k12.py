import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def blend(bk={},sk={}):
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K,**bk); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K,**sk); dt,_=run_doten(srv,1,xtf='4h',**K)
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d
    return pd.concat([b,s,dt,tb,ob,os_],ignore_index=True),base
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum())); st=stat(t)
    return f"{st['n']}玉 {st['sum']:+,.0f}p 勝率{st['win']/max(st['n'],1)*100:.1f}% PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
kk=lambda t: t.pips[pd.to_datetime(t.ent).dt.year.between(2016,2021)|(pd.to_datetime(t.ent).dt.year>=2025)].sum()
def line(nm,t,base,kind):
    T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    print(f"  {nm}: {kind}だけ {sp(t[t.kind==kind])}\n     全部 {sp(t)}\n     0.01ロット {st['最後の資金']:,}円 落ち込み率 {st['落ち込み率']}% 確かめる年 {kk(t):+,.0f}")
    return kk(t),st['落ち込み率']
print('決め方(先に決めた):全部で、確かめる年の合計が上がり、落ち込み率が上がらなければ残す\n')
A,base=blend()
for nm,kind,bk,sk,d in [('1 売りの降り:4時間で新しい921が出たら降りる(日足921・利確・TSはそのまま)','売り',{},dict(xcross='4h'),-1),
                        ('2 大山の取り切り:買いの1発目は利確せず日足219まで持つ(足しは利確)','買い',dict(tpcore=False),{},1)]:
    print('■',nm)
    kw={**K,**(sk if d<0 else bk)}
    ok,L=bugbug(lambda mk,dd: run_tai(mk,'1D','4h','1h',dd,('1D','219'),**kw)[0], raw,'server',5,0.003); print('  修正機:', '全部○' if ok else [l for l in L if l.startswith('×')])
    B,_=blend(bk,sk); a=line('今',A,base,kind); b=line('新',B,base,kind)
    print(f"  → {'残す' if (b[0]>a[0] and b[1]<=a[1]) else '×'}(確かめる年 {a[0]:+,.0f} → {b[0]:+,.0f}・落ち込み率 {a[1]}% → {b[1]}%)")
    x=A[A.kind==kind].merge(B[B.kind==kind],on='ent',how='outer',suffixes=('_今','_新')); x['差']=x.pips_新.fillna(0)-x.pips_今.fillna(0); c=x[x.差.abs()>0.05].sort_values('差')
    print(f"  変わった玉 {len(c)} 得{int((c.差>0).sum())} {c.差[c.差>0].sum():+,.0f}p / 損{int((c.差<0).sum())} {c.差[c.差<0].sum():+,.0f}p")
    f=lambda v: '----' if pd.isna(v) else f"{v:+.0f}p"
    for _,r in pd.concat([c.head(4),c.tail(4)]).iterrows(): print(f"    {r.ent:%Y/%m/%d %H時} 今 {f(r.pips_今)} → 新 {f(r.pips_新)} 差{r.差:+.0f}")
    print()

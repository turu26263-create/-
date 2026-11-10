import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
MH=(15,16)
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**K,maho=MH)[0], raw,'server',5,0.003)
print('マホカンタ 修正機:', '全部○' if ok else [l for l in L if l.startswith('×')])
def form(**x):
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K,**x); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K,**x); dt,_=run_doten(srv,1,xtf='4h',**K,**x)
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None},**x)
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1)]: t['kind']=k; t['d']=d
    return pd.concat([b,s,dt,tb],ignore_index=True),base
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum())); st=stat(t)
    return f"{st['n']}玉 {st['sum']:+,.0f}p 勝率{st['win']/max(st['n'],1)*100:.1f}% PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
A0,base=form(); A1,_=form(maho=MH)
print('今(GWだけ休む)         ',sp(A0)); print('+マホカンタ(15・16時は入らない)',sp(A1))
k=lambda t: t.pips[pd.to_datetime(t.ent).dt.year.between(2016,2021)|(pd.to_datetime(t.ent).dt.year>=2025)].sum()
for nm,t in [('今',A0),('マホカンタ',A1)]:
    T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); print(f"  {nm} 0.01ロット 最後 {st['最後の資金']:,}円 落ち込み率 {st['落ち込み率']}%  確かめる年 {k(t):+,.0f}")
key=lambda t: set(zip(t.kind,t.ent))
g=A0[[x not in key(A1) for x in zip(A0.kind,A0.ent)]]; n=A1[[x not in key(A0) for x in zip(A1.kind,A1.ent)]]
print(f"入らなくなった玉 {len(g)}(勝ち{int((g.pips>0).sum())} 負け{int((g.pips<0).sum())}) {g.pips.sum():+,.0f}p / 代わりに出た玉 {len(n)} {n.pips.sum():+,.0f}p")
for _,r in g.sort_values('pips').head(5).iterrows(): print(f"   消 {r.kind} {r.ent:%Y/%m/%d %H時} {r.pips:+.0f}p")
for _,r in g.sort_values('pips').tail(5).iterrows(): print(f"   消 {r.kind} {r.ent:%Y/%m/%d %H時} {r.pips:+.0f}p")

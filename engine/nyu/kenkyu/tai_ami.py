import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
T0={**K,'maxpos':1,'tp':None}; T1={**T0,'sl':('4h','e21',0.05)}
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('4h','9割れ'),**T1)[0], raw,'server',1,0.003)
print('鯛の網 修正機:', '全部○' if ok else [l for l in L if l.startswith('×')])
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum())); st=stat(t)
    return f"{st['n']}玉 {st['sum']:+,.0f}p 勝率{st['win']/max(st['n'],1)*100:.1f}% PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
t0,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**T0); t1,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**T1)
for t,d in [(b,1),(s,-1),(dt,1),(t0,1),(t1,1)]: t['d']=d
print('鯛 今     ',sp(t0)); print('鯛 網あり',sp(t1))
A0=pd.concat([b,s,dt,t0],ignore_index=True); A1=pd.concat([b,s,dt,t1],ignore_index=True)
print('形3+鯛 今     ',sp(A0)); print('形3+鯛 網あり',sp(A1))
for nm,t in [('今',A0),('網あり',A1)]:
    T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); print(f"  {nm} 0.01ロット 最後 {st['最後の資金']:,}円 落ち込み率 {st['落ち込み率']}%")
m=t0.merge(t1,on='ent',how='outer',suffixes=('_今','_網')); m['差']=m.pips_網.fillna(0)-m.pips_今.fillna(0); c=m[m.差.abs()>0.05].sort_values('差')
W={'芯の降り':'4h9割れ','網':'網(4h赤の5p下)','TS':'TS550'}
print(f"変わった鯛 {len(c)}玉 得{int((c.差>0).sum())} {c.差[c.差>0].sum():+,.0f}p / 損{int((c.差<0).sum())} {c.差[c.差<0].sum():+,.0f}p")
for _,r in pd.concat([c.head(5),c.tail(5)]).iterrows():
    f=lambda v,w: '----' if pd.isna(v) else f"{v:+.0f}p {W.get(w,w)}"
    print(f"  {r.ent:%Y/%m/%d %H時}  今 {f(r.pips_今,r.why_今)} → 網 {f(r.pips_網,r.why_網)}  差{r.差:+.0f}")

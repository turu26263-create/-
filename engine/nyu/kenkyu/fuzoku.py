import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
C=dict(maxpos=5,n8=False,reenter=True,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
import json; A=json.loads(sys.argv[2]); B=json.loads(sys.argv[3]); nmA,nmB=sys.argv[4],sys.argv[5]
for X in (A,B):
    if 'tp' in X and X['tp']: X['tp']=tuple(X['tp'])
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**C,**B)[0], raw,'server',5,0.003)
print('\n'.join(l for l in L if not l.startswith('○')))
WHY={'芯の降り':'日足219','足しの降り':'日足219(足し)','TS':'TS550','利確':'利確'}
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum()))
    st=stat(t); return f"{st['n']}玉 {st['sum']:+,.0f}p PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
R={}
for nm,X in [(nmA,A),(nmB,B)]:
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**C,**X); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**C,**X)
    b['d']=1; s['d']=-1; t=pd.concat([b,s],ignore_index=True); R[nm]=t
    T,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    print(f"\n{nm}\n  買い {sp(b)}\n  売り {sp(s)}\n  売り買い {sp(t)}\n  0.01ロット 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%")
D=srv.feat('1D'); up=(D.e9>D.e21); grp=(up!=up.shift()).cumsum(); bg=[0,0]; sm=[0,0]
for g,x in D.groupby(grp):
    size=(x.h.max()-x.l.min())*100; st,en=x.index[0],x.k.iloc[-1]
    v=[R[n][(R[n].ent>=st)&(R[n].ent<en)].pips.sum() for n in (nmA,nmB)]
    if size>=1000: bg[0]+=v[0]; bg[1]+=v[1]
    else: sm[0]+=v[0]; sm[1]+=v[1]
print(f"\n大山13個 {bg[0]:+,.0f} → {bg[1]:+,.0f} / 小さい山100個 {sm[0]:+,.0f} → {sm[1]:+,.0f}")
a=R[nmA]; b=R[nmB]; m=a.merge(b,on=['ent','d'],how='outer',suffixes=('_A','_B')); m['差']=m.pips_B.fillna(0)-m.pips_A.fillna(0)
c=m[m.差.abs()>0.05].sort_values('差')
print(f"変わった玉 {len(c)} 得 {int((c.差>0).sum())}玉 {c.差[c.差>0].sum():+,.0f}p / 損 {int((c.差<0).sum())}玉 {c.差[c.差<0].sum():+,.0f}p")
f=lambda v,w: '----' if pd.isna(v) else f"{v:+.0f}p {WHY.get(w,w)}"
for _,r in pd.concat([c.head(6),c.tail(6)]).iterrows():
    print(f"  {'買' if r.d>0 else '売'} {r.ent:%Y/%m/%d %H時}  {f(r.pips_A,r.why_A)} → {f(r.pips_B,r.why_B)}  差{r.差:+.0f}")

import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
K0=dict(maxpos=5,n8=False,reenter=True,ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
A=dict(tp=('4h',3.5)); B=dict(tp=None,junkou='4h')
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**K0,**B)[0], raw,'server',5,0.003)
print('\n'.join(l for l in L if not l.startswith('○')))
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum()))
    st=stat(t); return f"{st['n']}玉 {st['sum']:+,.0f}p PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
R={}
for nm,X in [('今(4h+3.5σで利確)',A),('巡航が終わるまで持つ',B)]:
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K0,**X); b['d']=1
    s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K0,**X); s['d']=-1
    t=pd.concat([b,s],ignore_index=True); R[nm]=(b,s)
    T,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    print(f"\n{nm}\n  買い {sp(b)}\n  売り {sp(s)}\n  売り買い {sp(t)}\n  0.01ロット 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%")
    print('  降りの理由',t.why.map({'芯の降り':'日足219','足しの降り':'日足219','TS':'TS550','利確':'利確'}).value_counts().to_dict())
D=srv.feat('1D'); up=(D.e9>D.e21); grp=(up!=up.shift()).cumsum()
ks=list(R)
print('\n日足の山ごと 取った合計(一番取った玉):今 → 巡航が終わるまで')
big=[0,0]; small=[0,0]
for g,x in D.groupby(grp):
    size=(x.h.max()-x.l.min())*100; u=bool(up.loc[x.index[0]]); st,en=x.index[0],x.k.iloc[-1]
    v=[R[k][0 if u else 1] for k in ks]; v=[t[(t.ent>=st)&(t.ent<en)] for t in v]
    if size>=1000:
        big[0]+=v[0].pips.sum(); big[1]+=v[1].pips.sum()
        print(f"  {'上げ' if u else '下げ'} {st:%Y/%m/%d}〜{en:%Y/%m/%d} 山{size:,.0f}p  {v[0].pips.sum():+,.0f}p({v[0].pips.max() if len(v[0]) else 0:+,.0f}) → {v[1].pips.sum():+,.0f}p({v[1].pips.max() if len(v[1]) else 0:+,.0f})")
    else: small[0]+=v[0].pips.sum(); small[1]+=v[1].pips.sum()
print(f"大山13個の合計 {big[0]:+,.0f} → {big[1]:+,.0f} / 小さい山100個の合計 {small[0]:+,.0f} → {small[1]:+,.0f}")

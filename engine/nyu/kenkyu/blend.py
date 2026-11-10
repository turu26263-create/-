import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
ok,L=bugbug(lambda mk,d: run_oshime_d(mk,d)[0], raw,'server',5,0.003)
print('日足の押し目巡航 修正機:', '全部○' if ok else [l for l in L if l.startswith('×')]); [print(' ',l) for l in L if l.startswith('△')]
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum())); st=stat(t)
    return f"{st['n']}玉 {st['sum']:+,.0f}p 勝率{st['win']/max(st['n'],1)*100:.1f}% PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None})
ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
for t,dd in [(b,1),(s,-1),(dt,1),(tb,1),(ob,1),(os_,-1)]: t['d']=dd
K3=pd.concat([b,s,dt,tb],ignore_index=True); OS=pd.concat([ob,os_],ignore_index=True); BL=pd.concat([K3,OS],ignore_index=True)
print('\n押し目巡航 買い',sp(ob)); print('押し目巡航 売り',sp(os_)); print('押し目巡航    ',sp(OS))
print('\nKujira3        ',sp(K3)); print('Kujira3+押し目巡航',sp(BL))
k=lambda t: t.pips[pd.to_datetime(t.ent).dt.year.between(2016,2021)|(pd.to_datetime(t.ent).dt.year>=2025)].sum()
for nm,t in [('Kujira3',K3),('ブレンド',BL)]:
    T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20); print(f"  {nm} 0.01ロット 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}%  確かめる年 {k(t):+,.0f}")
y=pd.to_datetime(OS.ent).dt.year; print('\n押し目巡航 年ごと:',OS.groupby(y).pips.sum().round().astype(int).to_dict())
W={'芯の降り':'日足219','網':'網(前の日のひげ先)','利確':'日足3.5σ'}
print('押し目巡航 降りの理由:',OS.why.map(lambda w: W.get(w,w)).value_counts().to_dict())
o2=OS.sort_values('pips'); print('一番勝った5玉'); [print(f"  {'買' if r.d>0 else '売'} {r.ent:%Y/%m/%d} {r.e:.3f} → {pd.Timestamp(r.ext):%m/%d} {r.pips:+.0f}p {W.get(r.why,r.why)}") for _,r in o2.tail(5).iterrows()]
print('一番負けた5玉'); [print(f"  {'買' if r.d>0 else '売'} {r.ent:%Y/%m/%d} {r.e:.3f} → {pd.Timestamp(r.ext):%m/%d} {r.pips:+.0f}p {W.get(r.why,r.why)}") for _,r in o2.head(5).iterrows()]

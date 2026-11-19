import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
C=dict(maxpos=5,n8=False,reenter=True,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
def run(X):
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**C,**X); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**C,**X)
    b['d']=1; s['d']=-1; t=pd.concat([b,s],ignore_index=True)
    T,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: float(t.pips[m].sum())
    return dict(n=len(t),sum=t.pips.sum(),sen=f(y.between(2022,2024)),k1=f(y.between(2016,2021)),k2=f(y>=2025),dd=st['落ち込み率'],yen=st['最後の資金'],t=t)
D=srv.feat('1D'); up=(D.e9>D.e21); grp=(up!=up.shift()).cumsum()
yama=[(x.index[0],x.k.iloc[-1],(x.h.max()-x.l.min())*100) for g,x in D.groupby(grp)]
def bs(t):
    bg=sum(t[(t.ent>=a)&(t.ent<b)].pips.sum() for a,b,z in yama if z>=1000); return bg, t.pips.sum()-bg
line=lambda nm,r: f"  {nm}: {r['n']}玉 {r['sum']:+,.0f}p | 選22-24 {r['sen']:+,.0f} 確16-21 {r['k1']:+,.0f} 確25-26 {r['k2']:+,.0f} | 落ち込み率 {r['dd']}% | 大山 {bs(r['t'])[0]:+,.0f} 小さい山 {bs(r['t'])[1]:+,.0f}"
print('決め方(先に決めた):足して「確かめる年(16-21と25-26)の合計が上がる」かつ「落ち込み率が上がらない」なら残す。どちらか悪くなれば外す\n')
cur=dict(kawa_chi=False,sao=99.0); r0=run(cur); print(line('基本だけ',r0))
for nm,add in [('TS550',dict(ts=550)),('利確 4h+3.5σ',dict(tp=('4h',3.5))),('竿先(2σの外で入らない)',dict(sao=2.0)),('川の外(±1σ)+遅行',dict(kawa_chi=True))]:
    nx={**cur,**add}
    ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**C,**nx)[0], raw,'server',5,0.003)
    r1=run(nx); keep=(r1['k1']+r1['k2']>r0['k1']+r0['k2']) and (r1['dd']<=r0['dd'])
    print(f"\n+{nm}  修正機:{'全部○' if ok else '×あり'}"); print(line('足す前',r0)); print(line('足した',r1))
    print(f"  → {'残す' if keep else '外す'}(確かめる年 {r0['k1']+r0['k2']:+,.0f} → {r1['k1']+r1['k2']:+,.0f}・落ち込み率 {r0['dd']}% → {r1['dd']}%)")
    if keep: cur, r0 = nx, r1
print('\nええとこどりの形:', {k:v for k,v in cur.items()}); print(line('ええとこどり',r0)); print(f"  0.01ロット 最後 {r0['yen']:,}円")
r2=run(dict(tp=('4h',3.5),ts=550)); print(line('今の形2(付属品ぜんぶ)',r2)); print(f"  0.01ロット 最後 {r2['yen']:,}円")

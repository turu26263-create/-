import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); srv=Market(raw,'server')
ok,L=bugbug(lambda mk,d: run_kujira_dan(mk,d)[0], raw,'server',5,0.003,bar='1D')
print('\n'.join(l for l in L if not l.startswith('○')))
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True)
def sp(t):
    y=pd.to_datetime(t.ent).dt.year; f=lambda m: round(float(t.pips[m].sum()))
    st=stat(t); return f"{st['n']}玉 {st['sum']:+,.0f}p PF{st['pf']} | 選22-24 {f(y.between(2022,2024)):+,} 確16-21 {f(y.between(2016,2021)):+,} 確25-26 {f(y>=2025):+,}"
b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); b['d']=1; s['d']=-1
wb,_=run_kujira_dan(srv,1); ws,_=run_kujira_dan(srv,-1); wb['d']=1; ws['d']=-1
f2=pd.concat([b,s],ignore_index=True); w=pd.concat([wb,ws],ignore_index=True); al=pd.concat([f2,w],ignore_index=True)
D=srv.feat('1D'); up=(D.e9>D.e21); grp=(up!=up.shift()).cumsum(); yama=[(x.index[0],x.k.iloc[-1],(x.h.max()-x.l.min())*100) for g,x in D.groupby(grp)]
def bs(t):
    bg=sum(t[(t.ent>=a)&(t.ent<=b2+pd.Timedelta('2D'))].pips.sum() for a,b2,z in yama if z>=1000); return bg, t.pips.sum()-bg
for nm,t in [('形2(魚の刺身)',f2),('クジラの段々5発(何も無し)',w),('ええとこどり=形2+クジラの段々',al)]:
    T,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    g=bs(t); print(f"\n{nm}\n  {sp(t)}\n  大山 {g[0]:+,.0f} 小さい山 {g[1]:+,.0f}\n  0.01ロット 最後 {st['最後の資金']:,}円 一番へこんだ {st['一番へこんだ資金']:,}円 落ち込み率 {st['落ち込み率']}% 強制決済 {st['強制決済']}")
print('\nクジラの段々 1発目〜5発目ごと:', w.groupby(w.groupby(['d','camp']).cumcount()+1).pips.agg(['count','sum']).round().to_dict('index'))
y=pd.to_datetime(al.ext).dt.year; print('ええとこどり 年ごと:',al.groupby(y).pips.sum().round().astype(int).to_dict())

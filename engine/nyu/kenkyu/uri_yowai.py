import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); D=srv.feat('1D'); k1=D.k.values
s['n']=s.groupby('camp').cumcount()+1; s['y']=pd.to_datetime(s.ent).dt.year
rows=[]
for _,r in s.iterrows():
    q=np.searchsorted(k1,np.datetime64(r.ent),'right')-1; d=D.iloc[q]
    rng=(D.h.iloc[q-19:q+1].max()-D.l.iloc[q-19:q+1].min())*100
    rows.append(dict(青と赤の間=round((d.e21-d.e9)*100),二十日の幅=round(rng),日足200の下=bool(d.c<d.e200),赤の傾き=round((d.e21-D.e21.iloc[q-3])*100)))
X=pd.concat([s.reset_index(drop=True),pd.DataFrame(rows)],axis=1)
bad=X.y.isin([2019,2020,2021,2026])
print('売り 弱い年(2019・20・21・26)と ほかの年:入った時の日足の様子(中央の値)')
for nm,m in [('弱い年',bad),('ほかの年',~bad)]:
    g=X[m]; print(f"  {nm}: {len(g)}玉 {g.pips.sum():+,.0f}p 勝率{(g.pips>0).mean()*100:.0f}% | 青と赤の間 {g.青と赤の間.median():.0f}p・20日の幅 {g.二十日の幅.median():.0f}p・赤の3日の傾き {g.赤の傾き.median():.0f}p・日足200の下 {g.日足200の下.mean()*100:.0f}%")
print('\n20日の幅(日足20本の高値−安値)で分けた(全部の年)')
print(X.groupby(pd.cut(X.二十日の幅,[0,250,350,500,800,5000])).pips.agg(['count','sum','mean']).round().to_string())
print('\n青と赤の間(日足21−日足9)で分けた')
print(X.groupby(pd.cut(X.青と赤の間,[-500,10,30,60,120,1000])).pips.agg(['count','sum','mean']).round().to_string())
print('\n1発目だけ・降りの理由'); print(X[X.n==1].groupby(X.why.map({'芯の降り':'日足921','利確':'利確','TS':'TS550'})).pips.agg(['count','sum']).round().to_string())
from bugbug import bugbug
raw=load_cached(sys.argv[1])
ok,L=bugbug(lambda mk,d: run_tai(mk,'1D','4h','1h',d,('1D','219'),**K,narabi=True)[0], raw,'server',5,0.003); print('\n修正機:', '全部○' if ok else [l for l in L if l.startswith('×')])
def blend(nb):
    KS={**K,'narabi':nb}
    b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**KS); dt,_=run_doten(srv,1,xtf='4h',**KS)
    tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d
    return pd.concat([b,s,dt,tb,ob,os_],ignore_index=True),base
print('決め方(先に決めた):確かめる年の合計が上がり、落ち込み率が上がらなければ残す')
for nm,nb in [('今','x'),('売りは日足が219の並び(青が赤の下)の時だけ',True)]:
    t,base=blend(False if nb=='x' else True); y=pd.to_datetime(t.ent).dt.year; T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    u=t[t.kind=='売り']; d_=t[t.kind=='ドテン買い']; uy=u.groupby(pd.to_datetime(u.ent).dt.year).pips.sum().round().astype(int).to_dict()
    print(f"  {nm}: 売り {len(u)}玉 {u.pips.sum():+,.0f}p / ドテン {len(d_)}玉 {d_.pips.sum():+,.0f}p / 全部 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}%\n     売りの年ごと {uy}")

import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
b,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
W={'芯の降り':'日足219/921','足しの降り':'日足219/921','TS':'TS550','利確':'利確','網':'前の日のひげ先'}
for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d; t['w']=t.why.map(lambda x: W.get(x,x))
dt['w']='4h219かTS'; tb['w']=tb.why.map({'芯の降り':'4h9割れ','TS':'TS550'})
A=pd.concat([b,s,dt,tb,ob,os_],ignore_index=True); A['y']=pd.to_datetime(A.ext).dt.year
D=srv.feat('1D'); H4=srv.feat('4h'); k1=D.k.values; k4=H4.k.values
for Y in (2019,2020):
    a=A[A.y==Y]; dd=D[D.index.year==Y]
    print(f"===== {Y}年:日足 高値 {dd.h.max():.2f} 安値 {dd.l.min():.2f}(1年の幅 {(dd.h.max()-dd.l.min())*100:,.0f}p)・日足の9と21が入れ替わった回数 {int(((dd.e9>dd.e21)!=(dd.e9>dd.e21).shift()).sum())-1}回")
    g=a.groupby('kind').pips.agg(['count','sum']); g['勝ち']=a[a.pips>0].groupby('kind').size(); print(g.round().fillna(0).astype(int).T.to_string()); print(f"  合計 {len(a)}玉 {a.pips.sum():+,.0f}p")
    print('  降りの理由ごと:', {k: f"{int(v['count'])}玉 {v['sum']:+,.0f}p" for k,v in a.groupby('w').pips.agg(['count','sum']).iterrows()})
    for _,r in a.sort_values('ent').iterrows():
        q=np.searchsorted(k1,np.datetime64(r.ent),'right')-1; h=np.searchsorted(k4,np.datetime64(r.ent),'right')-1; d=D.iloc[q]; hh=H4.iloc[h]
        nar='921' if d.e9>d.e21 else '219'
        print(f"  {r.kind:<5} {r.ent:%m/%d %H時} {r.e:7.3f} → {pd.Timestamp(r.ext):%m/%d %H時} {r.x:7.3f} {r.pips:+6.0f}p 伸び{r.mfe:+4.0f} {r.w:<8}| 日足:終値は青の{'上' if d.c>d.e9 else '下'}・赤の{'上' if d.c>d.e21 else '下'}・並び{nar}・赤の向き{'上' if d.e21>D.e21.iloc[q-3] else '下'}({(d.e21-D.e21.iloc[q-3])*100:+.0f}p) 4h:終値は赤の{'上' if hh.c>hh.e21 else '下'}")

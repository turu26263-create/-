import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
H=srv.feat('1h'); H4=srv.feat('4h'); D=srv.feat('1D')
k4=H4.k.values; k1=D.k.values
d4=lambda t: np.searchsorted(k4,np.datetime64(t),'right')-1
d1=lambda t: np.searchsorted(k1,np.datetime64(t),'right')-1
def why(i,d):
    t=H.index[i]+pd.Timedelta('1h'); r=H.iloc[i]; h=d4(t); dd=d1(H4.k.iloc[h]); q=d1(t)
    up=r.e9>r.e21; up1=H.e9.iloc[i-1]>H.e21.iloc[i-1]
    cross=(up and not up1) if d>0 else ((not up) and up1)
    pD=(D.c.iloc[dd]>D.e9.iloc[dd]) if d>0 else (D.c.iloc[dd]<D.e9.iloc[dd])
    p4=(H4.c.iloc[h]>H4.e21.iloc[h]) if d>0 else (H4.c.iloc[h]<H4.e21.iloc[h])
    kawa=(r.c>r.md+r.sd) if d>0 else (r.c<r.md-r.sd)
    chi=(r.c>H.h.iloc[i-21]) if d>0 else (r.c<H.l.iloc[i-21])
    ns=(r.c<=r.md+2*r.sd) if d>0 else (r.c>=r.md-2*r.sd)
    b21=(D.e21.iloc[q]-D.e21.iloc[q-3])*d>0
    return dict(時刻=H.index[i],終値=round(r.c,3),日足9の向こう=pD,四時間21の向こう=p4,川の外=kawa,遅行=chi,竿先でない=ns,日足21の向き=b21)
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
print('■ A 下げの大山 2022/11/09〜2023/02/08:12/13 から後に売りが入らなかった理由')
s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K)
print('  入った売り:'); [print(f"   {r.ent:%m/%d %H時} {r.e:.3f} → {pd.Timestamp(r.ext):%m/%d %H時} {r.pips:+.0f}p") for _,r in s[(s.ent>='2022-11-09')&(s.ent<'2023-02-09')].iterrows()]
sub=H.loc['2022-12-13':'2023-02-08']; idx=[H.index.get_loc(t) for t in sub.index]
rows=[why(i,-1) for i in idx if (H.e9.iloc[i]<H.e21.iloc[i]) and not (H.e9.iloc[i-1]<H.e21.iloc[i-1])]
R=pd.DataFrame(rows)
print(f"\n  この間に1時間の219が出た足 {len(R)}本。決まりごとに ×だった本数:")
for c in ['日足9の向こう','四時間21の向こう','川の外','遅行','竿先でない','日足21の向き']: print(f"   {c}: ×{int((~R[c]).sum())}本")
print('  日足の様子(この間):'); DD=D.loc['2022-12-12':'2023-02-08']
for t,r in DD.iloc[::4].iterrows():
    print(f"   {t:%m/%d} 終値{r.c:.3f} 青9 {r.e9:.3f} 赤21 {r.e21:.3f}  ロウソクは青の{'下' if r.c<r.e9 else '上'}・赤の{'下' if r.c<r.e21 else '上'}  21の向き {'下' if r.e21<D.e21.shift(3).loc[t] else '上'}")
print('\n  219が出た足の一覧(○=通った ×=止めた):')
for _,r in R.iterrows(): print('   '+f"{r.時刻:%m/%d %H時} {r.終値:.3f} "+' '.join(f"{c}{'○' if r[c] else '×'}" for c in ['日足9の向こう','四時間21の向こう','川の外','遅行','竿先でない','日足21の向き']))
print('\n■ B 上げの大山 2024/03/20〜2024/07/16 の鯛の刺身')
tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None})
x=tb[(tb.ent>='2024-03-20')&(tb.ent<'2024-07-17')]
for _,r in x.iterrows():
    t=r.ent; q=d1(t); h=d4(t); hh=H4.iloc[h]; dd=D.iloc[q]
    kk=0
    while D.c.iloc[q-kk]>D.e9.iloc[q-kk]: kk+=1
    w={'芯の降り':'4h9割れ','TS':'TS550'}.get(r.why,r.why)
    print(f"   {t:%m/%d %H時} {r.e:.3f} → {pd.Timestamp(r.ext):%m/%d %H時} {r.x:.3f} {r.pips:+5.0f}p(伸び{r.mfe:+.0f}) {w} | 日足:青の上{kk}本目・帯{(r.e-dd.md)/dd.sd:+.1f}σ | 4h:帯{(r.e-hh.md)/hh.sd:+.1f}σ・9との差{(r.e-hh.e9)*100:+.0f}p")

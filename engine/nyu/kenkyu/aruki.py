import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
b,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(srv,1,xtf='4h',**K)
tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None})
for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1)]: t['kind']=k; t['d']=d
tb['why']=tb.why.replace({'芯の降り':'4h9割れ'}); dt['why']=dt.why.replace({'芯の降り':'4h219'})
A=pd.concat([b,s,dt,tb],ignore_index=True)
D=srv.feat('1D'); up=(D.e9>D.e21); grp=(up!=up.shift()).cumsum(); G=list(D.groupby(grp))
WHY={'芯の降り':'日足219','足しの降り':'日足219','TS':'TS550','利確':'利確'}
print('日足の山(9と21の並びが続く間)ごとに、形3+鯛で取れた所を歩いた。山=その間の高値−安値。下から上=山の始まりの安値(下げは高値)から一番上(下げは下)まで\n')
rows=[]
for n,(g,x) in enumerate(G[1:-1],1):
    u=bool(up.loc[x.index[0]]); st=x.index[0]; nx=G[n+1][1].index[0]; size=(x.h.max()-x.l.min())*100
    if size<1000: 
        m=A[(A.ent>=st)&(A.ent<nx)]; rows.append((False,m.pips.sum(),len(m))); continue
    m=A[(A.ent>=st)&(A.ent<nx)].sort_values('ent'); rows.append((True,m.pips.sum(),len(m)))
    lo,hi=(x.l.min(),x.h.max()); top=x.h.idxmax() if u else x.l.idxmin(); bot=x.l.idxmin() if u else x.h.idxmax()
    print(f"■ {'上げ' if u else '下げ'}の大山 {st:%Y/%m/%d}〜{nx:%Y/%m/%d}  {('安値' if u else '高値')} {(lo if u else hi):.3f}({bot:%m/%d}) → {('高値' if u else '安値')} {(hi if u else lo):.3f}({top:%m/%d})  山 {size:,.0f}p")
    mine=m[m.d==(1 if u else -1)]; rev=m[m.d!=(1 if u else -1)]
    if len(mine):
        f=mine.iloc[0]; l=mine.sort_values('ext').iloc[-1]
        print(f"   最初の入り {f.ent:%m/%d %H時} {f.e:.3f}(山の{'下' if u else '上'}から {abs(f.e-(lo if u else hi))*100:,.0f}p)/最後の降り {pd.Timestamp(l.ext):%m/%d %H時} {l.x:.3f}({'上' if u else '下'}の端まで {abs((hi if u else lo)-l.x)*100:,.0f}p)")
        best=mine.loc[mine.pips.idxmax()]
        print(f"   向きの玉 {len(mine)}玉 {mine.pips.sum():+,.0f}p(勝ち{int((mine.pips>0).sum())}・負け{int((mine.pips<0).sum())})  一番取った {best.kind} {best.ent:%m/%d} {best.pips:+,.0f}p {WHY.get(best.why,best.why)}  → 山の{best.pips/size*100:.0f}%")
        kinds=mine.groupby('kind').pips.agg(['count','sum']).round(); print('   内訳:',' / '.join(f"{k} {int(r['count'])}玉 {r['sum']:+,.0f}p" for k,r in kinds.iterrows()))
        why=mine.why.map(lambda w: WHY.get(w,w)).value_counts().to_dict(); print('   降りの理由:',why)
    else: print('   向きの玉なし')
    if len(rev): print(f"   逆向きの玉(山の中の戻りを取りに行った) {len(rev)}玉 {rev.pips.sum():+,.0f}p")
    print()
R=pd.DataFrame(rows,columns=['big','p','n'])
print(f"大山 {int(R.big.sum())}個 合わせて {R[R.big].p.sum():+,.0f}p({int(R[R.big].n.sum())}玉)/レンジ {int((~R.big).sum())}個 {R[~R.big].p.sum():+,.0f}p({int(R[~R.big].n.sum())}玉)")

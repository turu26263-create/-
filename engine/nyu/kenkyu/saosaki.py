# ×(11-11)。部品(竿先で5分がレンジ → 網を建値へ)はエンジンから外した。この書き物はそのままでは動かない。部品は git の記録 7eaed35 にある。結果は engine/kekka_tai/nyu/竿先で5分レンジ_しあわせセットへ移す.txt
# 11-11 たくちん「竿先 5分でれんじになったら 竿元で買ったエントリーをしあわせセットに移行にできん?」「ご」
# 使い方: python3 saosaki.py <MT4 1時間足の置き場> <HistData 1分足の置き場> [seiseki]
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1]); fine=load_cached(sys.argv[2]); srv=Market(raw,'server'); range5_on(srv,fine)
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def mk5(mk):
    if not hasattr(mk,'r5'): range5_on(mk,fine)      # 帯の幅は上下ひっくり返しても同じなので、鏡のデータにも同じ5分足を使える
    return mk
make=lambda mk,d: run_tai(mk5(mk),'1D','4h','1h',d,('1D','219'),**K,saolock='1h')[0]
ok,L=bugbug(make,raw,'server',5,0.003); print('バグバグ修正機:', '全部○' if ok else '×あり'); print('\n'.join(l for l in L if not l.startswith('○')))
kowashi=lambda mk,d: run_tai(mk5(mk),'1D','4h','1h',d,('1D','219'),**K,saolock='1h')[0].assign(pips=lambda t: t.pips+(t.why=='建値')*5)
print('わざと壊した形(建値の玉に+5p):', '×を出した' if not bugbug(kowashi,raw,'server',5,0.003)[0] else '×を出さない(修正機に型が要る)')
# ---- ローソクで歩く(1戦だけ)と、建値で大きく負けた玉
b,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K,saolock='1h'); b0,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K)
s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K,saolock='1h'); s0,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K)
x=srv.feat('1h'); LB=sao_lock(srv,'1h',1); LS=sao_lock(srv,'1h',-1)
print('合図(竿先で5分がレンジ)が出た1時間足: 買い向き',int((~np.isnan(LB)).sum()),'本 / 売り向き',int((~np.isnan(LS)).sum()),'本 / 5分足のある1時間足',int(srv.w5.notna().sum()),'本 / 全部',len(x))
for nm,t in [('買い',b),('売り',s)]:
    q=t[(t.why=='建値')&(t.pips<-1.3)]
    for r in q.itertuples(): print(f'建値で大きく負け {nm} {r.ent} {r.e:.3f} → {r.ext} {r.x:.3f} {r.pips:+.1f}p  降りた足の始値 {x.o[r.ext]:.3f}・1本前の終値 {x.c.shift(1)[r.ext]:.3f}')
def aruki(t,t0,LK,d,a,bb):
    print(f'--- 歩き {a}〜{bb}({"買い" if d>0 else "売り"})---')
    for nm,tt in [('今の形',t0),('竿先しあわせ',t)]:
        q=tt[(tt.ent>=a)&(tt.ent<=bb)]
        for r in q.itertuples(): print(f'  {nm} {r.n}発目 {r.ent:%m/%d %H時} {r.e:.3f} → {r.ext:%m/%d %H時} {r.x:.3f} {r.pips:+.1f}p {r.why}(伸びた最大 {r.mfe:+.0f}p)')
    w=x[a:bb]; i0=x.index.get_loc(w.index[0])
    for k,(ts,r) in enumerate(w.iterrows()):
        if not np.isnan(LK[i0+k]) or (r.c>r.md+2*r.sd if d>0 else r.c<r.md-2*r.sd):
            print(f'  {ts:%m/%d %H時} 終値 {r.c:.3f} 1時間の2σ {r.md+2*d*r.sd:.3f} 竿先の外={"はい" if (r.c>r.md+2*r.sd if d>0 else r.c<r.md-2*r.sd) else "いいえ"} 5分の帯の幅 {srv.w5[ts]:.1f}p 5分がレンジ={"はい" if srv.r5[ts] else "いいえ"} → 合図={"出た" if not np.isnan(LK[i0+k]) else "なし"}')
def kawari(t,t0,nm):
    m=t.merge(t0,on=['ent','n'],how='outer',suffixes=('','_0')); df=m[(m.pips-m.pips_0).abs()>0.05]
    print(f'{nm}: 変わった玉 {len(df)} / 今の形に無い新しい玉 {int(m.pips_0.isna().sum())} / 消えた玉 {int(m.pips.isna().sum())} / 建値で降りた玉 {int((t.why=="建値").sum())}'); return df.sort_values('ent')
df=kawari(b,b0,'買い(1時間の竿先)'); f=df.iloc[0]; a_,b_=f.ent-pd.Timedelta('2h'),f.ent+pd.Timedelta('30h')
aruki(b,b0,LB,1,a_,b_)
b4,_=run_tai(srv,'1D','4h','1h',1,('1D','219'),**K,saolock='4h'); LB4=sao_lock(srv,'1h',1,2.0,'4h'); LS4=sao_lock(srv,'1h',-1,2.0,'4h')
print('合図(4時間の竿先で5分がレンジ): 買い向き',int((~np.isnan(LB4)).sum()),'本 / 売り向き',int((~np.isnan(LS4)).sum()),'本')
df4=kawari(b4,b0,'買い(4時間の竿先)'); f=df4.iloc[0]; print('4時間の竿先で最初に変わった玉:'); aruki(b4,b0,LB4,1,f.ent-pd.Timedelta('2h'),f.ent+pd.Timedelta('30h'))
if len(sys.argv)>3:
    def blend(sl):
        KB={**K,'saolock':sl}
        bb,base=run_tai(srv,'1D','4h','1h',1,('1D','219'),**KB); ss,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**KB); dt,_=run_doten(srv,1,xtf='4h',**KB)   # ドテン買いは売りの利確で構えるので、売りと同じ形を渡す
        tb,_=run_tai(srv,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(srv,1); os_,_=run_oshime_d(srv,-1)
        for t,k,d in [(bb,'買い',1),(ss,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d
        return pd.concat([bb,ss,dt,tb,ob,os_],ignore_index=True),base
    print('決め方(先に決めた・前と同じ):確かめる年の合計が上がり、落ち込み率が上がらなければ残す。5分足は2025/04まで(その後は合図が出ないので今の形と同じ)')
    for nm,sl in [('今の形',False),('1時間の竿先(±2σの外で閉じてから6時間のうち)で5分がレンジ → 網を建値へ','1h'),('4時間の竿先(直近の4時間足が±2σの外)で5分がレンジ → 網を建値へ','4h')]:
        t,base=blend(sl); y=pd.to_datetime(t.ent).dt.year; T_,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
        f=lambda k: f"{int((t.kind==k).sum())}玉 {t.pips[t.kind==k].sum():+,.0f}p"
        print(f"  {nm}:\n     買い {f('買い')} / 売り {f('売り')} / ドテン買い {f('ドテン買い')} / 全部 {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 建値で降り {int((t.why=='建値').sum())}玉")

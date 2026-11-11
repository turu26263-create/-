# 11-11 たくちん「ご」:週の竿先で出た日足の竿元を消す(先に数で決めてから照らす)
# 【置き換え・照らす前に決めた】週足=月曜0時からの7日足(閉じた週だけ)。週の帯=週の終値の20本平均±2σ(母標準偏差)
#   週の竿先=竿元の日足が閉じた時点で、直近に閉じた4本の週足のどれかの終値が、竿元と同じ向きの外側(買いは+2σの上・売りは−2σの下)で閉じた
#   → その竿元には入らない。入り方・降りは前と同じ(竿元1発+4時間の9への押し目で5発まで・日足219まで取り切り)
import sys,io,contextlib,runpy,warnings; warnings.filterwarnings('ignore')
sys.argv=[sys.argv[0],sys.argv[1]]
with contextlib.redirect_stdout(io.StringIO()): g=runpy.run_path('/home/user/-/engine/nyu/kenkyu/saomoto_damashi.py')
T=g['T']; W=g['W']; D=g['D']; pd=g['pd']; np=g['np']
W=W.copy(); W['md']=W.c.rolling(20).mean(); W['sd']=W.c.rolling(20).std(ddof=0)
W['up_out']=W.c>W.md+2*W.sd; W['dn_out']=W.c<W.md-2*W.sd
W['up4']=W.up_out.rolling(4,min_periods=1).max().astype(bool); W['dn4']=W.dn_out.rolling(4,min_periods=1).max().astype(bool)
yw=pd.merge_asof(pd.DataFrame({'k':D.k.values}),W[['k','up4','dn4','md']].sort_values('k'),on='k',direction='backward'); yw.index=D.index
def saosaki(s_,v):
    t=pd.Timestamp(s_.replace('/','-')); r=yw.loc[t]
    if pd.isna(r.md): return None
    return bool(r.up4) if v=='買い' else bool(r.dn4)
T['週の竿先']=[saosaki(s_,v) for s_,v in zip(T.竿元,T.向き)]
sel=lambda z:z[z.年.between(2022,2024)].合計.sum(); chk=lambda z:z[~z.年.between(2022,2024)].合計.sum()
print(f'もと:{len(T)}回 {T.合計.sum():+,}p(選22-24 {sel(T):+,}・確かめる年 {chk(T):+,})/週の帯が出ない竿元(データの始め) {int(T.週の竿先.isna().sum())}回は消さない')
m=T.週の竿先.fillna(False).astype(bool); k=T[m]; s=T[~m]
print(f'週の竿先で出た竿元:{len(k)}回(勝ち {int(k.勝ち.sum())}・負け {int((~k.勝ち).sum())}){k.合計.sum():+,}p')
print(f'消した後:{len(s)}回(勝ち {int(s.勝ち.sum())}・負け {int((~s.勝ち).sum())}){s.合計.sum():+,}p / 選22-24 {sel(s):+,} / 確かめる年 {chk(s):+,}')
print('  年ごと(消した後)',s.groupby('年').合計.sum().to_dict())
print('--- 消えた竿元 ---'); print(k[['竿元','向き','合計','週921']].to_string(index=False))
print('--- 大山の始まりの竿元(消えたか)---')
for d_ in ['2016/10/06','2018/01/10','2022/02/10','2022/11/10','2023/04/17','2023/11/20','2024/04/15','2024/10/02','2025/01/16','2025/09/24']:
    r=T[T.竿元==d_].iloc[0]; print(f'  {d_} {r.向き} {r.合計:+,}p 週の竿先={r.週の竿先}')
# ---- 参考(決まりではない):竿元の時、週足の終値が週の帯のどこにいたか(σで)と、週の9・21の並びが何週続いていたか
W['z']=(W.c-W.md)/W.sd; up=(W.e9>W.e21); W['run']=up.groupby((up!=up.shift()).cumsum()).cumcount()+1
yz=pd.merge_asof(pd.DataFrame({'k':D.k.values}),W[['k','z','run','e9','e21']].sort_values('k'),on='k',direction='backward'); yz.index=D.index
print('--- 参考:竿元の時の週足の位置(向きにそろえたσ)と、週の9・21が同じ並びで何週目か ---')
for d_ in ['2016/10/06','2018/01/10','2022/02/10','2022/11/10','2023/04/17','2023/11/20','2024/04/15','2025/01/16','2025/09/24','2022/07/14','2024/02/13','2024/09/06','2025/04/03','2026/06/18','2020/07/24','2019/08/02']:
    r=T[T.竿元==d_].iloc[0]; q=yz.loc[pd.Timestamp(d_.replace('/','-'))]; sg=1 if r.向き=='買い' else -1
    same=(q.e9>q.e21)==(sg>0)
    print(f"  {d_} {r.向き} {r.合計:+,}p:週の位置 {q.z*sg:+.1f}σ / 週の並び {'竿元と同じ向き' if same else '逆向き'} {int(q.run)}週目")

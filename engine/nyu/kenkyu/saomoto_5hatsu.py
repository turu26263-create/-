# 11-11 たくちん「竿元からはいらんと意味がない」(前の照らしは日足921で入っていた)
# 竿元=竿の根っこ(たくちん 10-29「入るのはレンジのあとbbしぼんだ後のバンドブレイクが竿根っこやで」)
# 【置き換え】日足の竿元=日足の帯(±2σの幅)が直前6本のどこかで、ふだん(その前100本の平均)の0.7倍より狭くしぼみ、終値が+2σの外で閉じた最初の1本(売りは−2σの外)(決まり帳 根1 の日足版)
#   入り:竿元の足が閉じた次の日から3本で 2・2・1発(各日の1時の始値)。2・3本目は前の日足の終値がまだ9の上の時だけ(売りは下)
#   降り:入った後に新しく出た日足219(売りは921)が閉じた次の日の1時の始値だけ。利確・TS・網は無し(何もせず取り切る)。スプレッド0.3p
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
raw=load_cached(sys.argv[1]); srv=Market(raw,'server'); SPR=0.003
D=srv.feat('1D'); H=srv.feat('1h')
w=(4*D.sd); sq=(w<0.7*w.shift(1).rolling(100).mean()); sq6=sq.rolling(6,min_periods=1).max().fillna(0).astype(bool).values
def at1(t):
    j=np.searchsorted(H.index.values,np.datetime64(t)+np.timedelta64(1,'h')); return j if j<len(H) else None
def run(d,hai=(2,2,1)):
    out_=(D.c>D.md+2*D.sd).values if d>0 else (D.c<D.md-2*D.sd).values
    c9=(D.c>D.e9).values if d>0 else (D.c<D.e9).values; up=(D.e9>D.e21).values if d>0 else (D.e9<D.e21).values
    out=[]; i=101; n=len(D); busy_until=-1
    while i<n-1:
        if i>busy_until and out_[i] and not out_[i-1] and sq6[i-1]:
            k=i+1
            while k<n and not (up[k-1] and not up[k]): k+=1          # 入った後に新しく出た219
            if k>=n: break
            jx=at1(D.k.values[k]); xo=H.o.values[jx]+(0 if d>0 else SPR)
            for m,cnt in enumerate(hai):
                q=i+m
                if q>=k or (m>0 and not c9[q]): continue
                je=at1(D.k.values[q]); e=H.o.values[je]+(SPR if d>0 else 0)
                for _ in range(cnt): out.append(dict(ent=H.index[je],e=e,ext=H.index[jx],x=xo,pips=(xo-e)/0.01*d,sao=D.index[i],n=m+1,d=d))
            busy_until=k; i=k
        else: i+=1
    return pd.DataFrame(out)
t=pd.concat([run(1),run(-1)],ignore_index=True); y=pd.to_datetime(t.ent).dt.year
_,st=lot_sizing(t,H,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
g=t.groupby(['sao','d']).agg(玉=('pips','size'),合計=('pips','sum'),降り=('ext','first')).reset_index()
print(f"竿元から5発・取り切り:{len(g)}回 {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}% 最後 {st['最後の資金']:,}円 強制決済 {st['強制決済']}")
print('  年ごと',{int(k):round(v) for k,v in t.groupby(y).pips.sum().items()})
w_=g.合計>0; print(f'  勝った回 {int(w_.sum())} +{g.合計[w_].sum():,.0f}p / 負けた回 {int((~w_).sum())} {g.合計[~w_].sum():,.0f}p')
print('--- 竿元を全部(日付・向き・入った玉・5発の合計・降りた日)---')
for r in g.itertuples(): print(f"  {r.sao:%Y/%m/%d} {'買い' if r.d>0 else '売り'} {r.玉}玉 {r.合計:+,.0f}p → {pd.Timestamp(r.降り):%Y/%m/%d}")
# 11-07 の大山13個に竿元で入れたか
YAMA=[('下げ','2016-06-06','2016-07-19'),('上げ','2016-10-06','2017-01-13'),('上げ','2022-01-31','2022-05-25'),('上げ','2022-06-02','2022-08-01'),('上げ','2022-08-22','2022-11-10'),('下げ','2022-11-10','2023-02-09'),('上げ','2023-04-17','2023-07-13'),('上げ','2023-08-02','2023-11-21'),('上げ','2024-03-21','2024-07-17'),('下げ','2024-07-17','2024-10-03'),('上げ','2024-10-03','2024-12-02'),('下げ','2025-01-22','2025-03-28'),('上げ','2025-09-22','2026-01-27')]
print('--- 大山13個(11-07 の表)のうち、山の中で竿元の玉が入ったか ---')
for k,a,b in YAMA:
    dd=1 if k=='上げ' else -1; q=t[(t.d==dd)&(t.ent>=a)&(t.ent<=b)]
    print(f"  {k} {a}〜{b}: " + (f"入った {len(q)}玉 {q.pips.sum():+,.0f}p(最初 {q.ent.min():%m/%d})" if len(q) else '竿元なし'))

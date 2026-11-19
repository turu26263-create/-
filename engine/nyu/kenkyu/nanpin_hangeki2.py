# 11-19 たくちん「ナンピン反撃」= 10-22 どんどんアセット/どんどん無限リーチの形にたくちんの段
# 1発目:今の決まった形のクジラの合図(買いは日足921の並びの時だけ)で、次の足の始値に0.01
# 足す:最後に足した値段から30p不利になるたびに、次の段(0.01→0.03→0.06→0.15→0.30)を足す
# 降り:かごの利益が1000円(10-22 と同じ)になったら全部(前の負けを取り戻す)/5発目の後さらに30p不利で全部切る
# 足の中で足すと降りるが両方届いたら、不利な方(足す・切る)を先。スプレッド0.3p。売り買いは別のかご
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']
srv = Market(load_cached(sys.argv[1]), 'server'); base = srv.feat('1h'); idx = base.index
O, H, L, C = base.o.values, base.h.values, base.l.values, base.c.values; n = len(idx)
DAN = [0.01, 0.03, 0.06, 0.15, 0.30]; STEP = 0.30; SPR = 0.003
YEN = float(sys.argv[2]) if len(sys.argv) > 2 else 1000.0   # かごの利益がこの円になったら全部降り(10-22 どんどん無限リーチと同じ1000円)
def kago(d):
    E = np.asarray(tai_entry(srv, '1D', '4h', '1h', d, f['sao'], f['n8'], kai_k9=f['kai_k9'], big21_up=f['big21_up'], narabi=f.get('narabi', False) and d > 0), bool)
    E &= ~yasumi_mask(idx)
    K = []; flo = np.zeros(n); i = 0
    while i < n - 1:
        if not E[i]: i += 1; continue
        j = i + 1; P = [O[j]]; Lt = [DAN[0]]; last = O[j]; why = None
        k = j
        while k < n:
            avg = np.dot(P, Lt) / sum(Lt)
            adv = (L[k] if d > 0 else H[k]); fav = (H[k] if d > 0 else L[k])
            # 不利が先:足す/切る
            while (d > 0 and adv <= last - STEP) or (d < 0 and adv >= last + STEP):
                if len(P) == len(DAN): x = last - d * STEP; why = '切り'; break
                last = last - d * STEP; P.append(last); Lt.append(DAN[len(P) - 1]); avg = np.dot(P, Lt) / sum(Lt)
            if why: break
            tgt = avg + d * (YEN / (sum(Lt) * 1000 * 100) + SPR)
            if (d > 0 and fav >= tgt) or (d < 0 and fav <= tgt):
                x = tgt; why = '取り戻し'; break
            flo[k] += sum(d * (C[k] - p) * 100 * l * 1000 for p, l in zip(P, Lt)) - SPR * 100 * sum(Lt) * 1000
            k += 1
        if why is None: break
        yen = sum(d * (x - p) * 100 * l * 1000 for p, l in zip(P, Lt)) - SPR * 100 * sum(Lt) * 1000
        K.append((idx[j], idx[k], d, len(P), max(Lt), yen, why)); i = k   # 降りた足から次の合図を見る
    return pd.DataFrame(K, columns=['ent', 'ext', 'd', '発', '一番大きい玉', '円', '降り']), flo
A, fa = kago(1); B, fb = kago(-1); T = pd.concat([A, B], ignore_index=True).sort_values('ext')
pos = {v: i for i, v in enumerate(idx)}; bal = np.full(n, 102000.0)
for _, r in T.iterrows(): bal[pos[r.ext]:] += r['円']
eq = bal + fa + fb; pk = np.maximum.accumulate(eq); dd = ((pk - eq) / pk).max() * 100
y = T.ext.dt.year
print(f"かご {len(T)}回 / 勝ち {int((T['円']>0).sum())} 負け {int((T['円']<=0).sum())} = かごの勝率 {100*(T['円']>0).mean():.1f}%")
print(f"最後の資金 {bal[-1]:,.0f}円(資金10.2万円) / 一番へこんだ資金 {eq.min():,.0f}円 / 落ち込み率 {dd:.1f}%")
print('買い', len(A), f"{A['円'].sum():+,.0f}円 / 売り", len(B), f"{B['円'].sum():+,.0f}円 / 降り", T['降り'].value_counts().to_dict())
print('何発まで足したか', T['発'].value_counts().sort_index().to_dict())
print('年ごと(円)', {int(a): int(round(v)) for a, v in T.groupby(y)['円'].sum().items()})
tm = ~y.between(2022, 2024); print(f"確かめる年 {T['円'][tm].sum():+,.0f}円 / 選22-24 {T['円'][~tm].sum():+,.0f}円")
w = T.loc[T['円'].idxmin()]; print('一番悪いかご', w.ent, '→', w.ext, f"{w['発']}発 {w['円']:+,.0f}円 {w['降り']}")

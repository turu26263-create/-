# 11-19 たくちん「ナンピン反撃 0,01/0,03/0,006/0,15/0,3 負けたら次のロッドにして前の負けとり戻す」【置き換え】
# 今の決まった形の玉に、ロットの段を当てる:0.01 → 0.03 → 0.06 → 0.15 → 0.30(0,006 は 0.06 と読んだ)
# 玉が負けて降りたら、次に入る玉は1段上。勝って降りたら0.01へ戻す。0.30で負けたら0.01へ戻す(段の上限)
# 段は決まった形の全部の玉で1本(降りた順に数え、入る時の段で入る)。資金10.2万円・レバレッジ2000・維持率20%で強制決済
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached(sys.argv[1]), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}
P = []
x, b = run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **NB); P.append(x.assign(d=1))
x, _ = run_tai(srv, '1D', '4h', '1h', -1, tuple(f['core_exit']), **KW); P.append(x.assign(d=-1))
x, _ = run_doten(srv, 1, xtf='4h', **KW); P.append(x.assign(d=1))
tz = f['tai']; x, _ = run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts']}); P.append(x.assign(d=1))
for d in (1, -1): x, _ = run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False)); P.append(x.assign(d=d))
t = pd.concat(P, ignore_index=True)
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
sh = pd.concat([run_shiawase(srv, d, yasumi=f.get('yasumi', False), shuu_muki=d in f['shiawase'].get('shuu_muki', []), **sz)[0].assign(d=d) for d in f['shiawase'].get('dirs', [1, -1])], ignore_index=True)
t = pd.concat([t, sh[sh.ent >= t.ent.min()]], ignore_index=True)
t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext); t = t.sort_values(['ent', 'ext']).reset_index(drop=True)
DAN = [0.01, 0.03, 0.06, 0.15, 0.30]
def lots(mode):
    if mode == 'kotei': return np.full(len(t), 0.01)
    ev = sorted([(r.ext, 1, i) for i, r in t.iterrows()] + [(r.ent, 0, i) for i, r in t.iterrows()], key=lambda z: (z[0], z[1]))  # 同じ時刻は入りを先(まだ結果が分からない)
    lv = 0; L = np.zeros(len(t))
    for _, kind, i in ev:
        if kind == 0: L[i] = DAN[lv]
        else: lv = 0 if (t.pips[i] > 0 or lv == len(DAN) - 1) else lv + 1
    return L
idx = b.index; C = b.c.values; pos = {v: i for i, v in enumerate(idx)}
def kekka(nm, L):
    yen = t.pips.values * L * 1000; bal = np.full(len(idx), float(k['資金'])); flo = np.zeros(len(idx)); mg = np.zeros(len(idx))
    for i in range(len(t)):
        a, z = pos[t.ent[i]], pos.get(t.ext[i], len(idx) - 1)
        flo[a:z] += t.d[i] * (C[a:z] - t.e[i]) * 100 * L[i] * 1000; mg[a:z] += L[i] * 100000 * C[a:z] / k['レバレッジ']; bal[z:] += yen[i]
    eq = bal + flo; pk = np.maximum.accumulate(eq); dd = ((pk - eq) / pk).max() * 100
    iji = np.where(mg > 0, eq / np.maximum(mg, 1e-9) * 100, np.inf); so = np.where(iji < k['強制決済の維持率'])[0]
    y = t.ext.dt.year; yy = pd.Series(yen).groupby(y.values).sum()
    print(f"\n{nm}: 最後の資金 {bal[-1]:,.0f}円 / 一番へこんだ資金 {eq.min():,.0f}円 / 落ち込み率 {dd:.1f}% / 証拠金維持率の一番低い {iji.min():,.0f}% / 強制決済 {'なし' if len(so)==0 else idx[so[0]]}")
    print('   年ごと(円)', {int(a): int(round(v)) for a, v in yy.items()})
    tm = ~pd.Series(y.values).between(2022, 2024); print(f"   確かめる年 {yen[tm.values].sum():+,.0f}円 / 選22-24 {yen[~tm.values].sum():+,.0f}円")
    return L, yen
print(f'玉 {len(t)}(今の決まった形・しあわせ入り)。勝ち {(t.pips>0).sum()} 負け {(t.pips<=0).sum()}')
kekka('今(0.01決め打ち)', lots('kotei'))
L, yen = kekka('ナンピン反撃(負けたら次の段)', lots('nanpin'))
print('   段ごとの玉数', {d: int((L == d).sum()) for d in DAN}, '/ 0.30で負けた回数', int(((L == 0.30) & (t.pips.values <= 0)).sum()))
w = int(np.argmin(yen)); print('   一番損した玉', t.ent[w], f"{L[w]}ロット {t.pips[w]:+.0f}p {yen[w]:+,.0f}円")
if len(sys.argv) > 2:   # 段の照らし:降りた順に、次に入った玉の段が決まりどおりか(11-19 食い違い0)
    lv = 0; bad = 0
    for _, kind, i in sorted([(r.ext, 1, i) for i, r in t.iterrows()] + [(r.ent, 0, i) for i, r in t.iterrows()], key=lambda z: (z[0], z[1])):
        if kind == 0: bad += L[i] != DAN[lv]
        else: lv = 0 if (t.pips[i] > 0 or lv == 4) else lv + 1
    print('段の食い違い', bad)

# 11-19 たくちん「許しいらんくない? もんが狭すぎる どれも最適化して バックテスト」:クジラ(と同じ入りの鯛・ドテンの元の売り)の門を1つずつ外す・広げる
# ミナデイン:1つずつ。2025で選び 2026・2021-24で確かめる。変わる玉30未満は決められない。0.01固定の円と落ち込み+7段の最後の資金
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); F0 = cfg['形']; k = cfg['口座']
srv = Market(load_cached('/home/user/data/mt4'), 'server')
_, B = run_tai(srv, '1D', '4h', '1h', 1, tuple(F0['core_exit']), maxpos=1)
def build(o):
    f = F0; mon = o.get('mon')
    KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=o.get('sao', f['sao']), reenter=True, tp=('4h', f['tp'][1]), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']),
              kai_k9=f['kai_k9'], big21_up=o.get('big21_up', f['big21_up']), yasumi=f['yasumi'], kawa_chi=o.get('kawa_chi', True), mon=mon)
    NB = {**KW, 'narabi': o.get('narabi', f['narabi'])}; rv = f['rev_maxpos']; tz = f['tai']
    P = [run_kujira(srv, 1, tuple(f['core_exit']), rev_maxpos=rv, **NB)[0].assign(d=1, bu='クジラ買い'),
         run_kujira(srv, -1, tuple(f['core_exit']), rev_maxpos=rv, **KW)[0].assign(d=-1, bu='クジラ売り'),
         run_doten(srv, 1, xtf='4h', rev_maxpos=rv, doten_maxpos=f['doten'].get('maxpos', 1), **KW)[0].assign(d=1, bu='ドテン'),
         run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': tz.get('maxpos', 1), 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(tz['ng_hours'])})[0].assign(d=1, bu='鯛')]
    for d in (1, -1): P.append(run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f['yasumi'])[0].assign(d=d, bu='押し目'))
    t = pd.concat(P, ignore_index=True)
    sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
    SH = pd.concat([run_shiawase(srv, d, yasumi=True, shuu_muki=d in f['shiawase']['shuu_muki'], **sz)[0].assign(d=d, bu='しあわせ') for d in f['shiawase']['dirs']], ignore_index=True)
    t = pd.concat([t, SH[SH.ent >= t.ent.min()]], ignore_index=True); t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext)
    return t.sort_values(['ent', 'ext']).reset_index(drop=True)
def hyou(t):
    T, s = lot_sizing(t, B, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
    y = pd.to_datetime(T.ent).dt.year; Y = T['円']; q = T.bu.str.startswith('クジラ')
    return dict(玉=len(T), クジラ=int(q.sum()), クジラp=int(T.loc[q, 'p'].sum()) if 'p' in T else 0, y2025=int(Y[y == 2025].sum()), y2026=int(Y[y == 2026].sum()), y2124=int(Y[y.between(2021, 2024)].sum()), 全期間=int(Y.sum()), 落ち込み=s['落ち込み率'])
DAN = [0.01, 0.03, 0.06, 0.15, 0.30, 0.60, 1.20]
def nana(t):
    t = t.reset_index(drop=True); ev = sorted([(r.ext, 1, i) for i, r in t.iterrows()] + [(r.ent, 0, i) for i, r in t.iterrows()], key=lambda z: (z[0], z[1]))
    lv = 0; L = np.zeros(len(t))
    for _, kd, i in ev:
        if kd == 0: L[i] = DAN[lv]
        else: lv = 0 if t.pips[i] > 0 else min(lv + 1, 6)
    idx = B.index; C = B.c.values; pos = {v: i for i, v in enumerate(idx)}
    bal = np.full(len(idx), float(k['資金'])); flo = np.zeros(len(idx)); mg = np.zeros(len(idx))
    for i in range(len(t)):
        a, z = pos[t.ent[i]], pos.get(t.ext[i], len(idx) - 1); y = t.pips[i] * L[i] * 1000
        flo[a:z] += t.d[i] * (C[a:z] - t.e[i]) * 100 * L[i] * 1000; mg[a:z] += L[i] * 100000 * C[a:z] / k['レバレッジ']; bal[z:] += y
    eq = bal + flo; dd = ((np.maximum.accumulate(eq) - eq) / np.maximum.accumulate(eq)).max() * 100
    iji = np.where(mg > 0, eq / np.maximum(mg, 1e-9) * 100, np.inf)
    w = (t.sort_values('ext').pips.values > 0); r = m = 0
    for v in w: r = 0 if v else r + 1; m = max(m, r)
    return dict(七段=int(bal[-1]), 七段落ち=round(dd, 1), 強制=('あり' if (iji < k['強制決済の維持率']).any() else 'なし'), 最大連敗=m, 勝率=round(w.mean() * 100, 1))
def key(t): return set(zip(t.ent.astype(str), t.bu, t.e.round(3)))
M = lambda **a: {'mon': a}
CASES = [('今', {}),
         ('B許しを外す', M(kai=False)),
         ('許しの日足21(qq)を外す', M(qq=False)),
         ('日足9+4h21(perm)を外す', M(perm=False)),
         ('遅行21(chi)を外す', M(chi=False)),
         ('川を外す(kawa 0σ)', M(kawa=0.0)), ('川 0.25σ', M(kawa=0.25)), ('川 0.5σ', M(kawa=0.5)), ('川 0.6σ', M(kawa=0.6)), ('川 0.75σ', M(kawa=0.75)), ('川 0.9σ', M(kawa=0.9)), ('川 1.25σ', M(kawa=1.25)),
         ('川と遅行を両方外す', {'kawa_chi': False}),
         ('竿先 2.5σ', {'sao': 2.5}), ('竿先 3σ', {'sao': 3.0}), ('竿先を外す', {'sao': 99.0}), ('竿先 2.25σ', {'sao': 2.25}), ('竿先 2.75σ', {'sao': 2.75}), ('竿先 1.8σ', {'sao': 1.8}),
         ('日足21の傾きを外す', {'big21_up': False}),
         ('買いの日足921並びを外す', {'narabi': False}),
         ('(重ね)川0.5σ+竿先を外す', {'mon': dict(kawa=0.5), 'sao': 99.0}), ('(重ね)川0.75σ+竿先2.5σ', {'mon': dict(kawa=0.75), 'sao': 2.5})]
base_t = build({}); BK = key(base_t); rows = []
for name, o in CASES:
    t = base_t if not o else build(o); h = hyou(t)
    n7 = lot_sizing(t, B, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=None, stopout=k['強制決済の維持率'], nanpin=True) if False else None
    rows.append(dict(門=name, 変わる玉=len(key(t) ^ BK), **h, **nana(t)))
R = pd.DataFrame(rows); pd.set_option('display.width', 250); print(R.to_string(index=False))
b = R.iloc[0]
print('\n■ 判定(2025・2026・2021-24・全期間が全部今以上、落ち込み+0.5まで、変わる玉30以上)')
for _, r in R.iloc[1:].iterrows():
    ok = r.y2025 > b.y2025 and r.y2026 >= b.y2026 and r.y2124 > b.y2124 and r.全期間 > b.全期間 and r.落ち込み <= b.落ち込み + 0.5
    print(f"{r.門}: {'○' if ok and r.変わる玉 >= 30 else ('△決められない(30未満)' if ok else '×')}  全期間 {r.全期間 - b.全期間:+,}円 / 2025 {r.y2025 - b.y2025:+,} / 2026 {r.y2026 - b.y2026:+,} / 21-24 {r.y2124 - b.y2124:+,} / 落ち込み {r.落ち込み}%")

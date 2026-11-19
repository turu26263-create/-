# 11-19 ミナデイン検証役:v4 の2つの決まりを ミナデインの決まり(2025で動かし 2026 と 2021〜24 で確かめる・30玉未満は決められない)で判定
# と、EA と研究台のずれの大きさ(週足・日足200 の EMA の始まり方)を数える
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']
srv = Market(load_cached('/home/user/data/mt4'), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}; tz = f['tai']
def per(t):
    y = pd.to_datetime(t.ent).dt.year; p = t.pips * 10   # 0.01ロットの円
    return {'2025': round(p[y == 2025].sum()), '2026': round(p[y == 2026].sum()), '2021-24': round(p[y.between(2021, 2024)].sum()), '全部': round(p.sum()), '玉': len(t)}
print('■ 鯛のNY外し(約定16〜23時)')
a, _ = run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts']})
b, _ = run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(tz['ng_hours'])})
pa, pb = per(a), per(b); print('  外す前', pa); print('  外した後', pb); print('  差', {k: pb[k] - pa[k] for k in pa})
print('■ クジラの週足逆の枠(上限なし)')
def kuj(rv): return pd.concat([run_kujira(srv, 1, tuple(f['core_exit']), rev_maxpos=rv, **NB)[0], run_kujira(srv, -1, tuple(f['core_exit']), rev_maxpos=rv, **KW)[0]], ignore_index=True)
def dot(rv): return run_doten(srv, 1, xtf='4h', rev_maxpos=rv, **KW)[0]
k3, k4 = per(kuj(None)), per(kuj(99)); d3, d4 = per(dot(None)), per(dot(99))
print('  クジラ v3', k3); print('  クジラ v4', k4); print('  ドテン v3', d3); print('  ドテン v4', d4)
print('  差(クジラ+ドテン)', {k: (k4[k] + d4[k]) - (k3[k] + d3[k]) for k in k3})
# EMA の始まり方:データの最初で種をまいた EMA と、1年あとで種をまいた EMA の向き(9>21・終値>200)の食い違い
print('■ EMA の始まり方のずれ(研究台はデータの最初 2016/03 で種をまく。MT4 は手前の足から計算するので違いうる)')
raw = srv.raw; AG = dict(o='first', h='max', l='min', c='last')
W = raw.resample('W-MON', label='left', closed='left').agg(AG).dropna(); D = raw.resample('1D').agg(AG).dropna()
def ema(c, n): return c.ewm(span=n, adjust=False).mean()
for nm, B, cut in [('週足 9>21', W, '2017-03-13'), ('日足 9>21', D, '2017-03-13')]:
    full = ema(B.c, 9) > ema(B.c, 21); late = ema(B.c[cut:], 9) > ema(B.c[cut:], 21)
    j = full[cut:]; df = (j != late)
    print(f'  {nm}:種を1年ずらすと、向きが違う足 {int(df.sum())}/{len(df)}。最後に違ったのは {df[df].index.max() if df.any() else "なし"}')
full = ema(D.c, 200); late = ema(D.c['2017-03-13':], 200); x = (full['2017-03-13':] - late).abs()
print(f'  日足200:種を1年ずらすと、差 {x.iloc[0]:.3f}円→1年後 {x.iloc[min(250, len(x)-1)]:.3f}円→2年後 {x.iloc[min(500, len(x)-1)]:.3f}円(しあわせの「200の上下1σ」と「週足219」に効く)')

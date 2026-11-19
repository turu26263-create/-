# 11-19 たくちん「カウンター反撃いれて 無限リーチとナンピンのかけあわせで最適化検証」
# ミナデインの進め方:【置き換え】を1つずつ動かす(全部のかけ合わせはしない)。決め方は 落ち込み・強制決済・選22-24・確かめる年。
# 動かす物:①無限リーチ=クジラの最大発数(今5) ②カウンター反撃を掛ける部品(全部/当たる部品だけ) ③資金(段の重さに耐える資金)
# 7段(0.01/0.03/0.06/0.15/0.3/0.6/1.2・負けで1段上げ・1.2で止める・勝ちで0.01)はたくちんの固定なので動かさない
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached('/home/user/data/mt4'), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}
DAN = [0.01, 0.03, 0.06, 0.15, 0.30, 0.60, 1.20]
base_parts = []
x, _ = run_doten(srv, 1, xtf='4h', **KW); base_parts.append(x.assign(d=1, bu='ドテン買い'))
tz = f['tai']; x, _ = run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts']}); base_parts.append(x.assign(d=1, bu='鯛'))
for d in (1, -1): x, _ = run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False)); base_parts.append(x.assign(d=d, bu='押し目'))
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
SH = pd.concat([run_shiawase(srv, d, yasumi=f.get('yasumi', False), shuu_muki=d in f['shiawase'].get('shuu_muki', []), **sz)[0].assign(d=d, bu='しあわせ') for d in f['shiawase'].get('dirs', [1, -1])], ignore_index=True)
_, B = run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **NB); idx = B.index; C = B.c.values; pos = {v: i for i, v in enumerate(idx)}
def tama(M):
    P = [run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **{**NB, 'maxpos': M})[0].assign(d=1, bu='クジラ買い'),
         run_tai(srv, '1D', '4h', '1h', -1, tuple(f['core_exit']), **{**KW, 'maxpos': M})[0].assign(d=-1, bu='クジラ売り')] + base_parts
    t = pd.concat(P, ignore_index=True); t = pd.concat([t, SH[SH.ent >= t.ent.min()]], ignore_index=True)
    t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext); return t.sort_values(['ent', 'ext']).reset_index(drop=True)
def lots(t, mode):
    if mode == '0.01固定': return np.full(len(t), 0.01)
    on = np.ones(len(t), bool) if mode == '全部' else t.bu.isin(['ドテン買い', 'クジラ買い']).values
    ev = sorted([(t.ext[i], 1, i) for i in range(len(t)) if on[i]] + [(t.ent[i], 0, i) for i in range(len(t)) if on[i]], key=lambda z: (z[0], z[1]))
    lv = 0; L = np.full(len(t), 0.01)
    for _, kind, i in ev:
        if kind == 0: L[i] = DAN[lv]
        else: lv = 0 if t.pips[i] > 0 else min(lv + 1, 6)
    return L
def kane(t, L, shikin):
    yen = t.pips.values * L * 1000; bal = np.full(len(idx), float(shikin)); flo = np.zeros(len(idx)); mg = np.zeros(len(idx))
    for i in range(len(t)):
        a, z = pos[t.ent[i]], pos.get(t.ext[i], len(idx) - 1)
        flo[a:z] += t.d[i] * (C[a:z] - t.e[i]) * 100 * L[i] * 1000; mg[a:z] += L[i] * 100000 * C[a:z] / k['レバレッジ']; bal[z:] += yen[i]
    eq = bal + flo; pk = np.maximum.accumulate(eq); dd = ((pk - eq) / pk).max() * 100
    iji = np.where(mg > 0, eq / np.maximum(mg, 1e-9) * 100, np.inf); so = np.where(iji < k['強制決済の維持率'])[0]
    y = t.ent.dt.year.values; sel = (y >= 2022) & (y <= 2024)
    return dict(玉=len(t), 最後の資金=int(bal[-1]), 落ち込み=round(dd, 1), 一番へこんだ=int(eq.min()), 強制決済=str(idx[so[0]])[:10] if len(so) else 'なし',
                選22_24=int(yen[sel].sum()), 確かめる年=int(yen[~sel].sum()), 負けた年=','.join(str(a) for a, v in pd.Series(yen).groupby(y).sum().items() if v < 0) or 'なし')
pd.set_option('display.width', 250); rows = []
T = {M: tama(M) for M in (3, 4, 5, 6, 8, 99)}
print('① 無限リーチ:クジラの最大発数(ほかは今のまま)。資金100万円')
for M, t in T.items():
    for mode in ('0.01固定', '全部'): rows.append(dict(調べ='①発数', 発数=M, 段='段なし' if mode == '0.01固定' else '7段 全部', 資金=1000000, **kane(t, lots(t, mode), 1000000)))
print('② カウンター反撃を掛ける部品(発数5)・資金100万円')
for mode in ('全部', '当たる部品だけ'): rows.append(dict(調べ='②掛ける部品', 発数=5, 段='7段 ' + mode, 資金=1000000, **kane(T[5], lots(T[5], mode), 1000000)))
print('③ 資金(発数5・7段 全部)')
for sk in (102000, 300000, 500000, 1000000, 2000000, 3000000):
    rows.append(dict(調べ='③資金', 発数=5, 段='7段 全部', 資金=sk, **kane(T[5], lots(T[5], '全部'), sk)))
R = pd.DataFrame(rows); print(R.to_string(index=False))
R.to_csv('/home/user/-/engine/kekka_tai/nyu/最適化_カウンター反撃x無限リーチ_20261119.csv', index=False)

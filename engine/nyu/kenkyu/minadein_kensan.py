# 11-19 たくちん「ミナデインやで」:研鑽役。決まった形(v4)の【置き換え】の数字を1つずつ前後に動かす(かけ合わせはしない)
# 決め方:2025で動かし、2026と2021〜24で確かめる。台地の真ん中。変わる玉30未満は決められない。0.01固定の円と落ち込みで見る
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); F0 = cfg['形']; k = cfg['口座']
srv = Market(load_cached('/home/user/data/mt4'), 'server')
_, B = run_tai(srv, '1D', '4h', '1h', 1, tuple(F0['core_exit']), maxpos=1)
def build(o):
    f = json.loads(json.dumps(F0)); g = lambda key, dv: o.get(key, dv)
    KW = dict(maxpos=g('maxpos', f['maxpos']), n8=f['n8'], sao=g('sao', f['sao']), reenter=True, tp=('4h', g('tp', f['tp'][1])), ts=g('ts', f['ts']),
              avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=g('kai_k9', f['kai_k9']), big21_up=f['big21_up'], yasumi=f['yasumi'])
    NB = {**KW, 'narabi': f['narabi']}; rv = g('rev_maxpos', f['rev_maxpos']); tz = f['tai']
    P = [run_kujira(srv, 1, tuple(f['core_exit']), rev_maxpos=rv, **NB)[0].assign(d=1, bu='クジラ買い'),
         run_kujira(srv, -1, tuple(f['core_exit']), rev_maxpos=rv, **KW)[0].assign(d=-1, bu='クジラ売り'),
         run_doten(srv, 1, xtf='4h', rev_maxpos=rv, **KW)[0].assign(d=1, bu='ドテン'),
         run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(range(g('ng', 16), 24))})[0].assign(d=1, bu='鯛')]
    for d in (1, -1): P.append(run_oshime_d(srv, d, maxpos=g('o_maxpos', f['oshime']['maxpos']), tpk=g('o_tpk', 3.5), yasumi=f['yasumi'])[0].assign(d=d, bu='押し目'))
    t = pd.concat(P, ignore_index=True)
    sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
    for a, b in (('nflip', 's_nflip'), ('win', 's_win'), ('tpk', 's_tpk'), ('tamek', 's_tamek'), ('naka', 's_naka')): sz[a] = g(b, sz[a])
    SH = pd.concat([run_shiawase(srv, d, yasumi=True, shuu_muki=d in f['shiawase']['shuu_muki'], **sz)[0].assign(d=d, bu='しあわせ') for d in f['shiawase']['dirs']], ignore_index=True)
    t = pd.concat([t, SH[SH.ent >= t.ent.min()]], ignore_index=True); t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext)
    return t.sort_values(['ent', 'ext']).reset_index(drop=True)
def hyou(t):
    T, s = lot_sizing(t, B, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
    y = pd.to_datetime(T.ent).dt.year; Y = T['円']
    return dict(玉=len(T), y2025=int(Y[y == 2025].sum()), y2026=int(Y[y == 2026].sum()), y2124=int(Y[y.between(2021, 2024)].sum()), 全期間=int(Y.sum()), 落ち込み=s['落ち込み率'])
def key(t): return set(zip(t.ent.astype(str), t.bu, t.e.round(3)))
base_t = build({}); BASE = hyou(base_t); BK = key(base_t)
GRID = {'sao': [1.8, 1.9, 2.0, 2.1, 2.2], 'tp': [3.5, 3.75, 4.0, 4.25, 4.5], 'ts': [450, 500, 550, 600, 650], 'kai_k9': [1, 2, 3, 4, 5], 'maxpos': [3, 4, 5, 6, 8],
        'rev_maxpos': [5, 8, 12, 20, 99], 'ng': [14, 15, 16, 17, 18], 'o_tpk': [3.0, 3.25, 3.5, 3.75, 4.0], 'o_maxpos': [3, 4, 5, 6, 8],
        's_nflip': [2, 3, 4], 's_win': [20, 25, 30, 35, 40], 's_tpk': [1.5, 1.75, 2.0, 2.25, 2.5], 's_tamek': [3.0, 3.25, 3.5, 3.75, 4.0], 's_naka': [0.5, 0.75, 1.0, 1.25, 1.5]}
NOW = {'sao': 2.0, 'tp': 4.0, 'ts': 550, 'kai_k9': 3, 'maxpos': 5, 'rev_maxpos': 99, 'ng': 16, 'o_tpk': 3.5, 'o_maxpos': 5, 's_nflip': 3, 's_win': 30, 's_tpk': 2.0, 's_tamek': 3.5, 's_naka': 1.0}
rows = []
for p, vals in GRID.items():
    for v in vals:
        t = base_t if v == NOW[p] else build({p: v}); h = hyou(t); kk = key(t)
        rows.append(dict(数字=p, 値=v, 今=('←今' if v == NOW[p] else ''), 変わる玉=len(kk ^ BK), **h))
R = pd.DataFrame(rows); pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
print('基準(今):', BASE); print(R.to_string(index=False))
# 判定:今より 2025・2026・2021-24・全期間 の全部で上、落ち込みが +0.5 以上悪くならない、変わる玉30以上、両隣も今より全期間で下がらない(台地)
print('\n■ 判定')
for p, vals in GRID.items():
    z = R[R.数字 == p].reset_index(drop=True); i0 = z.index[z.今 == '←今'][0]; cand = []
    for i, r in z.iterrows():
        if i == i0: continue
        up = r.y2025 > BASE['y2025'] and r.y2026 >= BASE['y2026'] and r.y2124 > BASE['y2124'] and r.全期間 > BASE['全期間'] and r.落ち込み <= BASE['落ち込み'] + 0.5
        nb = [z.loc[j, '全期間'] for j in (i - 1, i + 1) if 0 <= j < len(z) and j != i0]
        plateau = all(x >= BASE['全期間'] for x in nb)
        if up: cand.append(f"{r.値}(変わる玉{r.変わる玉}{'・30未満=決められない' if r.変わる玉 < 30 else ''}{'・台地' if plateau else '・尖り'})")
    nbr = [z.loc[j, '全期間'] for j in (i0 - 1, i0 + 1) if 0 <= j < len(z)]
    on = '台地の上' if all(abs(x - BASE['全期間']) <= 0.05 * abs(BASE['全期間']) or x <= BASE['全期間'] for x in nbr) else '端(隣の方が高い)'
    print(f'{p}: 今={NOW[p]} {on} / 候補: {", ".join(cand) if cand else "なし"}')

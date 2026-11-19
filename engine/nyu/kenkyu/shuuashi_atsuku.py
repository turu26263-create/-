# 11-19 たくちん「ご」:クジラを週足が逆向き(週足の9と21の並びが入る向きと逆)の時に厚くする形を照らす(決まりにはしていない)
# 厚く=週足逆の入りだけ発数を増やす(週足同じ向きは5発のまま)/薄く=週足同じ向きの発数を減らす。プールを分けて回す【置き換え】
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached('/home/user/data/mt4'), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}; tz = f['tai']
H = srv.feat('1h'); idx = H.index
W = srv.raw.resample('W-MON', label='left', closed='left').agg(dict(o='first', h='max', l='min', c='last')).dropna(); W['k'] = W.index + pd.Timedelta('7D')
W['up'] = W.c.ewm(span=9, adjust=False).mean() > W.c.ewm(span=21, adjust=False).mean()
wi = np.searchsorted(W.k.values, (idx + pd.Timedelta('1h')).values, side='right') - 1
wup = np.where(wi >= 0, W.up.values[np.clip(wi, 0, None)], False).astype(bool)
oth = [run_doten(srv, 1, xtf='4h', **KW)[0].assign(d=1), run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(tz.get('ng_hours', ()))})[0].assign(d=1)]
for d in (1, -1): oth.append(run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False))[0].assign(d=d))
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
SH = pd.concat([run_shiawase(srv, d, yasumi=True, shuu_muki=d in f['shiawase'].get('shuu_muki', []), **sz)[0].assign(d=d) for d in f['shiawase']['dirs']], ignore_index=True)
_, B = run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **NB)
DAN = [0.01, 0.03, 0.06, 0.15, 0.30, 0.60, 1.20]
def kuj(m_same, m_rev):
    P = []
    for d in (1, -1):
        kw = NB if d > 0 else KW; same = wup if d > 0 else ~wup
        if m_same == m_rev: P.append(run_tai(srv, '1D', '4h', '1h', d, tuple(f['core_exit']), **{**kw, 'maxpos': m_same})[0].assign(d=d)); continue
        if m_same: P.append(run_tai(srv, '1D', '4h', '1h', d, tuple(f['core_exit']), **{**kw, 'maxpos': m_same, 'e_mask': same})[0].assign(d=d))
        if m_rev: P.append(run_tai(srv, '1D', '4h', '1h', d, tuple(f['core_exit']), **{**kw, 'maxpos': m_rev, 'e_mask': ~same})[0].assign(d=d))
    t = pd.concat(P + oth, ignore_index=True); t = pd.concat([t, SH[SH.ent >= t.ent.min()]], ignore_index=True)
    t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext); t = t.sort_values(['ent', 'ext']).reset_index(drop=True); return t
def hyou(nm, t):
    T, s = lot_sizing(t, B, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
    y = pd.to_datetime(T.ent).dt.year; sel = y.between(2022, 2024)
    lv = 0; L = np.zeros(len(t))
    for _, kd, i in sorted([(t.ext[i], 1, i) for i in range(len(t))] + [(t.ent[i], 0, i) for i in range(len(t))], key=lambda z: (z[0], z[1])):
        if kd == 0: L[i] = DAN[lv]
        else: lv = 0 if t.pips[i] > 0 else min(lv + 1, 6)
    yen = t.pips.values * L * 1000; s7 = t.ent.dt.year.between(2022, 2024).values
    return dict(形=nm, 玉=len(t), 合計p=round(t.pips.sum()), 最後の資金=s['最後の資金'], 落ち込み=s['落ち込み率'], 選円=int(T['円'][sel].sum()), 確円=int(T['円'][~sel].sum()),
                負けた年=','.join(str(a) for a, v in T.groupby(y)['円'].sum().items() if v < 0) or 'なし', 七段_選円=int(yen[s7].sum()), 七段_確円=int(yen[~s7].sum()))
R = [hyou('今(5発・鯛NYなし)', kuj(5, 5)), hyou('週足逆だけ上限なし', kuj(5, 99)), hyou('週足逆だけ8発', kuj(5, 8)),
     hyou('週足同じ向きは3発', kuj(3, 5)), hyou('週足同じ向きは3発・逆は上限なし', kuj(3, 99)), hyou('週足同じ向きは入らない', kuj(0, 5))]
pd.set_option('display.width', 250); print(pd.DataFrame(R).to_string(index=False))

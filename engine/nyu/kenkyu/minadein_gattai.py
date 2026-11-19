# 11-19 ミナデイン 研鑽役(合体):v4 の部品の入/切 512通り(数字は動かさない)
import sys, json, itertools, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached('/home/user/data/mt4'), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}; tz = f['tai']; R = f.get('rev_maxpos')
P = {}
for rv in (True, False):
    P[('KB', rv)] = run_kujira(srv, 1, tuple(f['core_exit']), rev_maxpos=R if rv else None, **NB)[0].assign(d=1)
    P[('KS', rv)] = run_kujira(srv, -1, tuple(f['core_exit']), rev_maxpos=R if rv else None, **KW)[0].assign(d=-1)
    P[('DT', rv)] = run_doten(srv, 1, xtf='4h', rev_maxpos=R if rv else None, **KW)[0].assign(d=1)
P['TAI'] = run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(tz.get('ng_hours', ()))})[0].assign(d=1)
P['OB'] = run_oshime_d(srv, 1, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False))[0].assign(d=1)
P['OS'] = run_oshime_d(srv, -1, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False))[0].assign(d=-1)
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
start = pd.concat([P[('KB', True)], P[('KS', True)], P[('DT', True)], P['TAI'], P['OB'], P['OS']]).ent.min()
for d, nm in ((1, 'SB'), (-1, 'SS')):
    x = run_shiawase(srv, d, yasumi=True, shuu_muki=d in f['shiawase']['shuu_muki'], **sz)[0].assign(d=d); P[nm] = x[x.ent >= start]
_, B = run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **NB); idx = B.index; C = B.c.values; pos = {v: i for i, v in enumerate(idx)}; n = len(idx)
YR = idx.year.values
def kaku(t, L=None):   # 1つの部品の 確定の円(足ごとの足し上げ前)と含み
    t = t.reset_index(drop=True); L = np.full(len(t), 0.01) if L is None else L
    real = np.zeros(n); flo = np.zeros(n)
    for i in range(len(t)):
        a, z = pos[pd.Timestamp(t.ent[i])], pos.get(pd.Timestamp(t.ext[i]), n - 1)
        flo[a:z] += t.d[i] * (C[a:z] - t.e[i]) * 100 * L[i] * 1000; real[z] += t.pips[i] * L[i] * 1000
    return real, flo
A = {key: kaku(t) for key, t in P.items()}
NAMES = ['クジラ買い', 'クジラ売り', '週足逆の枠', 'ドテン', '鯛', '押し目買い', '押し目売り', 'しあわせ買い', 'しあわせ売り']
def parts(c):
    kb, ks, rv, dt, ta, ob, os_, sb, ss = c; L = []
    if kb: L.append(('KB', rv))
    if ks: L.append(('KS', rv))
    if ks and dt: L.append(('DT', rv))
    for on, key in ((ta, 'TAI'), (ob, 'OB'), (os_, 'OS'), (sb, 'SB'), (ss, 'SS')):
        if on: L.append(key)
    return L
rows = []
for c in itertools.product((1, 0), repeat=9):
    if not c[1] and c[3]: continue          # ドテンはクジラ売りが無いと出ない(同じ組になるので外す)
    if not (c[0] or c[1]) and not c[2]: continue   # クジラが無い時の週足逆の枠は意味がない
    L = parts(c)
    if not L: continue
    real = sum(A[x][0] for x in L); flo = sum(A[x][1] for x in L)
    bal = k['資金'] + np.cumsum(real); eq = bal + flo; pk = np.maximum.accumulate(eq); ddy = (pk - eq).max(); dd = ((pk - eq) / pk).max() * 100
    yy = pd.Series(real).groupby(YR).sum()
    g = lambda ys: float(yy[[y for y in ys if y in yy.index]].sum())
    rows.append(dict(組=''.join('●' if v else '・' for v in c), 最後=int(bal[-1]), 損益=int(bal[-1] - k['資金']), 落ち込み=round(dd, 1), 落ち込み円=int(ddy),
                     損益割る落ち込み=round((bal[-1] - k['資金']) / max(ddy, 1), 2), y2025=int(g([2025])), y2026=int(g([2026])), y21_24=int(g(range(2021, 2025))),
                     選22_24=int(g(range(2022, 2025))), 確かめる年=int(g([y for y in yy.index if not 2022 <= y <= 2024])), 負けた年=','.join(str(a) for a, v in yy.items() if v < 0) or 'なし', c=c))
D = pd.DataFrame(rows); print('組の数', len(D), ' 並び:', ' '.join(NAMES))
ima = (1,) * 9; D['今'] = D.c.apply(lambda c: c == ima)
for col in ['最後', '損益割る落ち込み', 'y2025', 'y2026', 'y21_24', '選22_24', '確かめる年']: D['順_' + col] = D[col].rank(ascending=False, method='min').astype(int)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40)
show = ['組', '最後', '落ち込み', '損益割る落ち込み', 'y2025', 'y2026', 'y21_24', '選22_24', '確かめる年', '負けた年', '順_最後', '順_損益割る落ち込み', '順_y2025', '順_y2026', '順_y21_24', '順_選22_24', '順_確かめる年']
print('\n■ 一番取れる組(最後の資金)上位10'); print(D.sort_values('最後', ascending=False).head(10)[show].to_string(index=False))
print('\n■ 損益÷落ち込み(円)上位10'); print(D.sort_values('損益割る落ち込み', ascending=False).head(10)[show].to_string(index=False))
print('\n■ 今の形(全部入り)'); print(D[D.今][show].to_string(index=False))
b25 = D.sort_values('y2025', ascending=False).head(5)
print('\n■ 2025で選んだ上位5 → 2026・2021〜24での順位'); print(b25[show].to_string(index=False))
# 7段(参考)
DAN = [0.01, 0.03, 0.06, 0.15, 0.30, 0.60, 1.20]
def nana(c):
    t = pd.concat([P[x] for x in parts(c)], ignore_index=True); t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext); t = t.sort_values(['ent', 'ext']).reset_index(drop=True)
    lv = 0; L = np.zeros(len(t))
    for _, kd, i in sorted([(t.ext[i], 1, i) for i in range(len(t))] + [(t.ent[i], 0, i) for i in range(len(t))], key=lambda z: (z[0], z[1])):
        if kd == 0: L[i] = DAN[lv]
        else: lv = 0 if t.pips[i] > 0 else min(lv + 1, 6)
    real, flo = kaku(t, L); bal = k['資金'] + np.cumsum(real); eq = bal + flo; pk = np.maximum.accumulate(eq); dd = ((pk - eq) / pk).max() * 100
    yy = pd.Series(real).groupby(YR).sum()
    return dict(玉=len(t), 最後=int(bal[-1]), 落ち込み=round(dd, 1), 負けた年=','.join(str(a) for a, v in yy.items() if v < 0) or 'なし')
c1 = D.sort_values('最後', ascending=False).iloc[0].c; c2 = D.sort_values('損益割る落ち込み', ascending=False).iloc[0].c
print('\n■ カウンター反撃7段(参考・段の並びの見かけに注意)')
for nm, c in (('今の形', ima), ('一番取れる組', c1), ('損益÷落ち込み一番の組', c2)):
    print(nm, ''.join('●' if v else '・' for v in c), nana(c))

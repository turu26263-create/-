# 11-19 たくちん「入り口出口確定までやる 5つの局面全部やって」
# 今の決まった形の5部品(クジラ買い売り・ドテン買い・鯛・押し目・しあわせ)を、エンジンの部品を1つも使わずに
# CSV から足を作り直し、入口から出口が確定するまで1本ずつ歩いて玉を作り直す(別の目)。
# エンジンの玉と1つずつ(入った足・入り値・降りた足・降り値・降りた理由)合わせ、入った所を5つの局面で分ける。
# 5つの局面【置き換え】=合図の1時間足の21の角度を向きに合わせた値:逆向き(0以下)/レンジ(0〜10)/起き始め(10〜30)/巡航(30〜55)/竿先(55超)
import sys, json, warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
D_ = sys.argv[1] if len(sys.argv) > 1 else '/home/user/data/mt4'
SPR = 0.003; P = 0.01

# ====================================================== 別の目:足と線(エンジンの部品は使わない)
r = pd.read_csv(f'{D_}/USDJPY60.csv', header=None, names=['d', 't', 'o', 'h', 'l', 'c', 'v'])
r.index = pd.to_datetime(r.d + ' ' + r.t, format='%Y.%m.%d %H:%M'); RAW = r[['o', 'h', 'l', 'c']].astype(float)
AG = dict(o='first', h='max', l='min', c='last')
def sen(b, ln):
    b = b.copy(); c = b.c
    b['e9'] = c.ewm(span=9, adjust=False).mean(); b['e21'] = c.ewm(span=21, adjust=False).mean(); b['e200'] = c.ewm(span=200, adjust=False).mean()
    b['md'] = c.rolling(20).mean(); b['sd'] = c.rolling(20).std(ddof=0)
    rng = b.h.rolling(150).max() - b.l.rolling(150).min(); b['ang'] = np.degrees(np.arctan2((b.e21 - b.e21.shift(3)) / rng * 500, 18))
    b['k'] = b.index + pd.Timedelta(ln); return b
H1 = sen(RAW, '1h'); H4 = sen(RAW.resample('4h').agg(AG).dropna(), '4h'); D1 = sen(RAW.resample('1D').agg(AG).dropna(), '1D')
idx = H1.index; n = len(idx); O, Hh, Ll, C = (H1[c].values for c in 'ohlc'); hr = idx.hour.values
K1 = H1.k.values
def ue(B):   # 1時間足 i が閉じた時に、もう閉じている上の足の行番号(無ければ -1)
    return np.searchsorted(B.k.values, K1, side='right') - 1
di = ue(D1); fi = ue(H4)
def col(B, ix, c):
    v = B[c].values; out = np.full(n, np.nan); ok = ix >= 0; out[ok] = v[ix[ok]]; return out
dc, de9, de21, dmd, dsd, dang, dk = (col(D1, di, c) for c in ['c', 'e9', 'e21', 'md', 'sd', 'ang', 'k'])
dk = np.where(di >= 0, D1.k.values[np.clip(di, 0, None)], np.datetime64('NaT')).astype('datetime64[ns]')
fc, fe9, fe21, fmd, fsd = (col(H4, fi, c) for c in ['c', 'e9', 'e21', 'md', 'sd'])
fk = np.where(fi >= 0, H4.k.values[np.clip(fi, 0, None)], np.datetime64('NaT')).astype('datetime64[ns]')
e9, e21, md, sd, ang1 = (H1[c].values for c in ['e9', 'e21', 'md', 'sd', 'ang'])
h21 = H1.h.shift(21).values; l21 = H1.l.shift(21).values
T = idx.values
def mae1(v): v = np.asarray(v, float); return np.r_[np.nan, v[:-1]]     # 足の中で使う線=1本前が閉じた時の値
nxh = np.r_[hr[1:], -1]                                                  # 合図 i が約定する足 i+1 の時刻
def gw(i):   # 足 i+1 の日付が GW(4/29〜5/6)
    t = idx[min(i + 1, n - 1)]; m = t.month * 100 + t.day; return 429 <= m <= 506
GW = np.array([gw(i) for i in range(n)])

def kyokuen(i, d):
    a = ang1[i] * d
    if np.isnan(a): return '?'
    return '逆向き' if a <= 0 else ('レンジ' if a < 10 else ('起き始め' if a < 30 else ('巡航' if a <= 55 else '竿先')))

# ====================================================== 歩く試験機(1玉ずつ、足の中は 網→利確→合図の降り)
def aruku(d, E, XC, XK, maxpos, SLV=None, TPV=None, ts=0.0, avoid_out=None):
    pos = []; out = []
    for i in range(1, n - 1):
        keep = []
        for p in pos:
            j = p['j']
            if i >= j: p['lo'] = min(p['lo'], Ll[i]); p['hi'] = max(p['hi'], Hh[i])
            if SLV is not None and not np.isnan(SLV[i]):
                p['sl'] = SLV[i] if np.isnan(p['sl']) else (max(p['sl'], SLV[i]) if d > 0 else min(p['sl'], SLV[i]))
            ex = None
            slhit = i > j and not np.isnan(p['sl']) and ((d > 0 and Ll[i] <= p['sl'] + 1e-9) or (d < 0 and Hh[i] >= p['sl'] - 1e-9))
            tv = TPV[i] if TPV is not None else np.nan
            tphit = i > j and not np.isnan(tv) and ((d > 0 and tv > p['e'] and Hh[i] >= tv - 1e-9) or (d < 0 and tv < p['e'] - SPR - 1e-12 and Ll[i] <= tv + 1e-9))
            if slhit: ex = (min(O[i], p['sl']) if d > 0 else max(O[i], p['sl']) + SPR, i, 'TS' if p['ts'] else '網')
            elif tphit: ex = (max(O[i], tv) if d > 0 else min(O[i], tv) + SPR, i, '利確')
            elif XC[i] and XK[i] > T[j] and not (avoid_out is not None and nxh[i] == avoid_out):
                ex = (O[i + 1] + (0 if d > 0 else SPR), i + 1, '芯の降り' if p['n'] == 1 else '足しの降り')
            if ex: out.append(dict(ent=idx[j], e=p['e'], ext=idx[ex[1]], x=ex[0], why=ex[2], sig=j - 1)); continue
            if ts > 0 and i >= j:
                fav = (p['hi'] - p['e']) / P if d > 0 else (p['e'] - p['lo'] - SPR) / P
                if fav >= 0:
                    nsl = p['hi'] - ts * P if d > 0 else p['lo'] + ts * P
                    if np.isnan(p['sl']) or (d > 0 and nsl > p['sl']) or (d < 0 and nsl < p['sl']): p['sl'] = nsl; p['ts'] = True
            keep.append(p)
        pos = keep
        if E[i] and len(pos) < maxpos:
            e = O[i + 1] + (SPR if d > 0 else 0.0); sl = SLV[i] if SLV is not None else np.nan
            if SLV is not None and not np.isnan(sl) and ((d > 0 and sl >= e) or (d < 0 and sl <= e)): continue
            pos.append(dict(j=i + 1, e=e, sl=sl, n=len(pos) + 1, lo=1e18, hi=-1e18, ts=False))
    return pd.DataFrame(out)

def okurasu(E, avoid=0):   # 0時に約定する合図は、0時でない足まで待つ
    E = E.copy()
    for i in np.where(E & (nxh == avoid))[0]:
        E[i] = False; k = i + 1
        while k < n - 1 and nxh[k] == avoid: k += 1
        E[k] = True
    return E

# ====================================================== 1) クジラの入口(縄1〜5・許し・日足9の3本目・日足21の傾き・並び)
def kujira_E(d, narabi):
    up = e9 > e21; up1 = np.r_[False, up[:-1]]
    p = ((dc > de9) & (fc > fe21)) if d > 0 else ((dc < de9) & (fc < fe21)); p = np.nan_to_num(p).astype(bool)
    p1 = np.r_[False, p[:-1]]
    if d > 0: cross = up & ~up1; side = up; kawa = C > md + sd; chi = C > h21; qq = dc > de21; ns = C <= md + 2 * sd
    else: cross = ~up & up1; side = ~up; kawa = C < md - sd; chi = C < l21; qq = dc < de21; ns = C >= md - 2 * sd
    s9 = (D1.c > D1.e9) if d > 0 else (D1.c < D1.e9); k9d = s9.groupby((~s9).cumsum()).cumsum().values
    kk = np.where(di >= 0, k9d[np.clip(di, 0, None)], 0); kk1 = np.r_[0, kk[:-1]]
    kai = p & ~p1 & side & ~cross & (kk >= 3)
    kai = kai | ((kk >= 3) & ~(kk1 >= 3) & p & side & ~cross & (kk == 3))
    E = ((cross & p & kawa & chi) | (kai & qq)) & ns
    E = E & ((dang > 0) if d > 0 else (dang < 0))
    if narabi: E = E & ((de9 > de21) if d > 0 else (de9 < de21))
    E = np.nan_to_num(E).astype(bool) & ~GW
    return okurasu(E)
def x219_D(d):   # 日足の219(売りは921)の並び
    v = (de9 <= de21) if d > 0 else (de9 > de21)
    return np.nan_to_num(v).astype(bool) & (di >= 0), dk
TP4 = lambda d: mae1(fmd + 4.0 * fsd * d)

KUJ = {d: aruku(d, kujira_E(d, d > 0), *x219_D(d), 5, None, TP4(d), 550, 0) for d in (1, -1)}

# ====================================================== 2) ドテン買い(売りの利確で構え、1時間921の足が閉じたら次の足で1玉)
def doten():
    tp = KUJ[-1][KUJ[-1].why == '利確']; arm = np.zeros(n, bool); arm[np.searchsorted(T, tp.ext.values)] = True
    up = e9 > e21; up1 = np.r_[up[0], up[:-1]]; cr = ~up1 & up
    W = np.zeros(n, bool); a = False
    for i in range(n):
        if arm[i]: a = True
        if a and cr[i]: W[i] = True; a = False
    W = W & ~GW
    u = (H4.e9 > H4.e21); x = (u.shift(1, fill_value=False) & ~u).values
    X = np.where(fi >= 0, x[np.clip(fi, 0, None)], False)
    return aruku(1, W, X, fk, 1, None, None, 550, None)
DOT = doten()

# ====================================================== 3) 鯛(クジラ買いと同じ入り・1玉・4時間9割れ・TS550)
w4 = (((H4.o + H4.c) / 2 < H4.e9) & (H4.c < H4.e9)).values
TAI_E = kujira_E(1, True) & ~np.isin(nxh, [16, 17, 18, 19, 20, 21, 22, 23])   # 11-19「ご」:約定16〜23時(NY)は入らない
TAI = aruku(1, TAI_E, np.where(fi >= 0, w4[np.clip(fi, 0, None)], False), fk, 1, None, None, 550, 0)

# ====================================================== 4) 押し目(かがみ無限 抜1・無1・出1:日足)
def oshime(d, pk=10, wk=3):
    o, h, l, c, a9, a21 = (D1[x].values for x in ['o', 'h', 'l', 'c', 'e9', 'e21']); w = (4 * D1.sd).values; nd = len(D1)
    sig = np.zeros(nd, bool); up = a9 > a21 if d > 0 else a9 < a21; arm = False; inc = False
    for i in range(pk + wk, nd):
        if not up[i]: inc = False; arm = False; continue
        seg_h, seg_l = h[i - pk:i], l[i - pk:i]
        pki = i - pk + (int(np.argmax(seg_h)) if d > 0 else int(np.argmin(seg_l)))
        prev = seg_h.max() if d > 0 else seg_l.min()
        pulled = (l[pki:i] <= a9[pki:i]).any() if d > 0 else (h[pki:i] >= a9[pki:i]).any()
        brk = c[i] > prev if d > 0 else c[i] < prev
        if not inc and w[i] > w[i - wk] and pulled and brk: sig[i] = True; inc = True; arm = False; continue
        if inc:
            if (c[i] > a9[i]) if d > 0 else (c[i] < a9[i]): arm = True
            if arm and ((l[i] <= a21[i]) if d > 0 else (h[i] >= a21[i])) and ((c[i] > o[i]) if d > 0 else (c[i] < o[i])): sig[i] = True; arm = False
    E = np.zeros(n, bool)
    for i in np.where(sig)[0]:
        j = np.searchsorted(T, D1.k.values[i])
        while j < n and hr[j] == 0: j += 1
        if 1 <= j < n: E[j - 1] = True
    E = E & ~GW
    X, XK = x219_D(d)
    SLV = mae1(col(D1, di, 'l') if d > 0 else col(D1, di, 'h')); TPV = mae1(dmd + 3.5 * dsd * d)
    return aruku(d, E, X, XK, 5, SLV, TPV, 0.0, 0)
OSH = {d: oshime(d) for d in (1, -1)}

# ====================================================== 5) しあわせセット(レンジの箱)
def shiawase(d, nflip=3, win=30, kar=3, tame_max=5, tpk=2.0, tamek=3.5, naka=1.0, shuu=False):
    sg = np.sign(D1.c - D1.c.shift(21)); fl = (sg != sg.shift(1)) & sg.shift(1).notna() & (sg != 0)
    rgD = (fl.astype(int).rolling(win).sum() >= nflip).values; hD, lD = D1.h.values, D1.l.values
    bh = np.full(len(D1), np.nan); bl = np.full(len(D1), np.nan); st = None
    for k in range(len(D1)):
        if rgD[k]:
            if st is None: st = max(0, k - win + 1)
            a = st
        else: st = None; a = max(0, k - win + 1)
        bh[k] = hD[a:k + 1].max(); bl[k] = lD[a:k + 1].min()
    pick = lambda v: np.where(di >= 0, v[np.clip(di, 0, None)], np.nan)
    rg = np.nan_to_num(pick(rgD.astype(float))).astype(bool); bhi, blo = pick(bh), pick(bl); e2 = col(D1, di, 'e200')
    ok = np.ones(n, bool)
    if shuu:
        Wk = RAW.resample('W-MON', label='left', closed='left').agg(AG).dropna(); Wk['k'] = Wk.index + pd.Timedelta('7D')
        Wk['m'] = (Wk.c.ewm(span=9, adjust=False).mean() - Wk.c.ewm(span=21, adjust=False).mean()) * d > 0
        wi = np.searchsorted(Wk.k.values, idx.values + np.timedelta64(1, 'h'), side='right') - 1
        ok = np.where(wi >= 0, Wk.m.values[np.clip(wi, 0, None)], False).astype(bool)
    newday = np.r_[False, dk[1:] != dk[:-1]]; pos = []; out = []; pair = False
    for i in range(1, n - 1):
        lv = dmd[i-1] - 2 * d * dsd[i-1]; t2 = dmd[i-1] + tpk * d * dsd[i-1]; t35 = dmd[i-1] + tamek * d * dsd[i-1]; keep = []
        for p in pos:
            ex = None
            if i > p['j']:
                if p['brk'] and hr[i] != 0: ex = (O[i] + (0 if d > 0 else SPR), '芯の降り')
                else:
                    tv = t2 if p['r'] == '刈る' else t35
                    if not np.isnan(tv) and ((d > 0 and tv > p['e'] and Hh[i] >= tv) or (d < 0 and tv < p['e'] - SPR and Ll[i] <= tv)):
                        ex = (max(O[i], tv) if d > 0 else min(O[i], tv) + SPR, '利確')
            if ex: out.append(dict(ent=idx[p['j']], e=p['e'], ext=idx[i], x=ex[0], why=ex[1], sig=p['j'], r=p['r']))
            else: keep.append(p)
        pos = keep
        if newday[i]:
            for p in pos:
                if (d > 0 and dc[i] < p['bx']) or (d < 0 and dc[i] > p['bx']): p['brk'] = True
        if pair and not any(p['r'] == '刈る' for p in pos): pair = False
        if rg[i-1] and not GW[i-1] and ok[i-1] and not pair and hr[i] != 0 and sum(p['r'] == 'ため' for p in pos) < tame_max and not np.isnan(lv) \
           and ((d > 0 and Ll[i] <= lv) or (d < 0 and Hh[i] >= lv)):
            e = (min(O[i], lv) + SPR) if d > 0 else max(O[i], lv); bx = blo[i-1] if d > 0 else bhi[i-1]
            if ((d > 0 and e > bx) or (d < 0 and e < bx)) and abs(e - e2[i-1]) > naka * dsd[i-1]:
                for k_, rr in enumerate(['刈る'] * kar + ['ため']): pos.append(dict(j=i, e=e, r=rr, bx=bx, brk=False))
                pair = True
    return pd.DataFrame(out)
SHI = {1: shiawase(1), -1: shiawase(-1, shuu=True)}

# ====================================================== エンジンの玉(比べられる側)
sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import Market, load_cached
from tai_parts import run_tai, run_doten, run_oshime_d, run_shiawase
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']
srv = Market(load_cached(D_), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']),
          kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}; tz = f['tai']
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
ENG = {'クジラ買い': run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **NB)[0],
       'クジラ売り': run_tai(srv, '1D', '4h', '1h', -1, tuple(f['core_exit']), **KW)[0],
       'ドテン買い': run_doten(srv, 1, xtf='4h', **KW)[0],
       '鯛': run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(tz.get('ng_hours', ()))})[0],
       '押し目買い': run_oshime_d(srv, 1, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False))[0],
       '押し目売り': run_oshime_d(srv, -1, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False))[0],
       'しあわせ買い': run_shiawase(srv, 1, yasumi=f.get('yasumi', False), shuu_muki=False, **sz)[0],
       'しあわせ売り': run_shiawase(srv, -1, yasumi=f.get('yasumi', False), shuu_muki=True, **sz)[0]}
ARU = {'クジラ買い': KUJ[1], 'クジラ売り': KUJ[-1], 'ドテン買い': DOT, '鯛': TAI, '押し目買い': OSH[1], '押し目売り': OSH[-1],
       'しあわせ買い': SHI[1], 'しあわせ売り': SHI[-1]}
MUKI = {'クジラ買い': 1, 'クジラ売り': -1, 'ドテン買い': 1, '鯛': 1, '押し目買い': 1, '押し目売り': -1, 'しあわせ買い': 1, 'しあわせ売り': -1}

# ====================================================== あわせ・5つの局面
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
def key(t): return pd.DataFrame({'ent': pd.to_datetime(t.ent), 'ext': pd.to_datetime(t.ext), 'e': np.round(t.e.astype(float), 3), 'x': np.round(t.x.astype(float), 3), 'why': t.why})
rows = []; zen = []; ALL = []
for nm in ENG:
    a, b = key(ENG[nm]), key(ARU[nm]); a['c'] = a.groupby(list(a.columns)).cumcount(); b['c'] = b.groupby(list(b.columns)[:5]).cumcount()
    m = a.merge(b, how='outer', on=['ent', 'ext', 'e', 'x', 'why', 'c'], indicator=True)
    g = m._merge.value_counts()
    rows.append(dict(部品=nm, エンジンの玉=len(a), 歩いた玉=len(b), 一致=int(g.get('both', 0)), エンジンだけ=int(g.get('left_only', 0)), 歩きだけ=int(g.get('right_only', 0))))
    if g.get('left_only', 0) or g.get('right_only', 0): zen.append((nm, m[m._merge != 'both'].sort_values('ent').head(10)))
    d = MUKI[nm]; t = ARU[nm].copy(); t['pips'] = (t.x - t.e) / P * d
    t['局面'] = [kyokuen(int(s), d) if 0 <= int(s) < n else '?' for s in (np.searchsorted(T, pd.to_datetime(t.ent).values) - 1)]
    t['部品'] = nm; ALL.append(t)
R = pd.DataFrame(rows); print('■ 入口から出口まで、別の目で歩いた玉とエンジンの玉のあわせ(入った足・入り値・降りた足・降り値・降りた理由が全部同じなら一致)')
print(R.to_string(index=False)); print(f'  合計 エンジン {R.エンジンの玉.sum()} 玉 / 一致 {R.一致.sum()} / ずれ {R.エンジンだけ.sum() + R.歩きだけ.sum()}')
for nm, z in zen: print(f'\n  ずれ:{nm}(先頭10)'); print(z.to_string(index=False))
A = pd.concat(ALL, ignore_index=True)
print('\n■ 降りた理由(歩いた玉)'); print(pd.crosstab(A.部品, A.why).to_string())
print('\n■ 5つの局面(合図の1時間足の21の角度を向きに合わせて)×部品:玉の数 / 勝率% / 合計p')
od = ['逆向き', 'レンジ', '起き始め', '巡航', '竿先']
for v, fn in [('玉', 'size'), ('勝率%', lambda s: round((s > 0).mean() * 100)), ('合計p', lambda s: round(s.sum()))]:
    tb = A.pivot_table(index='部品', columns='局面', values='pips', aggfunc=fn).reindex(columns=[c for c in od if c in A.局面.unique()])
    print(f'  [{v}]'); print(tb.fillna('').to_string())
A.to_csv('/home/user/-/engine/kekka_tai/nyu/歩いて検証_全部品_入口出口_20261119.csv', index=False)

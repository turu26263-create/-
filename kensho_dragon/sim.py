# bt_v3.py と同じ決まりを、数字を動かせる形にした試験機(numba で速くした)
# 初期値 = v3 そのまま。新しいスイッチ(COOL)は初期値「なし」= v3 と同じ動き
import glob, os, numpy as np, pandas as pd, numba as nb

HERE = os.path.dirname(os.path.abspath(__file__))
PIP = 0.01

def load():
    cache = HERE + '/m5h1.pkl'
    if os.path.exists(cache):
        return pd.read_pickle(cache)
    dfs = []
    for f in sorted(glob.glob(os.environ.get('M1DIR', HERE + '/../dl/m1') + '/*.csv')):
        d = pd.read_csv(f, header=None, names=['d', 't', 'o', 'h', 'l', 'c', 'v'])
        d.index = pd.to_datetime(d.d + ' ' + d.t, format='%Y.%m.%d %H:%M')
        dfs.append(d[['o', 'h', 'l', 'c']])
    m1 = pd.concat(dfs).sort_index(); m1 = m1[~m1.index.duplicated()]
    agg = dict(o='first', h='max', l='min', c='last')
    out = (m1.resample('5min').agg(agg).dropna(), m1.resample('1h').agg(agg).dropna())
    pd.to_pickle(out, cache)
    return out

def order(c):
    a, b, s = [c.ewm(span=p, adjust=False).mean() for p in (5, 9, 21)]
    return np.where((a > b) & (b > s), 1, np.where((a < b) & (b < s), -1, 0))

def atr14(df):
    tr = pd.concat([df.h - df.l, (df.h - df.c.shift()).abs(), (df.l - df.c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(14).mean()

def prep(m5, h1, CHB=22, CHK=3.0, ATRTF='M5'):
    m = m5.copy()
    m['loc'] = pd.Series(order(m.c), index=m.index).shift(1)
    h1o = pd.Series(order(h1.c), index=h1.index + pd.Timedelta(hours=1))
    m['trend'] = h1o.reindex(m.index, method='ffill')
    if ATRTF == 'M5':
        a = atr14(m).shift(1)
    else:
        a = atr14(h1); a.index = a.index + pd.Timedelta(hours=1); a = a.reindex(m.index, method='ffill')
    hh = m.h.rolling(CHB).max().shift(1); ll = m.l.rolling(CHB).min().shift(1)
    m['chL'] = hh - CHK * a; m['chS'] = ll + CHK * a
    m = m.dropna()
    return m

@nb.njit(cache=True)
def run(O, H, L, C, LOC, TRD, CHL, CHS, spr, MAXPOS, ADDSTEP, COOL, YEAR):
    # COOL: 0=なし(v3) / >0=損切りで玉が0になったら N本休む / -1=5分の並びが一度崩れるまで待つ
    n = len(O)
    pd_ = np.zeros(64); pe = np.zeros(64); ps = np.zeros(64); np_ = 0
    eqc = 0.0; peak = 0.0; dd = 0.0
    gain = 0.0; loss = 0.0; ntr = 0; ncamp = 0; nwin_camp = 0; camp_p = 0.0
    nsl = 0; ndoten = 0; nkuzure = 0
    yp = np.zeros(20)
    wait = 0; need_break = False
    for i in range(n):
        trend = int(TRD[i]); loc = int(LOC[i])
        if wait > 0: wait -= 1
        if need_break and loc != trend: need_break = False
        if np_ > 0:
            d = pd_[0]
            if trend == -d or trend == 0:
                for k in range(np_):
                    ex = O[i] if d > 0 else O[i] + spr
                    p = (ex - pe[k]) / PIP * d
                    eqc += p; camp_p += p; ntr += 1; yp[YEAR[i]] += p
                    if p > 0: gain += p
                    else: loss -= p
                np_ = 0
                if camp_p > 0: nwin_camp += 1
                camp_p = 0.0
                if trend == -d:
                    ndoten += 1
                    if loc == trend:
                        px = O[i] + spr if trend > 0 else O[i]
                        sl = CHL[i] if trend > 0 else CHS[i]
                        if trend > 0 and sl > px: sl = px - 10 * PIP
                        if trend < 0 and sl < px: sl = px + 10 * PIP
                        pd_[0] = trend; pe[0] = px; ps[0] = sl; np_ = 1; ncamp += 1
                else:
                    nkuzure += 1
            else:
                bid = O[i]
                for k in range(np_):
                    sl = CHL[i] if d > 0 else CHS[i]
                    if d > 0 and sl > ps[k] + 0.001 and sl < bid: ps[k] = sl
                    if d < 0 and sl < ps[k] - 0.001 and sl > bid + spr: ps[k] = sl
                if np_ < MAXPOS and loc == d:
                    px = O[i] if d > 0 else O[i] + spr
                    if d * (px - pe[np_ - 1]) >= ADDSTEP * PIP:
                        px2 = O[i] + spr if d > 0 else O[i]
                        sl = CHL[i] if d > 0 else CHS[i]
                        if d > 0 and sl > px2: sl = px2 - 10 * PIP
                        if d < 0 and sl < px2: sl = px2 + 10 * PIP
                        pd_[np_] = d; pe[np_] = px2; ps[np_] = sl; np_ += 1
        elif trend != 0 and loc == trend and wait == 0 and not need_break:
            px = O[i] + spr if trend > 0 else O[i]
            sl = CHL[i] if trend > 0 else CHS[i]
            if trend > 0 and sl > px: sl = px - 10 * PIP
            if trend < 0 and sl < px: sl = px + 10 * PIP
            pd_[0] = trend; pe[0] = px; ps[0] = sl; np_ = 1; ncamp += 1
        # 足の途中:損切り
        had = np_
        j = 0
        for k in range(np_):
            d = pd_[k]; e = pe[k]; sl = ps[k]
            hit = False
            if d > 0 and L[i] <= sl:
                ex = O[i] if O[i] <= sl else sl
                p = (ex - e) / PIP; hit = True
            elif d < 0 and H[i] + spr >= sl:
                ex = O[i] + spr if O[i] + spr >= sl else sl
                p = (e - ex) / PIP; hit = True
            if hit:
                eqc += p; camp_p += p; ntr += 1; nsl += 1; yp[YEAR[i]] += p
                if p > 0: gain += p
                else: loss -= p
            else:
                pd_[j] = d; pe[j] = e; ps[j] = sl; j += 1
        np_ = j
        if had > 0 and np_ == 0:
            if camp_p > 0: nwin_camp += 1
            camp_p = 0.0
            if COOL > 0: wait = COOL
            elif COOL == -1: need_break = True
        fl = 0.0
        for k in range(np_):
            fl += ((C[i] - pe[k]) if pd_[k] > 0 else (pe[k] - C[i] - spr)) / PIP
        eq = eqc + fl
        if eq > peak: peak = eq
        if peak - eq > dd: dd = peak - eq
    return eqc, gain, loss, ntr, ncamp, nwin_camp, dd, nsl, ndoten, nkuzure, yp

def sim(m, spread=0.3, MAXPOS=14, ADDSTEP=20.0, COOL=0, start=None, end=None):
    if start or end: m = m.loc[start:end]
    yr = (m.index.year - 2015).values.astype(np.int64)
    r = run(m.o.values, m.h.values, m.l.values, m.c.values, m['loc'].values.astype(np.float64),
            m.trend.values.astype(np.float64), m.chL.values, m.chS.values, spread * PIP,
            MAXPOS, ADDSTEP, COOL, yr)
    eqc, g, l, ntr, nc, nwc, dd, nsl, ndt, nkz, yp = r
    return dict(pips=round(eqc), PF=round(g / l, 3) if l else 99, DD=round(dd), tama=ntr, ikusa=nc,
                win=round(100 * nwc / max(nc, 1), 1), SL=nsl, doten=ndt, kuzure=nkz,
                year={2015 + k: round(v) for k, v in enumerate(yp) if v != 0})

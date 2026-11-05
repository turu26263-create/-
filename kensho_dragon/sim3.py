# 日足・4時間・1時間で波をとらえ、5分足で上下に入る形
from sim2 import *
from engine2 import run2

def sig(b, kind):
    c = b.c; e5, e9, e21, e200 = ema(c, 5), ema(c, 9), ema(c, 21), ema(c, 200)
    if kind == 'po':  up = (e5 > e9) & (e9 > e21) & (e21 > e200); dn = (e5 < e9) & (e9 < e21) & (e21 < e200)
    else:             up = (e5 > e9) & (e9 > e21);                dn = (e5 < e9) & (e9 < e21)
    s = pd.Series(np.where(up, 1, np.where(dn, -1, 0)), index=b.index)
    if kind == 'po': s[: b.index[min(200, len(b) - 1)]] = 0
    return s

def prep3(m5, h1, MAIN=('4h', 'po'), D1='none', H4='none', H1='none', EXIT='main', CHB=22, CHK=3.0, ATRTF=None):
    m = m5.copy(); idx = m.index
    bars = {tf: bigbars(h1, tf) for tf in ('1D', '4h', '1h')}
    main = to_m5(sig(bars[MAIN[0]], MAIN[1]), MAIN[0], idx)
    ent = main.copy()
    for tf, k in (('1D', D1), ('4h', H4), ('1h', H1)):
        if k != 'none':
            s = to_m5(sig(bars[tf], k), tf, idx)
            ent = ent.where(s == ent, 0)          # 全部が同じ向きの時だけ
    m['trend'] = ent if EXIT == 'all' else main
    m['ent'] = ent
    m['loc'] = pd.Series(order(m.c), index=idx).shift(1)
    atf = ATRTF or MAIN[0]
    a = to_m5(atr14(bars[atf]), atf, idx)
    hh = m.h.rolling(CHB).max().shift(1); ll = m.l.rolling(CHB).min().shift(1)
    m['chL'] = hh - CHK * a; m['chS'] = ll + CHK * a
    return m.dropna()

def sim3(m, spread=0.3, MAXPOS=14, ADDSTEP=20.0, COOL=0, start=None, end=None):
    if start or end: m = m.loc[start:end]
    yr = (m.index.year - 2015).values.astype(np.int64)
    r = run2(m.o.values, m.h.values, m.l.values, m.c.values, m['loc'].values.astype(np.float64),
             m.trend.values.astype(np.float64), m.ent.values.astype(np.float64), m.chL.values, m.chS.values,
             spread * PIP, MAXPOS, ADDSTEP, COOL, yr)
    eqc, g, l, ntr, nc, nwc, dd, nsl, ndt, nkz, yp, bs = r
    return dict(pips=round(eqc), PF=round(g / l, 3) if l else 99, DD=round(dd), ikusa=nc, win=round(100 * nwc / max(nc, 1), 1),
                buy=round(bs[0]), sell=round(bs[1]), year={2015 + k: round(v) for k, v in enumerate(yp) if v != 0})

def row(tag, m, spr=0.3, **kw):
    a = sim3(m, spr, start='2022', end='2024', **kw); b = sim3(m, spr, start='2015', end='2021', **kw); c = sim3(m, spr, start='2025', **kw)
    print(f"{tag:30s} 決 {a['pips']:+7d} PF{a['PF']:.2f} 戦{a['ikusa']:4d} DD{a['DD']:5d} | 確15-21 {b['pips']:+7d} PF{b['PF']:.2f} 戦{b['ikusa']:4d} DD{b['DD']:5d} 買{b['buy']:+6d} 売{b['sell']:+6d} | 確25 {c['pips']:+6d} 戦{c['ikusa']:3d}", flush=True)
    return a, b, c

# 波の大きい足(日足・4時間足)で 200/21/9/5 の並びを見る形。エンジンは sim.py の run をそのまま使う
from sim import *
LEN = {'1D': pd.Timedelta(days=1), '4h': pd.Timedelta(hours=4), '1h': pd.Timedelta(hours=1)}

def ema(c, p): return c.ewm(span=p, adjust=False).mean()

def bigbars(h1, tf):
    return h1 if tf == '1h' else h1.resample(tf).agg(dict(o='first', h='max', l='min', c='last')).dropna()

def to_m5(s, tf, idx):   # 足が確定した時刻に付け替えて、5分足へ前詰め
    s = s.copy(); s.index = s.index + LEN[tf]; return s.reindex(idx, method='ffill')

def prep2(m5, h1, TTF='1D', ETF='5min', F200='order', CHB=22, CHK=3.0):
    m = m5.copy(); b = bigbars(h1, TTF); c = b.c
    e5, e9, e21, e200 = ema(c, 5), ema(c, 9), ema(c, 21), ema(c, 200)
    if F200 == 'order':      # 5>9>21>200 の並び(パーフェクトオーダー)
        up = (e5 > e9) & (e9 > e21) & (e21 > e200); dn = (e5 < e9) & (e9 < e21) & (e21 < e200)
    elif F200 == 'close':    # 5>9>21 で、終値が200の上
        up = (e5 > e9) & (e9 > e21) & (c > e200); dn = (e5 < e9) & (e9 < e21) & (c < e200)
    else:                    # 200なし
        up = (e5 > e9) & (e9 > e21); dn = (e5 < e9) & (e9 < e21)
    tr = pd.Series(np.where(up, 1, np.where(dn, -1, 0)), index=b.index)
    tr[: b.index[min(200, len(b) - 1)]] = 0          # 200本そろうまでは見ない
    m['trend'] = to_m5(tr, TTF, m.index)
    if ETF == '5min': m['loc'] = pd.Series(order(m.c), index=m.index).shift(1)
    else:
        eb = bigbars(h1, ETF); m['loc'] = to_m5(pd.Series(order(eb.c), index=eb.index), ETF, m.index)
    a = to_m5(atr14(b), TTF, m.index)
    hh = m.h.rolling(CHB).max().shift(1); ll = m.l.rolling(CHB).min().shift(1)
    m['chL'] = hh - CHK * a; m['chS'] = ll + CHK * a
    return m.dropna()

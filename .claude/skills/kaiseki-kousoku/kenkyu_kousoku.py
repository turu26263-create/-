"""高速の研究台(numba)。入りの印を渡すと、網・利確・時間切れで1本ずつ決済して返す。

  from kenkyu_kousoku import load_srv, sim, summary
  合わせ込み防止:2021〜2022 で探し、2023 は最後に1回だけ見る(minadein-saiteki)。
"""
import numpy as np
import pandas as pd
from numba import njit

PIP = 0.01


def load_srv(path):
    d = pd.read_csv(path, sep="\t")
    d.columns = [c.strip("<>") for c in d.columns]
    t = pd.to_datetime(d["DATE"] + " " + d["TIME"])
    df = d[["OPEN", "HIGH", "LOW", "CLOSE"]].astype(float)
    df.columns = list("ohlc")
    df.index = t
    return df


@njit(cache=True)
def _sim(o, h, l, c, sig, sl_p, tp_p, maxbars, spr, exit_at):
    """sig[i]=+1/-1:足 i の始値で入る。sl_p/tp_p は値幅(円)。exit_at[i]=1 ならその足の始値で降りる。
    玉は1つだけ。足の中で網と利確の両方なら網が先。"""
    n = len(o)
    out = np.zeros((n, 4))  # 入り足, 出足, 向き, ピップ
    k = 0
    i = 0
    while i < n:
        d = sig[i]
        if d == 0 or np.isnan(sl_p[i]):
            i += 1
            continue
        op = o[i] + spr if d > 0 else o[i]
        sl = op - d * sl_p[i]
        tp = op + d * tp_p[i]
        j = i
        res = np.nan
        while j < n:
            if j > i and (j - i >= maxbars or exit_at[j] == 1):
                px = o[j] if d > 0 else o[j] + spr
                res = (px - op) * d
                break
            if d > 0:
                if l[j] <= sl:
                    res = (min(sl, o[j]) if j > i else sl) - op
                    break
                if h[j] >= tp:
                    res = tp - op
                    break
            else:
                if h[j] + spr >= sl:
                    res = op - (max(sl, o[j] + spr) if j > i else sl)
                    break
                if l[j] + spr <= tp:
                    res = op - tp
                    break
            j += 1
        if np.isnan(res):
            break
        out[k, 0] = i
        out[k, 1] = j
        out[k, 2] = d
        out[k, 3] = res / 0.01
        k += 1
        i = j + 1
    return out[:k]


def sim(df, sig, sl, tp, maxbars=9999, spread_pips=0.5, exit_at=None):
    n = len(df)
    f = lambda x: np.broadcast_to(np.asarray(x, float), (n,)).copy()
    ex = np.zeros(n, np.int8) if exit_at is None else np.asarray(exit_at, np.int8)
    r = _sim(df.o.values, df.h.values, df.l.values, df.c.values, np.asarray(sig, np.int8),
             f(sl), f(tp), int(maxbars), spread_pips * PIP, ex)
    tr = pd.DataFrame(r, columns=["i", "j", "d", "pips"])
    tr["t"] = df.index[tr.i.astype(int)]
    return tr


def summary(tr, label=""):
    if len(tr) == 0:
        return f"{label} 取引0"
    p = tr.pips
    g, ls = p[p > 0].sum(), -p[p < 0].sum()
    eq = p.cumsum()
    yrs = " ".join(f"{y}:{x.pips.sum():+.0f}p/PF{(x.pips[x.pips > 0].sum() / max(1e-9, -x.pips[x.pips < 0].sum())):.2f}"
                   for y, x in tr.groupby(tr.t.dt.year))
    return (f"{label} {len(tr)}回 {p.sum():+.0f}p PF{g / max(ls, 1e-9):.2f} 勝{(p > 0).mean():.0%} "
            f"落{(eq.cummax() - eq).max():.0f}p | {yrs}")

"""Wagamama_M5_EA.mq5 と同じ決まりの試験機(5分足)。

使い方:
  python bt_wagamama.py data/USDJPY_M5_*.csv.gz [--from 2024-01-01] [--to 2024-12-31] [--spread 0.3]

CSV は MT5 の書き出し(<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> ... <SPREAD>、タブ区切り)か、
日時,始,高,安,終 のカンマ区切り。SPREAD 列(ポイント)があればそれを使い、無ければ --spread(ピップ)。

決まりは EA と同じ:判断は確定足(1本前)、入りは次の足の始値。足の中で網と利確の両方に
届いたら網が先(厳しい側)。0.1ロット=1ピップ100円。
"""
import argparse
import sys

import numpy as np
import pandas as pd

PIP = 0.01
YEN_PER_PIP = 100.0  # 0.1 ロット

P = dict(
    max_spread=1.5, day_loss=5000.0,
    useA=True, a_start=1, a_end=8, a_bp=20, a_sig=2.0, a_max_atr=4.0, a_sl_atr=1.5, a_min_sl=5.0, a_max_bars=12,
    useB=True, b_start=9, b_end=20, b_h1ema=50, b_fast=20, b_slow=50, b_swing=6, b_pad=1.0, b_max_sl=15.0, b_rr=1.5, b_be=1.0,
)


def load(path):
    raw = pd.read_csv(path, sep=None, engine="python")
    cols = [c.strip("<>").upper() for c in raw.columns]
    raw.columns = cols
    if "DATE" in cols and "TIME" in cols:
        t = pd.to_datetime(raw["DATE"].astype(str) + " " + raw["TIME"].astype(str), format="mixed")
    else:
        t = pd.to_datetime(raw.iloc[:, 0], format="mixed")
    df = pd.DataFrame({"o": raw["OPEN"], "h": raw["HIGH"], "l": raw["LOW"], "c": raw["CLOSE"]}).astype(float)
    df.index = t
    if "SPREAD" in cols:
        df["spr"] = raw["SPREAD"].astype(float).values * 0.001  # ポイント(0.001)→円
    return df.sort_index()[~df.index.duplicated()]


def ema(x, n):
    return x.ewm(span=n, adjust=False).mean()


def indicators(df, p):
    c = df["c"]
    mid = c.rolling(p["a_bp"]).mean()
    sd = c.rolling(p["a_bp"]).std(ddof=0)  # MT5 の iBands は母標準偏差
    df["mid"], df["up"], df["dn"] = mid, mid + p["a_sig"] * sd, mid - p["a_sig"] * sd
    tr = pd.concat([df["h"] - df["l"], (df["h"] - c.shift()).abs(), (df["l"] - c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["ef"], df["es"] = ema(c, p["b_fast"]), ema(c, p["b_slow"])
    # 1時間足:確定した足だけを、その次の時間から使う
    h1 = df["c"].resample("1h", label="left", closed="left").last().dropna()
    e = ema(h1, p["b_h1ema"])
    trend = np.where((h1 > e) & (e > e.shift()), 1, np.where((h1 < e) & (e < e.shift()), -1, 0))
    tr_s = pd.Series(trend, index=h1.index + pd.Timedelta(hours=1))  # 確定したのは1時間後
    df["h1dir"] = tr_s.reindex(df.index, method="ffill").fillna(0).astype(int)
    df["lo_sw"] = df["l"].rolling(p["b_swing"]).min()
    df["hi_sw"] = df["h"].rolling(p["b_swing"]).max()
    return df


def run(df, p, spread_pips=0.3):
    df = indicators(df.copy(), p)
    n = len(df)
    t = df.index
    o, h, l, c = (df[k].values for k in "ohlc")
    spr = df["spr"].values if "spr" in df else np.full(n, spread_pips * PIP)
    mid, up, dn, atr = df["mid"].values, df["up"].values, df["dn"].values, df["atr"].values
    ef, es, h1d = df["ef"].values, df["es"].values, df["h1dir"].values
    lo_sw, hi_sw = df["lo_sw"].values, df["hi_sw"].values
    hours, mins, dow = t.hour.values, t.minute.values, t.dayofweek.values
    days = t.normalize()

    trades = []
    pos = {"A": None, "B": None}
    day_pnl, cur_day = 0.0, None

    def inh(hr, st, en):
        return (st <= hr < en) if st <= en else (hr >= st or hr < en)

    def close(eng, i, price, why):
        nonlocal day_pnl
        ps = pos[eng]
        pips = (price - ps["op"]) / PIP * ps["d"]
        trades.append(dict(eng=eng, d=ps["d"], t_in=t[ps["i"]], t_out=t[i], op=ps["op"], cp=price, pips=pips,
                           yen=pips * YEN_PER_PIP, why=why))
        day_pnl += pips * YEN_PER_PIP
        pos[eng] = None

    for i in range(300, n):
        if days[i] != cur_day:
            cur_day, day_pnl = days[i], 0.0
        k = i - 1  # 確定足
        bid = o[i]
        ask = o[i] + spr[i]

        # 足の始まり:持っている玉の世話(確定足 k で判断)
        if pos["A"]:
            ps = pos["A"]
            if i - ps["i"] >= p["a_max_bars"]:
                close("A", i, bid if ps["d"] > 0 else ask, "時間切れ")
            elif (ps["d"] > 0 and mid[k] > bid) or (ps["d"] < 0 and mid[k] < ask):
                ps["tp"] = mid[k]
            else:
                close("A", i, bid if ps["d"] > 0 else ask, "利確")
        if pos["B"]:
            ps = pos["B"]
            r = abs(ps["tp"] - ps["op"]) / p["b_rr"]
            if ps["d"] > 0 and ps["sl"] < ps["op"] and c[k] >= ps["op"] + p["b_be"] * r:
                ps["sl"] = ps["op"]
            if ps["d"] < 0 and ps["sl"] > ps["op"] and c[k] <= ps["op"] - p["b_be"] * r:
                ps["sl"] = ps["op"]

        # 入る
        ok = (spr[i] / PIP <= p["max_spread"] and not (p["day_loss"] > 0 and day_pnl <= -p["day_loss"])
              and not (dow[i] == 4 and hours[i] >= 20) and not (hours[i] == 23 and mins[i] >= 30)
              and not (hours[i] == 0 and mins[i] < 30))
        if ok and p["useA"] and pos["A"] is None and inh(hours[i], p["a_start"], p["a_end"]) \
                and atr[k] / PIP <= p["a_max_atr"]:
            slw = max(p["a_sl_atr"] * atr[k], p["a_min_sl"] * PIP)
            if h[k] >= up[k] and c[k] < up[k] and c[k] < o[k]:
                pos["A"] = dict(i=i, d=-1, op=bid, sl=bid + slw, tp=mid[k])
            elif l[k] <= dn[k] and c[k] > dn[k] and c[k] > o[k]:
                pos["A"] = dict(i=i, d=1, op=ask, sl=ask - slw, tp=mid[k])
        if ok and p["useB"] and pos["B"] is None and inh(hours[i], p["b_start"], p["b_end"]):
            if h1d[i] > 0 and ef[k] > es[k] and l[k] <= ef[k] and c[k] > ef[k] and c[k] > o[k]:
                sl = lo_sw[k] - p["b_pad"] * PIP
                w = ask - sl
                if 0 < w <= p["b_max_sl"] * PIP:
                    pos["B"] = dict(i=i, d=1, op=ask, sl=sl, tp=ask + p["b_rr"] * w)
            elif h1d[i] < 0 and ef[k] < es[k] and h[k] >= ef[k] and c[k] < ef[k] and c[k] < o[k]:
                sl = hi_sw[k] + p["b_pad"] * PIP
                w = sl - bid
                if 0 < w <= p["b_max_sl"] * PIP:
                    pos["B"] = dict(i=i, d=-1, op=bid, sl=sl, tp=bid - p["b_rr"] * w)

        # 足の中:網が先(厳しい側)。買いは bid、売りは ask(=bid+spread)で降りる
        for eng in ("A", "B"):
            ps = pos[eng]
            if not ps:
                continue
            if ps["d"] > 0:
                if l[i] <= ps["sl"]:
                    close(eng, i, min(ps["sl"], o[i]) if ps["i"] != i else ps["sl"], "網" if ps["sl"] < ps["op"] else "建値")
                elif h[i] >= ps["tp"]:
                    close(eng, i, ps["tp"], "利確")
            else:
                if h[i] + spr[i] >= ps["sl"]:
                    close(eng, i, max(ps["sl"], o[i] + spr[i]) if ps["i"] != i else ps["sl"], "網" if ps["sl"] > ps["op"] else "建値")
                elif l[i] + spr[i] <= ps["tp"]:
                    close(eng, i, ps["tp"], "利確")
    return pd.DataFrame(trades)


def report(tr, label=""):
    if tr.empty:
        print(label, "取引0")
        return
    eq = tr["yen"].cumsum()
    dd = (eq.cummax() - eq).max()
    g, ls = tr.loc[tr.yen > 0, "yen"].sum(), -tr.loc[tr.yen < 0, "yen"].sum()
    days = max(1, (tr.t_out.max() - tr.t_in.min()).days)
    print(f"{label} 取引{len(tr)}(1日{len(tr) / days * 7 / 5:.1f}回) 損益{tr.yen.sum():+,.0f}円 "
          f"PF{g / ls if ls else float('inf'):.2f} 勝率{(tr.yen > 0).mean():.0%} 最大落ち込み{dd:,.0f}円")
    for eng, x in tr.groupby("eng"):
        print(f"  {eng}: {len(x)}回 {x.yen.sum():+,.0f}円 理由別 " +
              " / ".join(f"{w}{len(y)}回{y.yen.sum():+,.0f}" for w, y in x.groupby("why")))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--from", dest="f")
    ap.add_argument("--to")
    ap.add_argument("--spread", type=float, default=0.3)
    a = ap.parse_args()
    d = pd.concat([load(f) for f in a.csv]).sort_index()
    d = d[~d.index.duplicated()]
    if a.f:
        d = d[d.index >= a.f]
    if a.to:
        d = d[d.index <= a.to]
    print(f"データ {d.index[0]} 〜 {d.index[-1]} {len(d)}本", file=sys.stderr)
    tr = run(d, P, a.spread)
    report(tr, "全体")
    if not tr.empty:
        for y, x in tr.groupby(tr.t_in.dt.year):
            report(x, f"{y}年")

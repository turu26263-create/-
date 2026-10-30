"""パソコン側で1回流す:MT5 からドル円5分足を書き出して、クラウドの試験機に渡す。

  pip install MetaTrader5 pandas
  python mt5_kakidashi.py            (MT5 を開いてログインしたまま)

できる物:USDJPY_M5_<年>.csv.gz(年ごと。1年で約1.5MB)。
この後、リポジトリの EA_5分足ひんぱん/data/ に入れて git push する。
"""
import datetime as dt
import sys

import MetaTrader5 as mt5
import pandas as pd

SYMBOL = sys.argv[1] if len(sys.argv) > 1 else "USDJPY"
YEARS = range(2020, 2027)

if not mt5.initialize():
    sys.exit(f"MT5 につながらない: {mt5.last_error()}")
mt5.symbol_select(SYMBOL, True)
for y in YEARS:
    r = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M5, dt.datetime(y, 1, 1), dt.datetime(y + 1, 1, 1))
    if r is None or len(r) == 0:
        print(y, "データなし", mt5.last_error())
        continue
    d = pd.DataFrame(r)
    t = pd.to_datetime(d["time"], unit="s")  # サーバー時刻のまま
    out = pd.DataFrame({"<DATE>": t.dt.strftime("%Y.%m.%d"), "<TIME>": t.dt.strftime("%H:%M:%S"),
                        "<OPEN>": d["open"], "<HIGH>": d["high"], "<LOW>": d["low"], "<CLOSE>": d["close"],
                        "<TICKVOL>": d["tick_volume"], "<VOL>": d["real_volume"], "<SPREAD>": d["spread"]})
    fn = f"USDJPY_M5_{y}.csv.gz"
    out.to_csv(fn, sep="\t", index=False, compression="gzip")
    gaps = (t.diff() > pd.Timedelta(days=4)).sum()
    print(y, len(out), "本", t.iloc[0], "〜", t.iloc[-1], "4日以上の穴", gaps, "→", fn)
mt5.shutdown()

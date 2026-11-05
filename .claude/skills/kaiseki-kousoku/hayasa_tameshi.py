"""速さの試し:作り物の5分足20万本で、648通りを回す時間を測る(成績には意味なし)。
  python3 hayasa_tameshi.py
"""
import itertools, os, sys, time
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kenkyu_kousoku import sim

rng = np.random.default_rng(0)
n = 200_000
c = 110 + np.cumsum(rng.normal(0, 0.02, n))
o = np.r_[c[0], c[:-1]]
h = np.maximum(o, c) + rng.random(n) * 0.02
l = np.minimum(o, c) - rng.random(n) * 0.02
df = pd.DataFrame({"o": o, "h": h, "l": l, "c": c},
                  index=pd.date_range("2021-01-01", periods=n, freq="5min"))
rng_w = (df.h - df.l).rolling(14).mean().values

t0 = time.time()
sim(df.iloc[:1000], np.zeros(1000, np.int8), 0.1, 0.1)  # 最初の組み立て
t_build = time.time() - t0

kumi = list(itertools.product([24, 36, 48, 60, 72, 96], [2, 2.5, 3], [3, 4, 5], [24, 48, 96, 144], [0.5, 1.0]))[:648]
t0 = time.time()
for N, ami, rikaku, honsu, spr in kumi:
    hi = df.h.rolling(N).max().shift(1).values
    lo = df.l.rolling(N).min().shift(1).values
    sig = np.where(df.c.values > hi, 1, np.where(df.c.values < lo, -1, 0)).astype(np.int8)
    sim(df, sig, ami * rng_w, rikaku * rng_w, maxbars=honsu, spread_pips=spr)
t = time.time() - t0
print(f"組み立て {t_build:.1f}秒 / {len(kumi)}通り {t:.1f}秒(1通り {t/len(kumi)*1000:.0f}ミリ秒)")

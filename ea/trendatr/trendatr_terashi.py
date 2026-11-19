# 11-19 たくちんが貼った TrendATR_SampleEA.mq4 を、そのままの決まりで研究台(MT4 1時間足 USDJPY・サーバー時刻)に写して1回だけ回す
# 決まり:EMA20/50 の921(ゴールデンクロス)で買い・RSI<70/219(デッドクロス)で売り・RSI>30。確定足で判定→次の足の始値で入る
# 損切り ATR14×2・利確 ATR14×3。玉は1つだけ。同じ足で両方に届いたら損切りが先(損な方)。スプレッド 0.3p
import sys, numpy as np, pandas as pd
df = pd.read_csv(sys.argv[1], header=None, names='d t o h l c v'.split())
df.index = pd.to_datetime(df.d + ' ' + df.t, format='%Y.%m.%d %H:%M'); o, h, l, c = df.o.values, df.h.values, df.l.values, df.c.values
ema = lambda s, p: s.ewm(span=p, adjust=False).mean()
f, s = ema(df.c, 20).values, ema(df.c, 50).values
d_ = df.c.diff(); up = d_.clip(lower=0); dn = -d_.clip(upper=0)
rsi = (100 - 100 / (1 + up.ewm(alpha=1/14, adjust=False).mean() / dn.ewm(alpha=1/14, adjust=False).mean())).values
tr = np.maximum(df.h - df.l, np.maximum((df.h - df.c.shift()).abs(), (df.l - df.c.shift()).abs())); atr = tr.rolling(14).mean().values   # MT4 の iATR は単純平均
spr = 0.003; T = []; i = 52; n = len(df)
while i < n - 1:
    gc = f[i-1] <= s[i-1] and f[i] > s[i] and rsi[i] < 70; dc = f[i-1] >= s[i-1] and f[i] < s[i] and rsi[i] > 30
    if not (gc or dc) or not atr[i] > 0: i += 1; continue
    dd = 1 if gc else -1; j = i + 1; e = o[j] + (spr if dd > 0 else 0); sl = e - dd * 2 * atr[i]; tp = e + dd * 3 * atr[i]
    k = j; why = None
    while k < n:
        if dd > 0:
            if l[k] <= sl: x, why = sl, '損切り'; break
            if h[k] - 0 >= tp: x, why = tp, '利確'; break
        else:
            if h[k] + spr >= sl: x, why = sl, '損切り'; break
            if l[k] + spr <= tp: x, why = tp, '利確'; break
        k += 1
    if why is None: break
    T.append((df.index[j], dd, e, df.index[k], x, why, dd * (x - e) * 100 - (spr * 100 if dd < 0 else 0), 2 * atr[i] * 100)); i = k   # 降りた足から次を見る(EA は降りた次の足から)
t = pd.DataFrame(T, columns='ent d e ext x why pips slp'.split()); t['R'] = t.pips / t.slp; y = t.ent.dt.year
print(f"{len(t)}玉 {t.pips.sum():+,.0f}p 勝率 {(t.pips>0).mean()*100:.0f}% PF {t.pips[t.pips>0].sum()/-t.pips[t.pips<0].sum():.2f} / 1%リスクで数えた合計 {t.R.sum():+.1f}R(1R=損切り1回ぶん)")
print('買い', int((t.d>0).sum()), f"{t.pips[t.d>0].sum():+,.0f}p / 売り", int((t.d<0).sum()), f"{t.pips[t.d<0].sum():+,.0f}p / 降り", t.why.value_counts().to_dict())
print('年ごと(p)', {int(a): int(round(v)) for a, v in t.groupby(y).pips.sum().items()})
print('年ごと(R)', {int(a): round(v, 1) for a, v in t.groupby(y).R.sum().items()})
eq = t.R.cumsum(); print('一番深い落ち込み', round((eq.cummax() - eq).max(), 1), 'R / 続けて負け最大', int((t.pips<0).astype(int).groupby((t.pips>=0).cumsum()).sum().max()))

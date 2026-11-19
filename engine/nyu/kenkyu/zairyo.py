# 11-19 たくちん「勝てる材料と負ける材料分けて」:歩いて検証で作り直した996玉の、合図の足(入る1本前)の材料ごとに勝ち負けを数える
# 決め方(ミナデイン):30玉以上・選22-24 と 確かめる年 の両方で同じ向き(両方で平均がその部品の平均より上=勝てる材料/両方で平均がマイナス=負ける材料)
import numpy as np, pandas as pd
r = pd.read_csv('/home/user/data/mt4/USDJPY60.csv', header=None, names=list('dtohlcv')); r.index = pd.to_datetime(r.d + ' ' + r.t, format='%Y.%m.%d %H:%M')
RAW = r[['o', 'h', 'l', 'c']].astype(float); AG = dict(o='first', h='max', l='min', c='last')
def sen(b, ln):
    b = b.copy(); c = b.c; b['e9'] = c.ewm(span=9, adjust=False).mean(); b['e21'] = c.ewm(span=21, adjust=False).mean()
    b['md'] = c.rolling(20).mean(); b['sd'] = c.rolling(20).std(ddof=0); b['w'] = 4 * b.sd / (4 * b.sd).rolling(100).mean()
    rng = b.h.rolling(150).max() - b.l.rolling(150).min(); b['ang'] = np.degrees(np.arctan2((b.e21 - b.e21.shift(3)) / rng * 500, 18))
    b['h21'] = b.h.shift(21); b['l21'] = b.l.shift(21); b['k'] = b.index + pd.Timedelta(ln); return b
H1 = sen(RAW, '1h'); H4 = sen(RAW.resample('4h').agg(AG).dropna(), '4h'); D1 = sen(RAW.resample('1D').agg(AG).dropna(), '1D')
W1 = sen(RAW.resample('W-MON', label='left', closed='left').agg(AG).dropna(), '7D')
def ue(B, t): i = B.k.searchsorted(t, side='right') - 1; return B.iloc[i]
A = pd.read_csv('/home/user/-/engine/kekka_tai/nyu/歩いて検証_全部品_入口出口_20261119.csv', parse_dates=['ent', 'ext'])
MUKI = {'クジラ買い': 1, 'クジラ売り': -1, 'ドテン買い': 1, '鯛': 1, '押し目買い': 1, '押し目売り': -1, 'しあわせ買い': 1, 'しあわせ売り': -1}
def kyoku(a):
    return '逆向き' if a <= 0 else ('レンジ' if a < 10 else ('起き始め' if a < 30 else ('巡航' if a <= 55 else '竿先')))
rows = []
for t in A.itertuples():
    d = MUKI[t.部品]; j = H1.index.get_loc(t.ent) - 1; x = H1.iloc[j]; tc = x.k
    a4, a1d, w = ue(H4, tc), ue(D1, tc), ue(W1, tc)
    z = (x.c - x.md) / x.sd * d; hon = (x.c - x.o) * d
    rows.append(dict(部品=t.部品, 年=t.ent.year, p=t.pips,
        色='向きと同じ' if hon > 0 else '逆', σ位置=('−1σより下' if z < -1 else '−1〜0σ' if z < 0 else '0〜1σ' if z < 1 else '1〜2σ' if z < 2 else '2σの外'),
        終値と9='向き側' if (x.c - x.e9) * d > 0 else '逆側', 終値と21='向き側' if (x.c - x.e21) * d > 0 else '逆側',
        局面1h=kyoku(x.ang * d), 局面4h=kyoku(a4.ang * d), 局面日足=kyoku(a1d.ang * d),
        遅行21='向きへ抜け' if (x.c > x.h21 if d > 0 else x.c < x.l21) else ('逆へ抜け' if (x.c < x.l21 if d > 0 else x.c > x.h21) else '絡み'),
        帯の幅=('しぼみ' if x.w < 0.7 else '広い' if x.w > 1.3 else 'ふつう'),
        実体=('小5p未満' if abs(x.c - x.o) < 0.05 else '大20p以上' if abs(x.c - x.o) >= 0.2 else '中'),
        日足並び='向き側' if (a1d.e9 - a1d.e21) * d > 0 else '逆', 週足並び='向き側' if (w.e9 - w.e21) * d > 0 else '逆',
        日足終値と9='向き側' if (a1d.c - a1d.e9) * d > 0 else '逆側', 四h終値と21='向き側' if (a4.c - a4.e21) * d > 0 else '逆側',
        時間帯=('東京0-8時' if tc.hour - 1 < 8 else '欧州8-15時' if tc.hour - 1 < 15 else 'NY15-24時'), 曜日='月火水木金土日'[x.name.dayofweek]))
F = pd.DataFrame(rows); F['選'] = F.年.between(2022, 2024)
ZAI = ['色', 'σ位置', '終値と9', '終値と21', '局面1h', '局面4h', '局面日足', '遅行21', '帯の幅', '実体', '日足並び', '週足並び', '日足終値と9', '四h終値と21', '時間帯', '曜日']
GRP = {'クジラ(買い売り)': ['クジラ買い', 'クジラ売り'], '鯛': ['鯛'], '押し目(買い売り)': ['押し目買い', '押し目売り'], 'しあわせ(買い売り)': ['しあわせ買い', 'しあわせ売り'], 'ドテン買い': ['ドテン買い']}
out = []
for g, bus in GRP.items():
    G = F[F.部品.isin(bus)]; base = G.p.mean()
    for zc in ZAI:
        for v, s in G.groupby(zc):
            if len(s) < 30: continue
            m1, m2 = s[s.選].p.mean(), s[~s.選].p.mean()
            kind = '勝てる' if (m1 > base and m2 > base and s.p.mean() > base * 1.3) else ('負ける' if (m1 < 0 and m2 < 0) else '')
            out.append(dict(部品=g, 材料=zc, 値=v, 玉=len(s), 勝率=round((s.p > 0).mean() * 100), 平均p=round(s.p.mean()), 部品の平均p=round(base), 選22_24平均=round(m1) if not np.isnan(m1) else None, 確かめる年平均=round(m2), 合計p=round(s.p.sum()), 判定=kind))
O = pd.DataFrame(out); pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
for kind in ('勝てる', '負ける'):
    z = O[O.判定 == kind].sort_values(['部品', '平均p'], ascending=[True, kind == '負ける'])
    print(f'\n■ {kind}材料(30玉以上・選22-24と確かめる年の両方で同じ向き)'); print(z.drop(columns='判定').to_string(index=False) if len(z) else '  なし')
O.to_csv('/home/user/-/engine/kekka_tai/nyu/勝ち負けの材料_20261119.csv', index=False)
print('\n部品ごとの平均p:', {g: round(F[F.部品.isin(b)].p.mean()) for g, b in GRP.items()})

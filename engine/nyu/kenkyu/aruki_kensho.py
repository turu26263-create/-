# 11-19 たくちん「エンジン改良 ロウソクのいち、色 上下 bb ルール通りにうごくかどうか 歩いて検証」
# エンジン(今の決まった形のクジラ買い・売り)が入った玉を1つずつ、合図の1時間足に戻って、
# エンジンの部品を使わずに CSV から足を作り直して決まりを1つずつ確かめる(別の目で照らす)。
# 見る物:ロウソク(色・実体・上ひげ・下ひげ)・位置(帯のσ・9と21の上下)・帯(川の外/竿先)・遅行スパン・上の足(日足9・4時間21・日足の並び・日足21の傾き)
# 約定:合図の足の次の足の始値(買いはスプレッド0.003を足す)で入っているか
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
import numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else '/home/user/data/mt4'

# ---------- 1) エンジンの玉(比べられる側)
from nyu import Market, load_cached
from tai_parts import run_tai
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']
srv = Market(load_cached(D), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']),
          avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
T = {1: run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **{**KW, 'narabi': f.get('narabi', False)})[0],
     -1: run_tai(srv, '1D', '4h', '1h', -1, tuple(f['core_exit']), **KW)[0]}

# ---------- 2) 別の目:CSV から足を作り直す(エンジンの部品は使わない)
r = pd.read_csv(f'{D}/USDJPY60.csv', header=None, names=['d', 't', 'o', 'h', 'l', 'c', 'v'])
r.index = pd.to_datetime(r.d + ' ' + r.t, format='%Y.%m.%d %H:%M'); H = r[['o', 'h', 'l', 'c']].astype(float)
def sen(b, ln):
    b = b.copy(); c = b.c
    b['e9'] = c.ewm(span=9, adjust=False).mean(); b['e21'] = c.ewm(span=21, adjust=False).mean()
    b['md'] = c.rolling(20).mean(); b['sd'] = c.rolling(20).std(ddof=0)
    b['k'] = b.index + pd.Timedelta(ln); return b
AG = dict(o='first', h='max', l='min', c='last')
H1 = sen(H, '1h'); H4 = sen(H.resample('4h').agg(AG).dropna(), '4h'); D1 = sen(H.resample('1D').agg(AG).dropna(), '1D')
rng = D1.h.rolling(150).max() - D1.l.rolling(150).min(); D1['ang'] = np.degrees(np.arctan2((D1.e21 - D1.e21.shift(3)) / rng * 500, 18))
def mae(B, t):          # 時刻 t(1時間足が閉じた時)にもう閉じている足
    i = B.k.searchsorted(t, side='right') - 1; return B.iloc[i] if i >= 0 else None
def k9(t, d):           # 日足の終値が9の向こうに何本続いているか
    i = D1.k.searchsorted(t, side='right') - 1; n = 0
    while i >= 0 and ((D1.c.iloc[i] > D1.e9.iloc[i]) if d > 0 else (D1.c.iloc[i] < D1.e9.iloc[i])): n += 1; i -= 1
    return n
def kyoka(t, d):        # 許し:日足の終値が9の向こう かつ 4時間の終値が21の向こう
    a = mae(D1, t); b = mae(H4, t)
    if a is None or b is None: return False
    return (a.c > a.e9 and b.c > b.e21) if d > 0 else (a.c < a.e9 and b.c < b.e21)
def sigma8(c, md, sd):
    z = (c - md) / sd
    for lim, nm in [(-3, '−3σの外'), (-2, '−3〜−2σ'), (-1, '−2〜−1σ'), (0, '−1σ〜真ん中'), (1, '真ん中〜+1σ'), (2, '+1〜+2σ'), (3, '+2〜+3σ')]:
        if z < lim: return nm
    return '+3σの外'

def miru(s, d):
    """合図の足 s(1時間足の開始時刻)で決まりを1つずつ見る"""
    x = H1.loc[s]; i = H1.index.get_loc(s); p = H1.iloc[i - 1]; t = x.k
    a = mae(D1, t); b = mae(H4, t); ch = H1.iloc[i - 21]
    up, up1 = x.e9 > x.e21, p.e9 > p.e21
    side = up if d > 0 else not up; cross = (up and not up1) if d > 0 else (not up and up1)
    kawa = x.c > x.md + x.sd if d > 0 else x.c < x.md - x.sd
    chi = x.c > ch.h if d > 0 else x.c < ch.l
    sao = x.c <= x.md + 2 * x.sd if d > 0 else x.c >= x.md - 2 * x.sd
    ky, ky1 = kyoka(t, d), kyoka(p.k, d); kk = k9(t, d)
    kai = ky and side and not cross and ((not ky1 and kk >= 3) or kk == 3) and ((a.c > a.e21) if d > 0 else (a.c < a.e21))
    e921 = cross and ky and kawa and chi
    nar = (a.e9 > a.e21) if d > 0 else True                     # 並び(買いだけ)
    ang = (a.ang > 0) if d > 0 else (a.ang < 0)
    gw = (lambda n: (n.month, n.day) >= (4, 29) and (n.month, n.day) <= (5, 6))(s + pd.Timedelta('1h'))
    hon = x.c - x.o
    return dict(合図の足=s, 入り方='921' if e921 else ('許し' if kai else '−'), 許し=ky, 川の外=kawa, 遅行21=chi, 竿先でない=sao,
                日足の並び=nar, 日足21の傾き=ang, GWでない=not gw, 日足9本数=kk,
                色='陽' if hon > 0 else ('陰' if hon < 0 else '十字'), 実体p=round(abs(hon) * 100, 1),
                上ひげp=round((x.h - max(x.o, x.c)) * 100, 1), 下ひげp=round((min(x.o, x.c) - x.l) * 100, 1),
                σ位置=sigma8(x.c, x.md, x.sd), 終値と9='上' if x.c > x.e9 else '下', 終値と21='上' if x.c > x.e21 else '下',
                ok=(e921 or kai) and sao and nar and ang and not gw)

rows = []
for d, tr in T.items():
    seen = set()
    for r_ in tr.itertuples():
        if r_.ent in seen: continue            # 同じ足で入った玉は1回見る
        seen.add(r_.ent)
        j = H1.index.get_loc(r_.ent); cand = [H1.index[j - 1]]          # 1本前の足(週明けは金曜の最後の足)
        if r_.ent.hour == 1: cand.append(H1.index[j - 2])                # 0時の約定は1時へずらす決まり → 2本前も見る
        m = [miru(c, d) for c in cand]; best = next((z for z in m if z['ok']), m[0])
        o = H1.loc[r_.ent].o; want = round(o + 0.003, 3) if d > 0 else round(o, 3)
        rows.append({'向き': '買い' if d > 0 else '売り', '入った足': r_.ent, 'エンジンの値': r_.e, '始値から': want, '約定あう': abs(r_.e - want) < 0.0005, **best})
R = pd.DataFrame(rows)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40); pd.set_option('display.max_rows', 400)
print(f'見た入り:{len(R)}(買い {int((R.向き=="買い").sum())}・売り {int((R.向き=="売り").sum())})。同じ足の玉は1回に数えた')
chk = ['許し', '竿先でない', '日足の並び', '日足21の傾き', 'GWでない', '約定あう']
for c in chk: print(f'  {c}: ○{int(R[c].sum())} ×{int((~R[c].astype(bool)).sum())}')
print(f'  入り方: {R.入り方.value_counts().to_dict()}(921 は 川の外と遅行21 も○の時だけ)')
print(f'  全部の決まりが○: {int(R.ok.sum())} / {len(R)}')
bad = R[~R.ok | ~R.約定あう]
print('\n×の入り(全部):'); print(bad.drop(columns=['ok']).to_string(index=False) if len(bad) else '  なし')
print('\nロウソクの数え(合図の足):')
for d in ('買い', '売り'):
    z = R[R.向き
          == d]; print(f'  {d}: 色 {z.色.value_counts().to_dict()} / 実体の平均 {z.実体p.mean():.1f}p・上ひげ {z.上ひげp.mean():.1f}p・下ひげ {z.下ひげp.mean():.1f}p')
    print(f'       σ位置 {z.σ位置.value_counts().to_dict()} / 終値と9 {z.終値と9.value_counts().to_dict()} / 終値と21 {z.終値と21.value_counts().to_dict()}')
R.to_csv('/home/user/-/engine/kekka_tai/nyu/歩いて検証_クジラ_20261119.csv', index=False)

# ---------- 3) 1本ずつ歩く(買い・売りの最初の入りの前5本と合図の足)
def aruku(s, d):
    i = H1.index.get_loc(s); out = []
    for j in range(i - 5, i + 2):
        x = H1.iloc[j]; p = H1.iloc[j - 1]; ch = H1.iloc[j - 21]; t = x.k; a = mae(D1, t); b = mae(H4, t)
        out.append(dict(足=H1.index[j].strftime('%m/%d %H:%M'), 始=x.o, 高=x.h, 安=x.l, 終=x.c, 色='陽' if x.c > x.o else '陰',
                        e9=round(x.e9, 3), e21=round(x.e21, 3), 並び='9上' if x.e9 > x.e21 else '9下',
                        交差='921' if (x.e9 > x.e21) and not (p.e9 > p.e21) else ('219' if (x.e9 <= x.e21) and (p.e9 > p.e21) else ''),
                        川=sigma8(x.c, x.md, x.sd), 遅行21本前='上抜け' if x.c > ch.h else ('下抜け' if x.c < ch.l else '絡み'),
                        日足c_e9='上' if a.c > a.e9 else '下', 四h_c_e21='上' if b.c > b.e21 else '下',
                        印='← 合図' if H1.index[j] == s else ('← 入り' if j == i + 1 else '')))
    return pd.DataFrame(out)
for d, nm in ((1, '買い'), (-1, '売り')):
    z = R[(R.向き == nm) & (R.入り方 == '921')]
    if len(z): s = z.合図の足.iloc[0]; print(f'\n歩き:{nm}の最初の921 {s}'); print(aruku(s, d).to_string(index=False))

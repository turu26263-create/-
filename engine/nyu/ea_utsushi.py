"""EA(ea/Kujira3_v1.mq5)の写し:EA の手順を1時間足1本ずつそのまま Python でなぞり、研究台(エンジン)の玉と1玉ずつ同じか照らす(11-09 たくちん「…がつくったデータと合わせて」)
ブローカーの網・利確は足の高安で見る(買いは Bid=足の値、売りは Ask=足の値+スプレッド)。スプレッドは研究台と同じ 0.3p"""
import sys, warnings; warnings.filterwarnings('ignore')
from nyu import *

def ea_run(mk, spr=0.003, maxpos=5, kai_k9=3, sao=2.0, tpk=3.5, ts=5.50, use_sell=True, use_doten=True, yasumi=True, avoid=0, tai=None):
    H = mk.feat('1h'); H4 = mk.feat('4h'); D = mk.feat('1D')
    O, Hh, Lh, C = H.o.values, H.h.values, H.l.values, H.c.values; T = H.index
    e9, e21, md, sd = H.e9.values, H.e21.values, H.md.values, H.sd.values
    k4, k1 = H4.k.values, D.k.values
    def done4(t): return np.searchsorted(k4, np.datetime64(t), 'right') - 1
    def done1(t): return np.searchsorted(k1, np.datetime64(t), 'right') - 1
    def perm(t, d):
        h = done4(t)
        if h < 0: return False
        dd = done1(H4.k.iloc[h])
        if dd < 0: return False
        return (D.c.iloc[dd] > D.e9.iloc[dd] and H4.c.iloc[h] > H4.e21.iloc[h]) if d > 0 else (D.c.iloc[dd] < D.e9.iloc[dd] and H4.c.iloc[h] < H4.e21.iloc[h])
    s9b = (D.c > D.e9).values; s9s = (D.c < D.e9).values
    def k9(dd, d):
        s = s9b if d > 0 else s9s; n = 0
        while dd - n >= 0 and s[dd - n]: n += 1
        return n
    def yas(t):
        m = t.month * 100 + t.day; return 429 <= m <= 506
    pos = []; out = []; arm = False; pend = {1: False, -1: False}
    def close(p, px, t, why): out.append(dict(kind=p['kind'], d=p['d'], ent=p['t'], e=p['e'], ext=t, x=px, why=why)); pos.remove(p)
    for i in range(30, len(T) - 1):
        t = T[i]; hour = t.hour
        ts1 = T[i - 1] + pd.Timedelta('1h'); ts2 = T[i - 2] + pd.Timedelta('1h')   # 合図の足が閉じた時刻(週末をまたいでも新しい足の始まりとは別)
        # --- 新しい足 t(i)が始まった:EA の OnTick ---
        dx = done1(ts1); h = done4(ts1)
        for p in list(pos):
            d = p['d']
            if p['kind'] == '鯛':
                a = H4.iloc[h]
                if bool(a.ware_b) and hour != avoid and H4.k.iloc[h] > p['t']: close(p, O[i], t, '4h9割れ'); continue
            elif p['kind'] == 'ドテン買い':
                a, b = H4.iloc[h], H4.iloc[h - 1]
                x219 = (b.e9 > b.e21) and not (a.e9 > a.e21)
                if x219 and H4.k.iloc[h] > p['t']: close(p, O[i], t, '4h219'); continue
            else:
                sig = (not (D.e9.iloc[dx] > D.e21.iloc[dx])) if d > 0 else (D.e9.iloc[dx] > D.e21.iloc[dx])
                if sig and hour != avoid and D.k.iloc[dx] > p['t']: close(p, O[i] + (0 if d > 0 else spr), t, '日足219/921'); continue
            # TS と利確の付け替え
            eb = p['i']
            if eb <= i - 1:
                if d > 0: mx = Hh[eb:i].max(); ns = mx - ts; p['sl'] = ns if p['sl'] is None or ns > p['sl'] else p['sl']
                else: mn = Lh[eb:i].min(); ns = mn + ts + spr; p['sl'] = ns if p['sl'] is None or ns < p['sl'] else p['sl']
            if p['kind'] not in ('ドテン買い', '鯛'):
                tpl = H4.md.iloc[h] + tpk * H4.sd.iloc[h] * d; p['tp'] = None
                if d > 0 and tpl > p['e']: p['tp'] = tpl
                if d < 0 and tpl < p['e'] - spr: p['tp'] = tpl + spr
        # 入り
        y = yasumi and yas(t)
        for d in ((1, -1) if use_sell else (1,)):
            c = C[i - 1]; upA, upB = e9[i - 1] > e21[i - 1], e9[i - 2] > e21[i - 2]
            side = upA if d > 0 else not upA; cross = (upA and not upB) if d > 0 else ((not upA) and upB)
            p_ = perm(ts1, d); pp = perm(ts2, d)
            dq = done1(ts1); qq = (D.c.iloc[dq] > D.e21.iloc[dq]) if d > 0 else (D.c.iloc[dq] < D.e21.iloc[dq])
            b21 = (D.e21.iloc[dq] - D.e21.iloc[dq - 3]) * d > 0
            kawa = c > md[i - 1] + sd[i - 1] if d > 0 else c < md[i - 1] - sd[i - 1]
            chi = c > Hh[i - 1 - 21] if d > 0 else c < Lh[i - 1 - 21]
            ns_ = c <= md[i - 1] + sao * sd[i - 1] if d > 0 else c >= md[i - 1] - sao * sd[i - 1]
            kk = k9(dq, d); kp = k9(done1(ts2), d)
            kai = p_ and not pp and side and not cross and kk >= kai_k9
            first = kk >= kai_k9 and not (kp >= kai_k9) and p_ and side and not cross and kk == kai_k9
            sig = (((cross and p_) and kawa and chi) or ((kai or first) and qq)) and ns_ and b21 and not y
            go = False
            if hour == avoid:
                if sig: pend[d] = True
            else: go = sig or pend[d]; pend[d] = False
            if go and sum(1 for q in pos if q['d'] == d and q['kind'] in ('買い', '売り')) < maxpos:
                pos.append(dict(kind='買い' if d > 0 else '売り', d=d, t=t, i=i, e=O[i] + (spr if d > 0 else 0), sl=None, tp=None))
            if go and d > 0 and tai and not any(q['kind'] == '鯛' for q in pos):
                pos.append(dict(kind='鯛', d=1, t=t, i=i, e=O[i] + spr, sl=None, tp=None))
        if use_doten and arm:
            if (e9[i - 1] > e21[i - 1]) and not (e9[i - 2] > e21[i - 2]):
                arm = False
                if not y and not any(q['kind'] == 'ドテン買い' for q in pos):
                    pos.append(dict(kind='ドテン買い', d=1, t=t, i=i, e=O[i] + spr, sl=None, tp=None))
        # --- 足 t(i)の中:ブローカーの網・利確 ---
        for p in list(pos):
            if p['i'] >= i and p['sl'] is None and p['tp'] is None: continue
            d = p['d']; sl, tp = p['sl'], p['tp']
            if d > 0:
                if sl is not None and Lh[i] <= sl + 1e-9: close(p, min(O[i], sl), T[i], 'TS550'); continue
                if tp is not None and Hh[i] >= tp - 1e-9: close(p, max(O[i], tp), T[i], '利確'); continue
            else:
                if sl is not None and Hh[i] + spr >= sl - 1e-9: close(p, max(O[i] + spr, sl), T[i], 'TS550'); continue
                if tp is not None and Lh[i] + spr <= tp + 1e-9:
                    close(p, min(O[i] + spr, tp), T[i], '利確'); arm = arm or (p['kind'] == '売り'); continue
    r = pd.DataFrame(out); r['pips'] = (r.x - r.e) / 0.01 * r.d; return r

if __name__ == '__main__':
    mk = Market(load_cached(sys.argv[1]), 'server')
    ea = ea_run(mk, tai=True)
    ref = pd.read_csv(sys.argv[2])
    ref['ent'] = pd.to_datetime(ref['入り(サーバー時刻)'], format='%Y.%m.%d %H:%M'); ref['ext'] = pd.to_datetime(ref['降り(サーバー時刻)'], format='%Y.%m.%d %H:%M')
    ea['ent'] = pd.to_datetime(ea.ent); ea['ext'] = pd.to_datetime(ea.ext)
    print(f"EAの写し {len(ea)}玉 {ea.pips.sum():+,.1f}p / 研究台 {len(ref)}玉 {ref.pips.sum():+,.1f}p")
    m = ea.merge(ref, left_on=['kind', 'ent'], right_on=['種類', 'ent'], how='outer', suffixes=('_ea', '_ref'), indicator=True)
    same = m[(m._merge == 'both') & (m.ext_ea == m.ext_ref) & ((m.pips_ea - m.pips_ref).abs() < 0.15)]
    print(f"入り・降り・損益が同じ玉 {len(same)} / 研究台だけ {int((m._merge=='right_only').sum())} / EAの写しだけ {int((m._merge=='left_only').sum())} / 入りは同じで降りが違う {int(((m._merge=='both')).sum()-len(same))}")
    diff = m.drop(same.index)
    pd.set_option('display.width', 250)
    print(diff[['kind', '種類', 'ent', 'e', '入り値', 'ext_ea', 'ext_ref', 'pips_ea', 'pips_ref', 'why', '降りの理由', '_merge']].head(25).to_string())

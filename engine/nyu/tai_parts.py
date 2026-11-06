# ニューぶん回しエンジンの部品:鯛の刺身とクジラ(決まりは engine_tai2・engine_kujira と同じ。数字は【置き換え】)
import numpy as np, pandas as pd
from nyu import Market, simulate

def tai_entry(mk, big, mid, small, d, sao=2.0, n8=False, kawa_chi=True, lag21=True):
    """縄1 big の9上 / 縄2 mid の21上 / 縄3 small の921 / 縄3改 許しが出た時にもう921済み / 縄4 川の外+遅行21本前 / 縄4改 big の21上 / 縄5 竿先で入らない / 縄8 big の角度55度超で入らない"""
    S = mk.feat(small); x = S
    M = mk.on(mid, big, ['c', 'e9']).join(mk.feat(mid)[['c', 'e21', 'k']].rename(columns={'c': 'cm'}))
    M['pb'] = (M.c > M.e9) & (M.cm > M.e21); M['ps'] = (M.c < M.e9) & (M.cm < M.e21)
    a = M[['k', 'pb', 'ps']].sort_values('k')
    perm = pd.merge_asof(pd.DataFrame({'kb': S.k.values}), a, left_on='kb', right_on='k', direction='backward')
    perm.index = S.index
    q = mk.on(small, big, ['c', 'e21', 'ang'])
    up = x.e9 > x.e21; up1 = up.shift(1, fill_value=False)
    if d > 0:
        p = perm.pb.fillna(False).astype(bool); cross = up & ~up1; side = up
        kawa = x.c > x.md + x.sd; chi = x.c > x.h21; qq = q.c > q.e21; ns = x.c <= x.md + sao * x.sd; ang = q.ang
    else:
        p = perm.ps.fillna(False).astype(bool); cross = ~up & up1; side = ~up
        kawa = x.c < x.md - x.sd; chi = x.c < x.l21; qq = q.c < q.e21; ns = x.c >= x.md - sao * x.sd; ang = -q.ang
    e921 = cross & p; kai = p & ~p.shift(1, fill_value=False) & side & ~cross
    filt = (kawa & chi) if kawa_chi else True
    ent = ((e921 & filt) | (kai & qq)) & ns
    if n8: ent = ent & ~(ang > 55)
    return ent.fillna(False).values

def exit_ware(mk, small, tf, d):
    """tf の9割れ(実体の真ん中と終値が9の向こう)。small の足に貼る"""
    c = 'ware_b' if d > 0 else 'ware_s'; y = mk.on(small, tf, [c])
    return y[c].fillna(False).astype(bool).values, y['k_' + tf].values

def exit_219(mk, small, tf, d):
    """tf の219(9が21の下。売りは921)"""
    y = mk.on(small, tf, ['up921'])
    v = y.up921.fillna(True if d > 0 else False).astype(bool)
    return (~v if d > 0 else v).values, y['k_' + tf].values

def exit_close9(mk, small, tf, d):
    """tf の終値が9の向こう"""
    F = mk.feat(tf); F = F.assign(cb=F.c < F.e9, cs=F.c > F.e9)
    mk._f[tf] = F
    c = 'cb' if d > 0 else 'cs'; y = mk.on(small, tf, [c])
    return y[c].fillna(False).astype(bool).values, y['k_' + tf].values

EXITS = {'9割れ': exit_ware, '219': exit_219, '終値9': exit_close9}

# ---- 網(上げるだけ)と利確の高さ(入る足に貼る。どれも閉じた足の値)
def sl_prevday(mk, small, d):
    """前の日の安値(売りは高値)"""
    y = mk.on(small, '1D', ['l', 'h']); return (y.l if d > 0 else y.h).values

def sl_line(mk, small, tf, col='e21', buf=0.05, d=1):
    """tf の線(e9/e21/e200/md)の buf 下(売りは上)"""
    y = mk.on(small, tf, [col]); return (y[col] - buf * d).values

def tp_sigma(mk, small, tf, k=3.5, d=1):
    """tf の帯の ±kσ"""
    y = mk.on(small, tf, ['md', 'sd']); return (y.md + k * y.sd * d).values

def make_sl(mk, small, d, sl):
    if sl is None: return None
    if sl == 'prevday': return sl_prevday(mk, small, d)
    tf, col = sl[0], sl[1]; buf = sl[2] if len(sl) > 2 else 0.05     # 例 ('4h','e21') / ('4h','e21',0.20)
    return sl_line(mk, small, tf, col, buf, d)

def make_tp(mk, small, d, tp):
    if tp is None: return None
    tf, k = tp; return tp_sigma(mk, small, tf, k, d)

def run_tai(mk, big, mid, small, d, core_exit=('1h', '9割れ'), add_exit=None, maxpos=1, sao=2.0, n8=False, spr=0.003, reenter=False, kawa_chi=True,
            sl=None, tp=None, lock=0.0, lockcore=True, ts=0.0, ts_start=0.0):
    """鯛・クジラを1回まわす。sl=None/'prevday'/(足,線) tp=None/(足,σ) lock=しあわせセットの pips(0=なし)"""
    E = tai_entry(mk, big, mid, small, d, sao, n8, kawa_chi)
    XC, KC = EXITS[core_exit[1]](mk, small, core_exit[0], d)
    if add_exit: XA, KA = EXITS[add_exit[1]](mk, small, add_exit[0], d)
    else: XA, KA = XC, KC
    base = mk.feat(small)
    return simulate(base, d, E, XC, KC, XA, KA, make_sl(mk, small, d, sl), maxpos, spr, reenter, make_tp(mk, small, d, tp), lock, lockcore, ts, ts_start), base

# ---- 小魚(11-06)
def kozakana_ue(mk, d=1, maxpos=5, spr=0.003, lock=0.0):
    """上の小魚(クジラと同じ向き):4h終値が21の向き側の間に、1hの終値が4h21をまたいだ足/1hの921で入る(最大 maxpos 発)。4h終値が21の逆側で全部降り【置き換え】"""
    S = mk.feat('1h'); q = mk.on('1h', '4h', ['c', 'e21'])
    side = (q.c > q.e21) if d > 0 else (q.c < q.e21); side = side.fillna(False)
    over = ((S.c > q.e21) & (S.c.shift() <= q.e21)) if d > 0 else ((S.c < q.e21) & (S.c.shift() >= q.e21))
    up = S.e9 > S.e21; x9 = (up & ~up.shift(1, fill_value=False)) if d > 0 else (~up & up.shift(1, fill_value=False))
    E = (side & (over | x9)).values; X = (~side).values; K = S.k.values   # 降りは 4h が閉じた時に確定するので、1h の閉じた時刻で見てよい
    return simulate(S, d, E, X, K, None, None, None, maxpos, spr, True, None, lock), S

def gyakume_99(mk, tf, d=-1, spr=0.003):
    """逆目は99(11-06 たくちん「逆目は99でいったら?」):tf の9割れが出た最初の足で入り、逆の9割れ(9に戻った)で降りる【置き換え】"""
    F = mk.feat(tf)
    w_in = F.ware_b if d < 0 else F.ware_s; w_out = F.ware_s if d < 0 else F.ware_b
    E = (w_in & ~w_in.shift(1, fill_value=False)).values
    return simulate(F, d, E, w_out.values, F.k.values, None, None, None, 1, spr, False), F

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

def run_tai(mk, big, mid, small, d, core_exit=('1h', '9割れ'), add_exit=None, maxpos=1, sao=2.0, n8=False, spr=0.003, reenter=False, kawa_chi=True):
    E = tai_entry(mk, big, mid, small, d, sao, n8, kawa_chi)
    XC, KC = EXITS[core_exit[1]](mk, small, core_exit[0], d)
    if add_exit: XA, KA = EXITS[add_exit[1]](mk, small, add_exit[0], d)
    else: XA, KA = XC, KC
    base = mk.feat(small)
    return simulate(base, d, E, XC, KC, XA, KA, None, maxpos, spr, reenter), base

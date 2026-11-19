# 11-19 たくちん「エントリーは全部 無限リーチで」:クジラ以外(ドテン・鯛・押し目・しあわせのため)の上限も外す。1つずつと全部
import sys; sys.argv = ['x']
src = open('/home/user/-/engine/nyu/kenkyu/mon_hiroge.py').read().split("M = lambda")[0]
exec(src)
def build2(o):
    f = F0; KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=('4h', f['tp'][1]), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']),
              kai_k9=f['kai_k9'], big21_up=f['big21_up'], yasumi=f['yasumi'])
    NB = {**KW, 'narabi': f['narabi']}; rv = f['rev_maxpos']; tz = f['tai']
    P = [run_kujira(srv, 1, tuple(f['core_exit']), rev_maxpos=rv, **NB)[0].assign(d=1, bu='クジラ買い'),
         run_kujira(srv, -1, tuple(f['core_exit']), rev_maxpos=rv, **KW)[0].assign(d=-1, bu='クジラ売り'),
         run_doten(srv, 1, xtf='4h', rev_maxpos=rv, doten_maxpos=o.get('doten', 1), **KW)[0].assign(d=1, bu='ドテン'),
         run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': o.get('tai', 1), 'tp': None, 'ts': tz['ts'], 'ng_hours': tuple(tz['ng_hours'])})[0].assign(d=1, bu='鯛')]
    for d in (1, -1): P.append(run_oshime_d(srv, d, maxpos=o.get('osh', 5), yasumi=f['yasumi'])[0].assign(d=d, bu='押し目'))
    t = pd.concat(P, ignore_index=True)
    sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}; sz['tame_max'] = o.get('tame', sz['tame_max'])
    SH = pd.concat([run_shiawase(srv, d, yasumi=True, shuu_muki=d in f['shiawase']['shuu_muki'], **sz)[0].assign(d=d, bu='しあわせ') for d in f['shiawase']['dirs']], ignore_index=True)
    t = pd.concat([t, SH[SH.ent >= t.ent.min()]], ignore_index=True); t['ent'] = pd.to_datetime(t.ent); t['ext'] = pd.to_datetime(t.ext)
    return t.sort_values(['ent', 'ext']).reset_index(drop=True)
CASES = [('今', {}), ('ドテン 上限なし', {'doten': 99}), ('鯛 上限なし', {'tai': 99}), ('押し目 上限なし', {'osh': 99}), ('しあわせのため 上限なし', {'tame': 99}),
         ('全部 上限なし', {'doten': 99, 'tai': 99, 'osh': 99, 'tame': 99})]
b0 = build2({}); BK = key(b0); rows = []
for nm, o in CASES:
    t = b0 if not o else build2(o); rows.append(dict(形=nm, 変わる玉=len(key(t) ^ BK), **hyou(t), **nana(t)))
pd.set_option('display.width', 250); print(pd.DataFrame(rows).drop(columns=['クジラp']).to_string(index=False))

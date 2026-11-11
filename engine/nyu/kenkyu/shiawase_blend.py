# 11-11 たくちん「ご」:決まった形(クジラ3ブレンド)と、しあわせセット7回目(箱=レンジに入ってからの高安)を一緒に回す
# 【置き換え・照らす前に決めた】決まった形は今のまま(0.01ロット決め打ち、1玉 1p=10円)。しあわせセットは2通りの大きさで足すだけ(どちらも同じ決まり・大きさ違い):
#   A 1セット=0.01ロットぶん(1単位 1p=2.5円)/ B 1単位=0.01ロット(1セット=0.04ロット、1単位 1p=10円。MT の最小ロットで本当に置ける大きさ)
#   落ち込み率=10.2万円から、降りた時の損益を順に足した残高の、それまでの一番高い所からの下がり幅÷一番高い所。決まった形だけの時も同じ測り方で並べる
import sys, json, io, contextlib, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
D = sys.argv[1]; here = '/home/user/-/engine/nyu'
cfg = json.load(open(here + '/settei_kimari.json')); f = cfg['形']
srv = Market(load_cached(D), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
t, b = run_tai(srv, f['big'], f['mid'], f['small'], 1, tuple(f['core_exit']), **KW); t['d'] = 1
if f.get('uri'): u, _ = run_tai(srv, f['big'], f['mid'], f['small'], -1, tuple(f['core_exit']), **KW); u['d'] = -1; t = pd.concat([t, u], ignore_index=True)
if f.get('doten'): dz = f['doten']; dt_, _ = run_doten(srv, dz['d'], xtf=dz.get('xtf'), **KW); dt_['d'] = dz['d']; t = pd.concat([t, dt_], ignore_index=True)
if f.get('tai'): tz = f['tai']; KT = {**KW, 'maxpos': tz['maxpos'], 'tp': None, 'ts': tz['ts']}; tt_, _ = run_tai(srv, f['big'], f['mid'], f['small'], tz['d'], tuple(tz['exit']), **KT); tt_['d'] = tz['d']; t = pd.concat([t, tt_], ignore_index=True)
if f.get('oshime'):
    for dz in (1, -1): oo, _ = run_oshime_d(srv, dz, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False)); oo['d'] = dz; t = pd.concat([t, oo], ignore_index=True)
K = pd.DataFrame(dict(ent=pd.to_datetime(t.ent), ext=pd.to_datetime(t.ext), pips=t.pips.astype(float)))
g = {'__name__': '__main__'}; sys.argv = ['x', D]
with contextlib.redirect_stdout(io.StringIO()): exec(open(here + '/kenkyu/shiawase_hako2.py', encoding='utf-8').read(), g)
S = g['t']; S = pd.DataFrame(dict(ent=pd.to_datetime(S.ent), ext=pd.to_datetime(S.ext), pips=S.pips.astype(float)))
st = K.ent.min(); S = S[S.ent >= st]                                        # 決まった形と同じ始まり(研究台 2016/10〜)
def stat(parts):
    z = pd.concat(parts, ignore_index=True).sort_values('ext'); eq = 102000 + z.yen.cumsum(); pk = eq.cummax()
    y = z.ent.dt.year; tashika = ~y.between(2022, 2024)
    return f"{z.p1.sum():+,.0f}p / 確かめる年 {z.p1[tashika].sum():+,.0f} / 選22-24 {z.p1[~tashika].sum():+,.0f} / 円 {z.yen.sum():+,.0f} / 落ち込み率 {((pk-eq)/pk).max()*100:.1f}%"
k_ = K.assign(p1=K.pips, yen=K.pips * 10)
sA = S.assign(p1=S.pips / 4, yen=S.pips * 2.5); sB = S.assign(p1=S.pips, yen=S.pips * 10)
print('決まった形だけ        ', len(K), '玉', stat([k_]))
print('しあわせだけ(A)       ', stat([sA]))
print('一緒 A 1セット0.01ロット', stat([k_, sA]))
print('一緒 B 1単位0.01ロット ', stat([k_, sB]))
# 重なり:しあわせの単位を持っている間に、決まった形の玉も持っていた時間
hk = pd.Series(0, index=srv.bars('1h').index)
for a, c in zip(K.ent, K.ext): hk[a:c] += 1
ov = [(hk[a:c] > 0).mean() for a, c in zip(S.ent, S.ext)]
print(f"重なり:しあわせの単位が持っている時間のうち、決まった形の玉も持っていた割合 平均 {np.mean(ov)*100:.0f}%(全部重なった単位 {sum(o>=0.999 for o in ov)}/{len(ov)})")
yy = lambda z: z.groupby(z.ent.dt.year).p1.sum().round().astype(int).to_dict()
print('年ごと 決まった形', yy(k_)); print('年ごと しあわせA ', yy(sA))

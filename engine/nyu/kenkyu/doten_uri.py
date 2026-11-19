# 11-19 たくちん「ご」:逆向きのドテン(クジラ買いの利確 4時間+4σ で構え、1時間219が閉じた次の足で売り1玉。降りは4時間の新しい921・TS550)
# 今のドテン買いの鏡うつし【置き換え】。今の決まった形(988玉)に足した時と足さない時を、0.01決め打ち・資金10.2万円で比べる
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']; k = cfg['口座']
srv = Market(load_cached(sys.argv[1] if len(sys.argv) > 1 else '/home/user/data/mt4'), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']), kai_k9=f.get('kai_k9', 0), big21_up=f.get('big21_up', False), yasumi=f.get('yasumi', False))
NB = {**KW, 'narabi': f.get('narabi', False)}
P = []
x, b = run_tai(srv, '1D', '4h', '1h', 1, tuple(f['core_exit']), **NB); P.append(x.assign(d=1, bu='クジラ買い'))
x, _ = run_tai(srv, '1D', '4h', '1h', -1, tuple(f['core_exit']), **KW); P.append(x.assign(d=-1, bu='クジラ売り'))
x, _ = run_doten(srv, 1, xtf='4h', **KW); P.append(x.assign(d=1, bu='ドテン買い'))
tz = f['tai']; x, _ = run_tai(srv, '1D', '4h', '1h', 1, tuple(tz['exit']), **{**NB, 'maxpos': 1, 'tp': None, 'ts': tz['ts']}); P.append(x.assign(d=1, bu='鯛'))
for d in (1, -1): x, _ = run_oshime_d(srv, d, maxpos=f['oshime']['maxpos'], yasumi=f.get('yasumi', False)); P.append(x.assign(d=d, bu='押し目'))
t = pd.concat(P, ignore_index=True)
sz = {a: v for a, v in f['shiawase'].items() if a not in ('説明', 'dirs', 'shuu_muki')}
sh = pd.concat([run_shiawase(srv, d, yasumi=f.get('yasumi', False), shuu_muki=d in f['shiawase'].get('shuu_muki', []), **sz)[0].assign(d=d, bu='しあわせ') for d in f['shiawase'].get('dirs', [1, -1])], ignore_index=True)
t = pd.concat([t, sh[sh.ent >= t.ent.min()]], ignore_index=True)
DU, _ = run_doten(srv, -1, xtf='4h', **NB)              # 鏡:元はクジラ買い(日足の並びつき=決まった形の買いと同じ)
DU = DU.assign(d=-1, bu='ドテン売り')
# 構えの元が決まった形のクジラ買いと同じか(利確の玉の数)
print('構えの元 クジラ買いの利確', int((P[0].why == '利確').sum()), '回')
w = DU.pips
print(f'ドテン売り:{len(DU)}玉 勝率 {(w>0).mean()*100:.0f}% 合計 {w.sum():+,.0f}p 平均 {w.mean():+.0f}p 一番勝ち {w.max():+.0f} 一番負け {w.min():+.0f} 降り {DU.why.value_counts().to_dict()}')
y = pd.to_datetime(DU.ent).dt.year; print('  年ごと(p)', {int(a): int(round(v)) for a, v in w.groupby(y).sum().items()})
ys = pd.to_datetime(DU.ent).dt.year.between(2022, 2024); print(f'  選22-24 {w[ys].sum():+,.0f}p / 確かめる年 {w[~ys].sum():+,.0f}p')
dm = t[t.bu == 'ドテン買い'].pips; print(f'(比べ)ドテン買い:{len(dm)}玉 勝率 {(dm>0).mean()*100:.0f}% 合計 {dm.sum():+,.0f}p')
def kane(nm, T):
    T = T.copy(); T['ent'] = pd.to_datetime(T.ent); T['ext'] = pd.to_datetime(T.ext); T = T.sort_values(['ent', 'ext']).reset_index(drop=True)
    T2, s = lot_sizing(T, b, 1, k['資金'], margin_cap=k['証拠金の上限'], leverage=k['レバレッジ'], fixed_lot=k['決め打ちのロット'], stopout=k['強制決済の維持率'])
    yy = T2.groupby(pd.to_datetime(T2.ent).dt.year)['円'].sum()
    tm = ~pd.to_datetime(T2.ent).dt.year.between(2022, 2024)
    print(f'\n{nm}: 玉 {len(T2)} / {s}')
    print('   年ごと(円)', {int(a): int(round(v)) for a, v in yy.items()}, f'/ 確かめる年 {T2["円"][tm].sum():+,.0f}円 / 選22-24 {T2["円"][~tm].sum():+,.0f}円')
kane('今の決まった形', t)
kane('今の決まった形+ドテン売り', pd.concat([t, DU], ignore_index=True))
DU.to_csv('/home/user/-/engine/kekka_tai/nyu/ドテン売り_玉_20261119.csv', index=False)

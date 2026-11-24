# 11-23 たくちん「1時間の921・219で歩いて入り口出口きちんとやって」(一本照らし ichihon-terashi-921)
# 1時間足の9と21の交わり(買い=921・売り=219)を1か所も飛ばさず、合図の足1本ずつ ローソク・川(1σ)・9と21・遅行スパン(21本前)の4つで照らし、
# 門(日足9・4h21・遅行・川・竿先・日足21の傾き・並び・GW)の通り/止まりを書く。入った玉は出口の足も同じ4つで照らす。
# 別の目(aruki_zenbu の足と線=エンジンの部品なし)で決めた入り/降りと、エンジンの玉を1玉ずつ あわす
import sys, json, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0, '/home/user/-/engine/nyu')
D_ = sys.argv[1] if len(sys.argv) > 1 else '/home/user/data/mt4'
src = open('/home/user/-/engine/nyu/kenkyu/aruki_zenbu.py').read().split('# ====================================================== 2)')[0]
sys.argv = ['x', D_]; exec(src)
from nyu import Market, load_cached; from tai_parts import run_kujira
cfg = json.load(open('/home/user/-/engine/nyu/settei_kimari.json')); f = cfg['形']
srv = Market(load_cached(D_), 'server')
KW = dict(maxpos=f['maxpos'], n8=f['n8'], sao=f['sao'], reenter=True, tp=tuple(f['tp']), ts=f['ts'], avoid_in=tuple(f['avoid_in']), avoid_out=tuple(f['avoid_out']),
          kai_k9=f['kai_k9'], big21_up=f['big21_up'], yasumi=f['yasumi'])
ENG = {1: run_kujira(srv, 1, tuple(f['core_exit']), rev_maxpos=f['rev_maxpos'], **{**KW, 'narabi': f['narabi']})[0],
       -1: run_kujira(srv, -1, tuple(f['core_exit']), rev_maxpos=f['rev_maxpos'], **KW)[0]}
r3 = lambda v: None if np.isnan(v) else round(float(v), 3)
def yon(i, d):
    """足 i(確定足)の4つ:ローソク・川・9と21・遅行"""
    kawa = '上の外' if C[i] > md[i] + sd[i] else ('下の外' if C[i] < md[i] - sd[i] else '中')
    hami = '上はみ出し' if Hh[i] > md[i] + sd[i] and C[i] <= md[i] + sd[i] else ('下はみ出し' if Ll[i] < md[i] - sd[i] and C[i] >= md[i] - sd[i] else '')
    chi = '上抜け' if C[i] > h21[i] else ('下抜け' if C[i] < l21[i] else '絡み')
    return dict(足=str(idx[i]), 始=O[i], 高=Hh[i], 安=Ll[i], 終=C[i], 陽陰='陽' if C[i] > O[i] else ('陰' if C[i] < O[i] else '十字'),
                川=kawa + (f'({hami})' if hami else ''), 帯1σ上=r3(md[i] + sd[i]), 帯1σ下=r3(md[i] - sd[i]),
                e9=r3(e9[i]), e21=r3(e21[i]), e9前=r3(e9[i - 1]), e21前=r3(e21[i - 1]),
                終値と9='上' if C[i] > e9[i] else '下', 終値と21='上' if C[i] > e21[i] else '下',
                遅行21=chi, 比べた足=str(idx[i - 21]) if i >= 21 else '', 比べた高=r3(h21[i]), 比べた安=r3(l21[i]))
rows = []; tama = []
for d in (1, -1):
    up = e9 > e21; up1 = np.r_[False, up[:-1]]
    cross = (up & ~up1) if d > 0 else (~up & up1)
    p = ((dc > de9) & (fc > fe21)) if d > 0 else ((dc < de9) & (fc < fe21))
    E_ok = kujira_E(d, d > 0)          # 別の目の入り(0時は次の足へ)
    eng_ent = set(pd.to_datetime(ENG[d].ent).astype(str))
    for i in np.where(cross)[0]:
        if i < 30 or i >= n - 1: continue
        mon = [('日足終値が9の向こう', (dc[i] > de9[i]) if d > 0 else (dc[i] < de9[i])),
               ('4時間終値が21の向こう', (fc[i] > fe21[i]) if d > 0 else (fc[i] < fe21[i])),
               ('川(1σ)の外', (C[i] > md[i] + sd[i]) if d > 0 else (C[i] < md[i] - sd[i])),
               ('遅行21抜け', (C[i] > h21[i]) if d > 0 else (C[i] < l21[i])),
               ('竿先±2σの内', (C[i] <= md[i] + 2 * sd[i]) if d > 0 else (C[i] >= md[i] - 2 * sd[i])),
               ('日足21が入る向き', (dang[i] > 0) if d > 0 else (dang[i] < 0)),
               ('日足921の並び(買いだけ)', (de9[i] > de21[i]) if d > 0 else True),
               ('GWでない', not GW[i])]
        tomari = [m for m, ok in mon if not bool(np.nan_to_num(ok))]
        ireru = not tomari
        j = i + 1
        while ireru and nxh[j - 1] == 0 and j < n - 1: j += 1     # 0時の足はよけて次の足
        e_eng = str(idx[j]) in eng_ent
        rows.append(dict(向き='買い921' if d > 0 else '売り219', **yon(i, d), 判定='入る' if ireru else '入らない', 止めた門='・'.join(tomari),
                         入る足=str(idx[j]) if ireru else '', エンジン=('入った' if e_eng else '入らない'),
                         あわせ='○' if ireru == e_eng else ('?許しの入りと同じ足' if (not ireru and e_eng) else '×')))
    # 入った玉(921・許し 全部)の入口と出口を4つで照らす
    W = KUJ[d]
    for _, t in W.iterrows():
        si = int(t.sig); xi = int(np.searchsorted(T, np.datetime64(t.ext))); xs = xi - 1 if t.why in ('芯の降り', '足しの降り') else xi
        kind = '921' if ((e9[si] > e21[si]) != (e9[si - 1] > e21[si - 1])) else '許し'
        en = ENG[d][(pd.to_datetime(ENG[d].ent) == t.ent)]
        ok = len(en) and any(abs(en.e - t.e) < 1e-6) and any(pd.to_datetime(en.ext) == t.ext)
        a = {('入口_' + k): v for k, v in yon(si, d).items()}; b = {('出口_' + k): v for k, v in yon(xs, d).items()}
        tama.append(dict(向き='買い' if d > 0 else '売り', 種類=kind, 入った足=str(t.ent), 入り値=round(t.e, 3), 降りた足=str(t.ext), 降り値=round(t.x, 3), 理由=t.why,
                         pips=round((t.x - t.e) / 0.01 * d, 1), エンジンとあわせ='○' if ok else '×', **a, **b))
R = pd.DataFrame(rows); TM = pd.DataFrame(tama)
out = '/home/user/-/engine/kekka_tai/nyu'
R.to_csv(f'{out}/ichihon_1h921_219_kouho.csv', index=False, encoding='utf-8-sig'); TM.to_csv(f'{out}/ichihon_1h921_219_tama.csv', index=False, encoding='utf-8-sig')
print('■ 1時間の921・219 合図の足(1か所も飛ばさず)')
print(R.groupby(['向き', '判定', 'あわせ']).size().to_string())
print('\n■ 止めた門(1つ目でなく、止めた門ぜんぶを数える)')
for d in ('買い921', '売り219'):
    s = R[(R.向き == d) & (R.判定 == '入らない')].止めた門.str.split('・').explode().value_counts(); print(d, s.to_dict())
print('\n■ 4つの照らしで抜けた所(値が無い足)', int(R[['帯1σ上', 'e9', 'e21', '比べた高']].isna().any(axis=1).sum()))
print('\n■ 入った玉の入口〜出口(別の目)とエンジン')
print(TM.groupby(['向き', '種類', 'エンジンとあわせ']).size().to_string())
print('\n■ 降りた理由', TM.groupby(['向き', '理由']).size().to_dict())
x = R[R.あわせ == '×']; print('\n■ ×(別の目とエンジンが違う合図の足)', len(x)); print(x[['向き', '足', '判定', '止めた門', 'エンジン']].head(20).to_string(index=False))

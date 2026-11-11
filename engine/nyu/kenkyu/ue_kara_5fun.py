# 11-11 たくちん「上からロウソク921で5で合わしてエントリー 21のうえを取りに行くんやで 21のうえにおるロウソク」
# 【置き換え・照らす前に決めた】
#   上から:日足・4時間・1時間の3つとも、閉じた足で 9>21 かつ 終値が9の上(ロウソクが青の上・青が赤の上)。売りは鏡うつし
#   5で合わす:5分足の新しい921(9が21を上抜けて閉じた足)で、終値が5分の9の上 → 次の5分足の始値で1発。上の3つがそろっている間は5分の921のたびに足す(無限リーチ・最大5発)
#   21のうえを取る:日足のロウソク(終値)が日足21の下で閉じたら全部降りる(売りは上)。利確・TS・網は無し。0時の入り降りは1時へ。スプレッド0.3p
# 11-11「ご」2本目:上を週足まで1段伸ばす=週足も閉じた週で 9>21 かつ 終値が9の上(売りは逆)の時だけ入る。週足=月曜0時からの7日足(閉じた週だけ)
# 11-11 たくちん「週足までみんでも 日足でとれん？ 四時間、ならだましほとんどないけどな」3本目:週足は外す。1本目に、4時間の帯が開いている(直近に閉じた4時間足で +2σ が上がり −2σ が下がった)時だけ5分で入る、を1つ足す
# 11-11 たくちん「下りからのレンジ 遅刻スパン見てない証拠」(2017年の日足に印:1月・4月の帯の閉じ始め、5月〜12月の108〜114円の箱)4本目:1本目に、日足の遅行スパン(今の終値が21本前の日足の高値より上・売りは安値より下=遅行スパンがロウソクに絡んでいない)の時だけ入る、を1つ足す
# データ:HistData 1分足(EST)を7時間ずらしてサーバー時刻にした物(1時間足の終値の差 0.2〜0.4p で合わせ済み)。2015/01〜2025/04。5分足の有る所だけ
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
fine=load_cached(sys.argv[1]).copy(); fine.index=fine.index+pd.Timedelta(hours=7)
mk=Market(fine,'server'); SPR=0.003; SHUU=False; HIRAKU=False; CHIKOU=False
B=mk.feat('5min')
def run(d):
    x=B; up=(x.e9>x.e21) if d>0 else (x.e9<x.e21); c9=(x.c>x.e9) if d>0 else (x.c<x.e9)
    cross=(up&~up.shift(1,fill_value=False)&c9).values
    ok=np.ones(len(x),bool)
    for tf in ('1h','4h','1D'):
        y=mk.on('5min',tf,['c','e9','e21'])
        ok&=(((y.e9>y.e21)&(y.c>y.e9)) if d>0 else ((y.e9<y.e21)&(y.c<y.e9))).fillna(False).values
    if SHUU:
        AGG={'o':'first','h':'max','l':'min','c':'last'}
        W=fine.resample('7D',origin=pd.Timestamp('2015-01-05')).agg(AGG).dropna(); W['k']=W.index+pd.Timedelta('7D')
        W['e9']=W.c.ewm(span=9,adjust=False).mean(); W['e21']=W.c.ewm(span=21,adjust=False).mean()
        yw=pd.merge_asof(pd.DataFrame({'kb':x.k.values}),W[['k','c','e9','e21']].sort_values('k'),left_on='kb',right_on='k',direction='backward')
        ok&=(((yw.e9>yw.e21)&(yw.c>yw.e9)) if d>0 else ((yw.e9<yw.e21)&(yw.c<yw.e9))).fillna(False).values
    if HIRAKU:
        F=mk.feat('4h'); ub=F.md+2*F.sd; lb=F.md-2*F.sd; kc='hiraku4'
        if kc not in F.columns: mk._f['4h']=F.assign(hiraku4=(ub>ub.shift(1))&(lb<lb.shift(1)))
        ok&=mk.on('5min','4h',[kc])[kc].fillna(False).astype(bool).values
    if CHIKOU:
        yd2=mk.on('5min','1D',['c','h21','l21'])
        ok&=((yd2.c>yd2.h21) if d>0 else (yd2.c<yd2.l21)).fillna(False).values
    E=cross&ok
    fh=np.r_[x.index.hour.values[1:],-1]
    E=E.copy()
    for i in np.where(E&(fh==0))[0]:
        E[i]=False; k=i+1
        while k<len(E)-1 and fh[k]==0: k+=1
        E[k]=True
    yd=mk.on('5min','1D',['c','e21']); XC=(((yd.c<yd.e21) if d>0 else (yd.c>yd.e21)).fillna(False).values)&~(fh==0); KC=yd['k_1D'].values
    t=simulate(x,d,E,XC,KC,None,None,None,5,SPR,True)
    return t
for SHUU,HIRAKU,CHIKOU,NM in [(False,False,False,'1本目(日足・4時間・1時間)'),(False,False,True,'4本目(日足の遅行スパンがロウソクに絡んでいない時だけ)')]:
    t=pd.concat([run(1).assign(d=1),run(-1).assign(d=-1)],ignore_index=True); y=pd.to_datetime(t.ent).dt.year
    t=t[pd.to_datetime(t.ent)>='2015-06-01']; y=pd.to_datetime(t.ent).dt.year
    st=stat(t)
    print(f"{NM} 上からそろえて5分の921で入り、日足のロウソクが21の下で閉じたら降りる:{st['n']}玉 {st['sum']:+,.0f}p PF{st['pf']} 勝ち {st['win']}")
    print(f"  選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} / 確かめる年(15-21・25) {t.pips[~y.between(2022,2024)].sum():+,.0f}")
    print('  年ごと',{int(k):round(v) for k,v in t.groupby(y).pips.sum().items()})
    print('  買い',stat(t[t.d==1]),' 売り',stat(t[t.d==-1]))
    # 山ごと(同じ日足の流れの玉をまとめる=降りた時刻で)
    g=t.groupby(['d','ext']).agg(玉=('pips','size'),合計=('pips','sum'),最初=('ent','min')).reset_index()
    w=g.合計>0; print(f'  流れ {len(g)}回:勝ち {int(w.sum())} +{g.合計[w].sum():,.0f}p / 負け {int((~w).sum())} {g.合計[~w].sum():,.0f}p')
    print('--- 歩き:2017年(印を付けた年)---')
    for r in g[(g.最初>='2017-01-01')&(g.最初<'2018-01-01')].itertuples(): print(f"  {'買い' if r.d>0 else '売り'} {r.最初:%m/%d %H:%M} から {r.玉}玉 → {pd.Timestamp(r.ext):%m/%d %H:%M} 降り {r.合計:+,.0f}p")
    # 参考:同じ期間(2016/03〜2025/04)の今の決まった形

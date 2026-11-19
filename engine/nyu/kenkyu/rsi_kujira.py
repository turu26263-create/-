# 11-11 たくちん「ＲＳＩ組みあわしても」「極めて優位性の……はよんだ？」
# 極めて優位性の高いサイン(TrendingSignEX)説明書のだまし:「3波以上の強いトレンドが進んだ後」「長期EMAとレートが大きく乖離」「大きなローソク足で急上昇した直後」はサインが出てもスルー。押し目は「トレンドの中の買われすぎ・売られすぎ」をオシレーター(ストキャス)で見る
# 【置き換え】オシレーターは RSI(14・ワイルダー)。クジラの入り(1発目〜5発目)のうち、入る1時間足が閉じた時の4時間足 RSI が 70 を超えている(売りは 30 未満)=買われすぎ・乖離の所では入らない。70/30 は RSI のふつうの目安。ほかは今の形のまま
import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *; from bugbug import bugbug
raw=load_cached(sys.argv[1])
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',4.0),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
def rsi(c,n=14):
    d_=c.diff(); up=d_.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); dn=(-d_.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean(); return 100-100/(1+up/dn)
def put_rsi(mk, on=True):
    F=mk.feat('4h')
    if 'rsi' not in F.columns: mk._f['4h']=F.assign(rsi=rsi(F.c))
    r=mk.on('1h','4h',['rsi']).rsi.values
    for d in (1,-1):
        key=('tai_entry','1D','4h','1h',d,2.0,False,True,3,True,False)
        mk._f.pop(key,None); E=tai_entry(mk,'1D','4h','1h',d,2.0,False,True,kai_k9=3,big21_up=True)
        if on: mk._f[key]=E&~((r>70) if d>0 else (r<30))
    return r
def blend(mk):
    b,base=run_tai(mk,'1D','4h','1h',1,('1D','219'),**K); s,_=run_tai(mk,'1D','4h','1h',-1,('1D','219'),**K); dt,_=run_doten(mk,1,xtf='4h',**K)
    tb,_=run_tai(mk,'1D','4h','1h',1,('4h','9割れ'),**{**K,'maxpos':1,'tp':None}); ob,_=run_oshime_d(mk,1); os_,_=run_oshime_d(mk,-1)
    for t,k,d in [(b,'買い',1),(s,'売り',-1),(dt,'ドテン買い',1),(tb,'鯛',1),(ob,'押し目買い',1),(os_,'押し目売り',-1)]: t['kind']=k; t['d']=d
    return pd.concat([b,s,dt,tb,ob,os_],ignore_index=True),base
def mk_(on): m=Market(raw,'server'); r=put_rsi(m,on); return m,r
ok,L=bugbug(lambda m,d: (put_rsi(m,True), run_tai(m,'1D','4h','1h',d,('1D','219'),**K)[0])[1],raw,'server',5,0.003)
print('修正機:','全部○' if ok else '×あり'); [print('  ',l) for l in L if l.startswith('×')]
print('決め方(先に決めた・前と同じ):確かめる年の合計が上がり、落ち込み率が上がらなければ残す')
res={}
for nm,on in [('今の形',False),('4時間RSIが70超(売りは30未満)の所ではクジラに入らない',True)]:
    m,r=mk_(on); t,base=blend(m); y=pd.to_datetime(t.ent).dt.year; _,st=lot_sizing(t,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    f=lambda k: f"{int((t.kind==k).sum())}玉 {t.pips[t.kind==k].sum():+,.0f}p"
    print(f"  {nm}:\n     買い {f('買い')} / 売り {f('売り')} / ドテン買い {f('ドテン買い')} / 鯛 {f('鯛')} / 全部 {len(t)}玉 {t.pips.sum():+,.0f}p 選22-24 {t.pips[y.between(2022,2024)].sum():+,.0f} 確かめる年 {t.pips[y.between(2016,2021)|(y>=2025)].sum():+,.0f} 落ち込み率 {st['落ち込み率']}%")
    res[on]=(t,m,r)
t0,m0,r0=res[False]; t1=res[True][0]
for k,d in [('買い',1),('売り',-1)]:
    a=t0[t0.kind==k].copy(); idx=m0.feat('1h').index; a['rsi']=r0[np.searchsorted(idx.values,pd.to_datetime(a.ent).values)-1]
    hit=(a.rsi>70) if d>0 else (a.rsi<30)
    print(f'今の形の{k}で、入る時に4時間RSIが{"70超" if d>0 else "30未満"}だった玉:{int(hit.sum())}玉 {a.pips[hit].sum():+,.0f}p(勝ち {int((a.pips[hit]>0).sum())})/それ以外 {int((~hit).sum())}玉 {a.pips[~hit].sum():+,.0f}p')
    print('   一番得した5玉:',' '.join(f'{x.ent:%Y/%m/%d} {x.pips:+.0f}p(RSI{x.rsi:.0f})' for x in a[hit].nlargest(5,'pips').itertuples()))
    print('   一番損した5玉:',' '.join(f'{x.ent:%Y/%m/%d} {x.pips:+.0f}p(RSI{x.rsi:.0f})' for x in a[hit].nsmallest(5,'pips').itertuples()))

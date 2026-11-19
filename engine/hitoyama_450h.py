# 450時間足の大山ひと山だけ(11-06 たくちん「450hも日足と同じようにおおやまだけやる」)
# データ:Drive の MT4 1時間足 USDJPY60.csv(サーバー時刻)。450時間足=暦の450時間ごと(1970-01-01 0時から)【置き換え】
# 山=450hの9が21を上抜けた(921)〜下抜けた(219)。一番大きい上げの山を1つだけ見る
# 形:450hの9上・日足の21上・1hで入る(縄4〜5・縄8は450h)。最大5発・損切りなし・450hの219で全部降りる
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
import engine_tai_g as G
from engine_tai_g import *
from engine_kujira import attach2,run_k
def bars_srv(m1,tf):
    if tf=='450h': b=m1.resample('450h',origin='epoch').agg(AGG).dropna(); b['k']=b.index+pd.Timedelta('450h'); return b
    f='1D' if tf=='1D' else tf; b=m1.resample(f).agg(AGG).dropna(); b['k']=b.index+pd.Timedelta(f); return b
G.bars=bars_srv
m1=load(sys.argv[1])
B=bars_srv(m1,'450h'); B['e9']=ema(B.c,9); B['e21']=ema(B.c,21); up=B.e9>B.e21
seg=(up!=up.shift()).cumsum(); rows=[]
for s_,g in B[up].groupby(seg[up]):
    if len(g)<2: continue
    i0=g.index[0]; i1=g.index[-1]; rows.append((i0,B.k[i1]+pd.Timedelta('450h'),g.l.min(),g.h.max(),(g.h.max()-g.l.min())*100,len(g)))
yama=pd.DataFrame(rows,columns=['921の足','219の確定(次の足の終わり)','安値','高値','幅p','本数']).sort_values('幅p',ascending=False)
print('450時間足の上げの山(921〜219)'); print(yama.head(5).to_string(index=False))
a,b=yama.iloc[0]['921の足'],yama.iloc[0]['219の確定(次の足の終わり)']
x=G.prep(m1,'450h','1D','1h')
x=attach2(x,pd.DataFrame({'b_k':B.k,'b_wb':B.e9<B.e21,'b_ws':False}),'b_'); x['a_wb']=False; x['a_ws']=False; x['a_k']=x['b_k']
t=run_k(x,1,G.signals(x,1,2.0,True),'kujira',5,spr=0.003)
y=t[(t.ent>=a)&(t.ent<=b)]
print(f'\n大山 {a:%Y/%m/%d}〜{b:%Y/%m/%d} 安値{yama.iloc[0].安値:.3f} 高値{yama.iloc[0].高値:.3f}(幅{yama.iloc[0].幅p:.0f}p)。玉',len(y),'合計',round(y.pips.sum(),1),'p')
for _,r in y.iterrows():
    e=x.loc[:r.ent].iloc[-2]
    print(f"  {r.n}発目 {r.ent:%Y/%m/%d %H時} {r.e:.3f} → {r.ext:%Y/%m/%d %H時} {r.x:.3f} {r.pips:+.1f}p | 合図の足:450hC{e.q_c:.3f} 1h C{e.c:.3f} 9={e.e9:.3f} 21={e.e21:.3f}")

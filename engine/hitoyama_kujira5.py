# 大山ひと山だけ(11-06 たくちん「わからんやつやな 大山ひとやま だけ」)
# 山:2025/9/19(921)〜2026/1/26(219) ドル円 146.3→159.4(前のチャットの「日足ひと山」と同じ山)
# データ:Drive の MT4 1時間足 USDJPY60.csv(サーバー時刻。日足はサーバー時刻の0時で区切る=業者の日足)
# 形:クジラの刺身5発=日足版の鯛の合図(日足の9上・4hの21上・1hで入る・縄4〜5・縄8)で足す(最大5発)・損切りなし・日足の終値が9の下で確定したら全部降りる
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
import engine_tai_g as G
from engine_tai_g import *
from engine_kujira import attach2,run_k
def bars_srv(m1,tf):
    b=m1.resample('1D' if tf=='1D' else tf).agg(AGG).dropna(); b['k']=b.index+pd.Timedelta('1D' if tf=='1D' else tf); return b
G.bars=bars_srv
m1=load(sys.argv[1])
D=bars_srv(m1,'1D'); D['e9']=ema(D.c,9); mid=(D.o+D.c)/2
x=G.prep(m1,'1D','4h','1h')
mode=sys.argv[2] if len(sys.argv)>2 else '終値'
D['e21']=ema(D.c,21)
wb=(D.c<D.e9) if mode=='終値' else (D.e9<D.e21) if mode=='219' else ((mid<D.e9)&(D.c<D.e9))   # '219'=日足の9が21を下抜けた(山の終わり)
x=attach2(x,pd.DataFrame({'b_k':D.k,'b_wb':wb,'b_ws':False}),'b_'); x['a_wb']=False; x['a_ws']=False; x['a_k']=x['b_k']
ent=G.signals(x,1,2.0,True)
t=run_k(x,1,ent,'kujira',5,spr=0.003)
y=t[(t.ent>='2025-09-19')&(t.ent<='2026-01-27')]
print(f'山 2025/9/19〜2026/1/26(146.3→159.4 約1,310p)。降り=日足の{mode}。玉',len(y),' 合計',round(y.pips.sum(),1),'p')
for c,g in y.groupby('camp'):
    print(f'-- クジラ{c} --')
    for _,r in g.iterrows():
        e=x.loc[:r.ent].iloc[-2]   # 合図の1h足(入る1本前)
        print(f"  {r.n}発目 {r.ent:%m/%d %H時} {r.e:.3f} → {r.ext:%m/%d %H時} {r.x:.3f} {r.pips:+.1f}p | 合図の足:日足C{e.q_c:.3f}(9の上) 4hの21上 1h C{e.c:.3f} 9={e.e9:.3f} 21={e.e21:.3f}")
D2=D.loc['2025-09-15':'2026-01-30']
print('\n日足の終値と9(山の間で 終値が9の下の日)')
print(', '.join(f"{i:%m/%d} C{r.c:.3f}<9 {r.e9:.3f}" for i,r in D2[D2.c<D2.e9].iterrows()))

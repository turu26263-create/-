# B:日足の鯛の刺身のプログラムの照らし(11-06「bも」)
# 1) 先読みの照らし:データを途中で切って回し、切った日より前の戦が全期間の時と1戦も違わないか
# 2) 入りの照らし:1戦ずつ、入る前の足(確定足)だけで条件を計算し直して、全部そろっているか(別に書いた計算で)
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
m1=load(sys.argv[1])
def go(m):
    x=add_exit(prep(m,'1D','4h','1h'),m,'4h'); return run(x,1,signals(x,1,2.0,True)),x
full,x=go(m1)
for cut in ('2017-06-01','2020-03-15','2023-01-10'):
    p,_=go(m1[m1.index<cut]); f=full[pd.to_datetime(full.ext)<pd.Timestamp(cut)-pd.Timedelta('2D')]; q=p[pd.to_datetime(p.ext)<pd.Timestamp(cut)-pd.Timedelta('2D')]
    same=len(f)==len(q) and (f.ent.values==q.ent.values).all() and (abs(f.pips.values-q.pips.values)<1e-9).all()
    print('先読み照らし 切った日',cut,'戦',len(f),'同じ' if same else '違う!!')
# 2) 別の計算:pandas で日足・4h・1h を作り直して条件を見る
D=bars(m1,'1D'); D['e9']=ema(D.c,9); H4=bars(m1,'4h'); H4['e21']=ema(H4.c,21); H1=bars(m1,'1h'); H1['e9']=ema(H1.c,9); H1['e21']=ema(H1.c,21)
bad=0
for _,r in full.iterrows():
    t=pd.Timestamp(r.ent)                      # 入った足の始まり=合図の足が閉じた時刻
    d=D[D.k<=t].iloc[-1]; h4=H4[H4.k<=t].iloc[-1]; h1=H1[H1.k<=t].iloc[-1]
    ok=(d.c>d.e9) and (h4.c>h4.e21) and (h1.e9>h1.e21)
    if not ok: bad+=1
print('入りの照らし',len(full),'戦のうち 条件(日足の9上・4hの21上・1hの9>21)が欠けている戦',bad)

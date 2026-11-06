# 小魚=4時間の21の上と下(11-06 たくちん「小魚四時間の21のうえしたは取れるはす」)
# クジラの間だけ(日足:2025/09/19〜2026/01/27、450h:2021/03/26〜2025/04/15)。データ MT4 1時間足(サーバー時刻)
# 【置き換え】上の小魚(買い):確定4h足の終値が4hEMA21の上の間に、1hの合図(1hの終値が4h21を下から上へまたいだ確定足/1hの921)で入る。最大5発。確定4h足の終値が21の下で全部降りる
#             下の小魚(売り):鏡うつし。spr0.3
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai_g import *
from engine_kujira import attach2
m1=load(sys.argv[1])
h=m1.resample('1h').agg(AGG).dropna(); h['k']=h.index+pd.Timedelta('1h'); h['kakutei']=h.k; h['e9']=ema(h.c,9); h['e21']=ema(h.c,21)
F=m1.resample('4h').agg(AGG).dropna(); F['k']=F.index+pd.Timedelta('4h'); F['e21']=ema(F.c,21); F['up']=F.c>F.e21
x=attach2(h,F[['k','c','e21','up']].rename(columns=lambda c:'F_'+c),'F_')
up=x.F_up.fillna(False).astype(bool)
def run(d,a,b,MAX=5,spr=0.003):
    side=up if d>0 else ~up
    over=(x.c>x.F_e21)&(x.c.shift()<=x.F_e21) if d>0 else (x.c<x.F_e21)&(x.c.shift()>=x.F_e21)
    x9=(x.e9>x.e21)&(x.e9.shift()<=x.e21.shift()) if d>0 else (x.e9<x.e21)&(x.e9.shift()>=x.e21.shift())
    ent=(side&(over|x9)).values; S=side.values; FK=x.F_k.values; O=x.o.values; T=x.index.values
    pos=[]; tr=[]; i0=np.searchsorted(T,np.datetime64(a)); i1=np.searchsorted(T,np.datetime64(b))
    for i in range(i0,i1):
        if pos and not S[i]:
            for j,e in pos: ex=O[i+1]+(0 if d>0 else spr); tr.append((T[j],e,T[i+1],ex,(ex-e)*100*d))
            pos=[]
        if ent[i] and S[i] and len(pos)<MAX: pos.append((i+1,O[i+1]+(spr if d>0 else 0)))
    for j,e in pos: ex=O[i1]+(0 if d>0 else spr); tr.append((T[j],e,T[i1],ex,(ex-e)*100*d))   # 山の終わりで残りは降りる
    return pd.DataFrame(tr,columns=['ent','e','ext','x','pips'])
for nm,a,b,kj in (('日足のクジラ','2025-09-19','2026-01-27',1936.7),('450hのクジラ','2021-03-26','2025-04-15 18:00',16604.3)):
    print(f'\n=== {nm} {a}〜{b}(クジラ5発 {kj:+.1f}p)===')
    tot=0
    for d,nn in ((1,'上の小魚(買い)'),(-1,'下の小魚(売り)')):
        t=run(d,a,b); w=t.pips>0; tot+=t.pips.sum()
        print(f"{nn}:玉{len(t)} 勝ち{w.sum()} 負け{(~w).sum()} 合計{t.pips.sum():+.1f}p(勝ち{t.pips[w].sum():+.1f} 負け{t.pips[~w].sum():+.1f})")
        t.to_csv(f"engine/kekka_tai/hitoyama/小魚4h21_{nm}_{'buy' if d>0 else 'sell'}.csv",index=False)
    print(f"小魚 上+下 {tot:+.1f}p → クジラ+小魚 {kj+tot:+.1f}p")

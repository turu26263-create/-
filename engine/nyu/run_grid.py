# ニューぶん回しエンジンで回す(例:鯛の刺身)。選ぶ年 2022-24/確かめる年 2015-21・2025/スプレッド 0.5p と 1.0p(解析スピードアップの決まり)/台地の印
# 使い方: python3 run_grid.py <HistData 1分足の置き場> <書き出し先>
import sys, time, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
mk=Market(load_csv_dir(sys.argv[1]),'est'); out=sys.argv[2]
LADDER={'4h段(4h/1h/5分)':('4h','1h','5min','1h'),'日足段(日足/4h/1h)':('1D','4h','1h','4h')}
def fn(段,向き,玉,足しの降り,竿先,縄8,spr):
    big,mid,small,ex=LADDER[段]; d=1 if 向き=='買い' else -1
    core=(big,'9割れ') if 玉>1 else (ex,'9割れ')                     # 玉が1つ=鯛(1段下の9割れ)/足す時の芯=クジラ(段の上の足の9割れ)
    add=(ex,'9割れ') if 足しの降り=='1段下' else None
    t,base=run_tai(mk,big,mid,small,d,core,add,玉,竿先,縄8,spr,reenter=玉>1)
    return report(t,base,d)
space=dict(段=list(LADDER),向き=['買い','売り'],玉=[1,5,20],足しの降り=['芯と同じ','1段下'],竿先=[2.0,2.5],縄8=[False,True],spr=[0.005,0.01])
t0=time.time(); df=grid(fn,space); print('回した組',len(df),'通り',round(time.time()-t0,1),'秒')
df=df[~((df.玉==1)&(df.足しの降り=='1段下'))]                                # 玉1つの時は足しが無いので同じ物を消す
df=daichi(df,['竿先'],'確15-21_p')
cols=['段','向き','玉','足しの降り','竿先','縄8','spr','全_p','全_pf','選22-24_p','確15-21_p','確15-21_pf','確25_p','含み損込みDD','同時最大','台地']
df[cols].to_csv(out+'/ぶん回し_鯛.csv',index=False)
for 向き in ('買い','売り'):
    z=df[(df.向き==向き)&(df.spr==0.01)&(df['選22-24_p']>0)&(df['確15-21_p']>0)].sort_values('確15-21_p',ascending=False)
    print(f'\n--- {向き}:スプレッド1.0pで 選ぶ年も確かめる年もプラスの組(確かめる年の順) 上10 ---'); print(z[cols].head(10).to_string(index=False))

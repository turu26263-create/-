# 位置関係エンジン 第2版(たくちん 11-05 の決まりを全部入れた)
# 1) ドテン: 1時間足の実体が9の向こう側に渡り切って確定(【置き換え】実体の真ん中と終値が9の向こう)した時だけ向きを変える
#    終値が9をまたいだだけ(毛1本)の時は、元の向きの入り・足しを止める
# 2) 5エントリ: 確定5分足が「ひげが21に触れた・終値が9の向き側・9と21が向き側・竿先(±2σ外)でない」→ 次の始値
# 3) 方向あわせ: 4時間足の終値が21の向き側 かつ 1時間足21の傾きが向き側
# 4) 足し: 2) と 3) を満たし、前の玉から20pips   5) 網: 5分22本の高安 − 4hATR14×3
from sim4 import *
from engine_ichi import run_ichi
def prep_v2(m5,h1):
    m=m5.copy(); idx=m.index; c=m.c
    e9,e21=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    sellok=(m.h>=e21)&(c<e9)&(e9<e21)&(c>=mid-2*sd)
    buyok =(m.l<=e21)&(c>e9)&(e9>e21)&(c<=mid+2*sd)
    b4=bigbars(h1,'4h'); s4=to_m5(pd.Series(np.sign(b4.c-ema(b4.c,21)).values,index=b4.index),'4h',idx)
    s1=to_m5(pd.Series(np.sign(ema(h1.c,21).diff()).values,index=h1.index),'1h',idx)
    sellok&=(s4<0)&(s1<0); buyok&=(s4>0)&(s1>0)
    # 毛1本でも1時間足の終値が9をまたいだら、元の向きの入り・足しは止める
    e91=ema(h1.c,9); side1=to_m5(pd.Series(np.sign(h1.c-e91).values,index=h1.index),'1h',idx)
    sellok&=(side1<0); buyok&=(side1>0)
    m['pos5']=pd.Series(np.where(sellok,-1,np.where(buyok,1,0)),index=idx).shift(1)
    # 1時間足の向き(実体が9の向こうに渡り切った足で切り替わる)
    # 渡り切り【置き換え】= 実体の真ん中が9の向こう側(大体そのあたり)
    bm=(h1.o+h1.c)/2; full_up=(bm>e91)&(h1.c>e91); full_dn=(bm<e91)&(h1.c<e91)
    st=pd.Series(np.where(full_up,1.0,np.where(full_dn,-1.0,np.nan)),index=h1.index).ffill().fillna(0)
    m['dir1h']=to_m5(st,'1h',idx)
    a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    return m.dropna()
if __name__=='__main__':
    m5,h1=load(); lg=run_ichi(prep_v2(m5,h1)); lg.to_pickle('ichi_v2.pkl'); J=pd.Timedelta(hours=14)
    marks=[('A','01/05〜01/07 下げと戻り(直すとこ)','2017-01-04 16:00','2017-01-07 08:00'),
           ('F','01/11 22時 116.87 → 01/12 14時 113.76 下げ','2017-01-11 06:00','2017-01-13 00:00'),
           ('G','01/13 22時 115.44 → 01/18 06時 112.56 下げ','2017-01-13 06:00','2017-01-18 18:00'),
           ('B','01/19 02時 113.33 → 01/20 02時 115.62 上げ','2017-01-18 10:00','2017-01-20 12:00'),
           ('C','01/21 02時 115.20 → 01/24 06時 112.52 下げ','2017-01-20 10:00','2017-01-24 18:00'),
           ('D','01/26 14時 113.23 → 01/27 22時 115.37 上げ','2017-01-25 22:00','2017-01-27 18:00'),
           ('E','01/30 06時 114.95 → 02/02 22時 112.05 下げ','2017-01-29 14:00','2017-02-02 12:00')]
    for nm,desc,a0,a1 in marks:
        x=lg[(lg.close>=a0)&(lg.open<a1)]
        print(f'== 印{nm} {desc}  エンジン合計 {x.pips.sum():+.1f}p')
        for cp,g in x.groupby('camp'):
            print(f"   戦{cp} {g.dir.iloc[0]} {len(g)}発 入 {(g.open.min()+J):%m/%d %H:%M} {g.entry.iloc[0]:.3f} → 降 {(g.close.max()+J):%m/%d %H:%M} {g.exit.iloc[-1]:.3f} {g.why.iloc[-1]} {g.pips.sum():+.1f}")

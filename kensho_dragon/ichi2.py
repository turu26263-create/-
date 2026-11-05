# 位置関係エンジン + スキルの決まり(1つずつ入/切)
import sys
from sim4 import *
from engine_ichi import run_ichi
def prep2(m5,h1,TOUCH=9,SAO=2.0,BOMB=False,DOTEN='1h'):
    m=m5.copy(); idx=m.index; c=m.c
    e9,e21=ema(c,9),ema(c,21); et=e9 if TOUCH==9 else e21; mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    sellok=(m.h>=et)&(c<e9)&(e9<e21)&(c>=mid-SAO*sd)
    buyok =(m.l<=et)&(c>e9)&(e9>e21)&(c<=mid+SAO*sd)
    if BOMB:   # 爆弾岩=アストロン: 1時間足のボリ帯がしぼんでいる(ふだん100本の0.7倍未満)時は入らない
        hc=h1.c; w=4*hc.rolling(20).std(ddof=0); sq=to_m5((w<0.7*w.rolling(100).mean()).astype(float),'1h',idx)>0
        sellok&=~sq; buyok&=~sq
    m['pos5']=pd.Series(np.where(sellok,-1,np.where(buyok,1,0)),index=idx).shift(1)
    b=bigbars(h1,DOTEN); m['dir1h']=to_m5(pd.Series(np.where(b.c>ema(b.c,9),1,-1),index=b.index),DOTEN,idx)
    b4=bigbars(h1,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    return m.dropna()
def summ(lg):
    def s(a=None,b=None):
        x=lg
        if a: x=x[x.close>=a]
        if b: x=x[x.close<b]
        g=x[x.pips>0].pips.sum(); l=-x[x.pips<=0].pips.sum(); return x.pips.sum(), (g/l if l else 99)
    eq=lg.sort_values('close').pips.cumsum(); dd=(eq.cummax()-eq).max()
    return dict(決=s('2022','2025'),確=s(None,'2022'),確25=s('2025'),全=s(),DD=dd,戦=lg.camp.nunique(),y17=s('2017','2018')[0],y18=s('2018','2019')[0],j17=s('2017-01','2017-02')[0])
def row(tag,m5,h1,**kw):
    lg=run_ichi(prep2(m5,h1,**kw)); r=summ(lg)
    print(f"{tag:30s} 決22-24 {r['決'][0]:+7.0f} PF{r['決'][1]:.2f} | 確15-21 {r['確'][0]:+7.0f} PF{r['確'][1]:.2f} | 確25 {r['確25'][0]:+6.0f} | 全 {r['全'][0]:+7.0f} PF{r['全'][1]:.2f} DD{r['DD']:6.0f} 戦{r['戦']} | 2017 {r['y17']:+6.0f} 2018 {r['y18']:+6.0f} 17年1月 {r['j17']:+5.0f}",flush=True)
    return lg
if __name__=='__main__':
    m5,h1=load()
    print('=== 土台(さっきの決まり)')
    lg=row('土台 9に触れ・竿先2σ・1hドテン',m5,h1); lg.to_pickle('ichi_base.pkl')
    print('=== スキルの決まりを1つずつ')
    row('押し=21まで待つ',m5,h1,TOUCH=21)
    row('竿先=魚道(1σの外)でも入らない',m5,h1,SAO=1.0)
    row('爆弾岩(1hしぼみで入らない)',m5,h1,BOMB=True)
    row('ドテン=4時間足の9',m5,h1,DOTEN='4h')

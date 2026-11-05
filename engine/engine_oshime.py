# 押し目エンジン(たくちん 11-05「5でレンジ抜け前の山こえて巡航上昇下降なら押し目買い無限リーチのみにしたら、取れるはず」)
# 1) 5分レンジ = 5分遅行(21本前)が直近12本のうち8本以上絡む【置き換え:ポンの貯めと同じ】
# 2) 前の山 = そのレンジの間の一番高い所(売りは一番安い所)。レンジが終わった後も、次のレンジまで覚えておく
# 3) 山越え+巡航 = 5分終値が前の山を越えて確定 かつ 巡航の形(終値が±1σの外・帯が広がる・遅行が抜ける)【書】
# 4) 入り = その後、押し目買い(戻り売り)の無限リーチだけ:確定5分足のひげが21に触れ・終値が9の向き側・9と21が向き側・竿先(±2σ外)でない
#    押し目ごとに1発(21から離れてまた触れたら次)、前の玉から20pips、最大20発【置き換え】
# 5) 降り = 1時間足の9割れ(実体の真ん中と終値が9の向こう)で全部利確、この巡航は終わり。網=5分22本の高安−4hATR×3(守り)
# 6) だまし回避 = 1h21が逆向きなら入らない・1h200の向き側(実体が渡り切り)だけ
# 7) 5分21の傾き:巡航=向き側に30〜55度、押し目で入るのは0〜55度の時だけ。遅行は21本前(たくちん「5分の傾きもいれる？ 遅効21やろ」)
import os, sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from engine_ichi import load, ema, atr14, bigbars, to_m5, PIP, angle21, karami
import numpy as np, pandas as pd
def prep(m5,h1,LAG=21,ANG=True):
    m=m5.copy(); idx=m.index; c=m.c
    e9,e21=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0); w=4*sd
    rng=karami(m,LAG).rolling(12).sum()>=8                               # 5分レンジ(遅行は LAG 本前・たくちん「遅効21」)
    a5=angle21(m)                                                            # 5分21の角度(だまし回避スキルの測り方)
    # 前の山:レンジの足の高値・安値をレンジが続く間ためて、レンジが終わっても次のレンジまで持つ
    hi=m.h.where(rng); lo=m.l.where(rng); grp=(rng&~rng.shift(1,fill_value=False)).cumsum()
    yama_h=hi.groupby(grp).cummax().ffill(); yama_l=lo.groupby(grp).cummin().ffill()
    if ANG:   # 巡航=5分21の角度が向き側に30〜55度 かつ 遅行(LAG本前)が抜けている【たくちん「5分の傾きもいれる？ 遅効21やろ」】
        cruise_up=(c>yama_h)&(a5>=30)&(a5<=55)&(c>m.h.shift(LAG))
        cruise_dn=(c<yama_l)&(a5<=-30)&(a5>=-55)&(c<m.l.shift(LAG))
    else:
        cruise_up=(c>yama_h)&(c>mid+sd)&(w>w.shift(1))&(c>m.h.shift(21))
        cruise_dn=(c<yama_l)&(c<mid-sd)&(w>w.shift(1))&(c<m.l.shift(21))
    m['go']=pd.Series(np.where(cruise_up&~rng,1,np.where(cruise_dn&~rng,-1,0)),index=idx).shift(1)   # 確定足で山越え+巡航
    pb=(m.l<=e21)&(c>e9)&(e9>e21)&(c<=mid+2*sd); ps=(m.h>=e21)&(c<e9)&(e9<e21)&(c>=mid-2*sd)
    if ANG: pb&=(a5>0)&(a5<=55); ps&=(a5<0)&(a5>=-55)                         # 寝ている時・竿先(55度超)では入らない
    m['pull']=pd.Series(np.where(pb,1,np.where(ps,-1,0)),index=idx).shift(1)
    m['t21']=pd.Series(np.where(m.l<=e21,1,0)+np.where(m.h>=e21,-1,0)*0,index=idx).shift(1)     # (使わない:押し目の区切りは pull で見る)
    hc=h1.c; e91=ema(hc,9); bm=(h1.o+hc)/2
    nine=pd.Series(np.where((bm>e91)&(hc>e91),1,np.where((bm<e91)&(hc<e91),-1,0)),index=h1.index)
    s200=ema(hc,200); ab=((hc>s200)&(bm>s200)).astype(int)-((hc<s200)&(bm<s200)).astype(int)
    ang=np.sign(angle21(h1))
    for k,v in (('nine',nine),('s200',ab),('ang1',ang)): m[k]=to_m5(pd.Series(v.values,index=h1.index).astype(float),'1h',idx)
    b4=bigbars(h1,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    m['newh']=(idx.minute==0)
    return m.dropna()
def run(m,spr=0.3*PIP,MAXPOS=20,ADD=20.0):
    O,H,L=m.o.values,m.h.values,m.l.values; G=m.go.values; P=m.pull.values; NN=m.nine.values; S2=m.s200.values; A1=m.ang1.values; NH=m.newh.values
    CL,CS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; cr=0; prev_pull=0
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d'],i0=p['i0'],i1=i))
    def opn(i,d,k):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k,i0=i))
    for i in range(len(m)):
        if NH[i] and cr!=0 and int(NN[i])==-cr:            # 1時間9割れ → 利確、この巡航は終わり
            for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'9割れ')
            pos=[]; cr=0
        g=int(G[i])
        if g!=0 and g!=cr and int(S2[i])==g and int(A1[i])!=-g:   # 山越え+巡航(だまし回避を通ったもの)
            if pos and pos[0]['d']!=g:
                for p in pos: cls(i,p,O[i] if p['d']>0 else O[i]+spr,'逆の巡航')
                pos=[]
            cr=g
        pl=int(P[i])
        if cr!=0 and pl==cr and prev_pull!=cr and int(S2[i])==cr and int(A1[i])!=-cr:   # 押し目ごとに1発
            if not pos: opn(i,cr,'押し目')
            elif len(pos)<MAXPOS:
                pxc=O[i] if cr>0 else O[i]+spr
                if cr*(pxc-pos[-1]['e'])>=ADD*PIP: opn(i,cr,'無限リーチ')
        prev_pull=pl
        if pos:
            d=pos[0]['d']
            for p in pos:
                sl=CL[i] if d>0 else CS[i]
                if d>0 and sl>p['sl']+0.001 and sl<O[i]: p['sl']=sl
                if d<0 and sl<p['sl']-0.001 and sl>O[i]+spr: p['sl']=sl
        keep=[]
        for p in pos:
            d=p['d']
            if d>0 and L[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'網')
            elif d<0 and H[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'網')
            else: keep.append(p)
        pos=keep
    out=pd.DataFrame(log); out.attrs['open_left']=len(pos); return out

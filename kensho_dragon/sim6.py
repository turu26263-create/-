# B2 に 9割れ利確・川戻り利確・魚を追う向き を足す試験機
from sim5 import *
import numba as nb
@nb.njit(cache=True)
def run6(O,H,L,C,LOC,TRD,DIR,XL,XS,CHL,CHS,spr,MAXPOS,ADD,YEAR):
    # TRD: ドテンの向き(200) / DIR: 入り・足しを許す向き / XL,XS: 買い・売りを全部降りる合図(その5分足の始値で)
    n=len(O); pd_=np.zeros(64); pe=np.zeros(64); ps=np.zeros(64); k_=0
    eq=np.zeros(n); eqc=0.0; g=0.0; l=0.0; yp=np.zeros(20); bs=np.zeros(2); nc=0; nx=0; prev_tr=0
    for i in range(n):
        tr=int(TRD[i]); loc=int(LOC[i]); dr=int(DIR[i])
        if k_>0:
            d=pd_[0]; out=False
            if tr==-d and prev_tr!=tr: out=True                   # 200ドテン
            elif (d>0 and XL[i]) or (d<0 and XS[i]): out=True; nx+=1   # 9割れ・川戻り
            if out:
                for k in range(k_):
                    ex=O[i] if d>0 else O[i]+spr; p=(ex-pe[k])/PIP*d
                    eqc+=p; yp[YEAR[i]]+=p; bs[0 if d>0 else 1]+=p
                    if p>0: g+=p
                    else: l-=p
                k_=0
            else:
                for k in range(k_):
                    sl=CHL[i] if d>0 else CHS[i]
                    if d>0 and sl>ps[k]+0.001 and sl<O[i]: ps[k]=sl
                    if d<0 and sl<ps[k]-0.001 and sl>O[i]+spr: ps[k]=sl
                if k_<MAXPOS and loc==d and dr==d:
                    pxc=O[i] if d>0 else O[i]+spr; px=O[i]+spr if d>0 else O[i]
                    if d*(pxc-pe[k_-1])>=ADD*PIP:
                        sl=CHL[i] if d>0 else CHS[i]
                        if d>0 and sl>px: sl=px-10*PIP
                        if d<0 and sl<px: sl=px+10*PIP
                        pd_[k_]=d; pe[k_]=px; ps[k_]=sl; k_+=1
        prev_tr=tr
        if k_==0 and dr!=0 and loc==dr and not ((dr>0 and XL[i]) or (dr<0 and XS[i])):
            px=O[i]+spr if dr>0 else O[i]; sl=CHL[i] if dr>0 else CHS[i]
            if dr>0 and sl>px: sl=px-10*PIP
            if dr<0 and sl<px: sl=px+10*PIP
            pd_[0]=dr; pe[0]=px; ps[0]=sl; k_=1; nc+=1
        j=0
        for k in range(k_):
            d=pd_[k]; hit=False
            if d>0 and L[i]<=ps[k]: ex=O[i] if O[i]<=ps[k] else ps[k]; hit=True
            elif d<0 and H[i]+spr>=ps[k]: ex=O[i]+spr if O[i]+spr>=ps[k] else ps[k]; hit=True
            if hit:
                p=(ex-pe[k])/PIP*d; eqc+=p; yp[YEAR[i]]+=p; bs[0 if d>0 else 1]+=p
                if p>0: g+=p
                else: l-=p
            else:
                pd_[j]=d; pe[j]=pe[k]; ps[j]=ps[k]; j+=1
        k_=j; fl=0.0
        for k in range(k_): fl+=((C[i]-pe[k]) if pd_[k]>0 else (pe[k]-C[i]-spr))/PIP
        eq[i]=eqc+fl
    return eq,g,l,yp,bs,nc,nx

def build(m5,h1,XTF='1h'):
    import fix1
    from fix1 import B, side_n, with_trend, c4
    m=with_trend(side_n(3)); idx=m.index
    m['f921']=to_m5(pd.Series(np.sign(ema(c4,9)-ema(c4,21)).values,index=c4.index),'4h',idx).values
    hb=bigbars(h1,XTF); hc=hb.c; e9=ema(hc,9); mid=hc.rolling(20).mean(); sd=hc.rolling(20).std(ddof=0)
    x9L=(hc<e9); x9S=(hc>e9)
    outU=(hc>mid+sd); outD=(hc<mid-sd)
    kL=outU.shift(1).fillna(False)&~outU; kS=outD.shift(1).fillna(False)&~outD     # 川の外から内へ戻った1時間足
    for nm,s in (('x9L',x9L),('x9S',x9S),('kL',kL),('kS',kS)): m[nm]=to_m5(s.astype(float),XTF,idx).values>0
    # 1時間足が閉じた直後の5分足でだけ合図を出す(閉じた足の判断を1回だけ使う)
    m['newh']=(m.index.minute==0) if XTF=='1h' else ((m.index.minute==0)&(m.index.hour%4==0))
    return m

def go6(m,DIRMODE='200+921',EXIT=(),spr=0.3,MAXPOS=20,ADD=20.0,start=None,end=None,WAIT9=False):
    if start or end: m=m.loc[start:end]
    n=len(m); tr=m.trend.values.astype(np.float64)
    if DIRMODE=='200+921': dr=np.where(m.f921.values==tr,tr,0)
    elif DIRMODE=='921':   dr=m.f921.values.astype(float)        # 魚を追う: 川(4h 9と21)の向き
    else: dr=tr
    nh=m.newh.values
    if WAIT9:   # 1時間足の終値が9の向こう側の間は、その向きに入らない・足さない
        dr=np.where((dr>0)&m.x9L.values,0,np.where((dr<0)&m.x9S.values,0,dr))
    xl=np.zeros(n,bool); xs=np.zeros(n,bool)
    if '9' in EXIT: xl|=m.x9L.values&nh; xs|=m.x9S.values&nh
    if 'kawa' in EXIT: xl|=m.kL.values&nh; xs|=m.kS.values&nh
    yr=(m.index.year-2015).values.astype(np.int64)
    eq,g,l,yp,bs,nc,nx=run6(m.o.values,m.h.values,m.l.values,m.c.values,m['loc'].values.astype(np.float64),tr,dr.astype(np.float64),xl,xs,
                         m.chL.values,m.chS.values,spr*PIP,MAXPOS,ADD,yr)
    peak=np.maximum.accumulate(eq); dd=(peak-eq).max()
    return dict(pips=round(eq[-1]),PF=round(g/l,3) if l else 99,DD=round(dd),ikusa=nc,nx=nx,buy=round(bs[0]),sell=round(bs[1]),year={2015+i:round(v) for i,v in enumerate(yp) if v!=0})

def row6(tag,m,**kw):
    j=go6(m,start='2017-01',end='2017-01',**kw); y7=go6(m,start='2017',end='2017',**kw); y8=go6(m,start='2018',end='2018',**kw)
    a=go6(m,start='2022',end='2024',**kw); b=go6(m,start='2015',end='2021',**kw); c=go6(m,start='2025',**kw); f=go6(m,**kw)
    print(f"{tag:28s} 17年1月 {j['pips']:+6d} | 2017 {y7['pips']:+6d} | 2018 {y8['pips']:+6d} | 決 {a['pips']:+7d} 確15-21 {b['pips']:+7d} 確25 {c['pips']:+6d} | 全 {f['pips']:+7d} PF{f['PF']:.2f} DD{f['DD']} 戦{f['ikusa']} 利確降り{f['nx']} 買{f['buy']:+d} 売{f['sell']:+d}",flush=True)
    return f

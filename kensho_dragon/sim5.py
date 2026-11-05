# B(4h 200ドテン+5分合図+網) に わざ を足す。トレンド側と レンジ打ち側 を別々に回して足し合わせる
from sim4 import *
import numba as nb

@nb.njit(cache=True)
def run_tr(O,H,L,C,LOC,TRD,CHL,CHS,OKB,OKS,spr,MAXPOS,ADDSTEP,W1,YEAR):
    # OKB/OKS: その足で買い/売りの入り・足しをしてよいか(竿先・押し目)。W1: 1発目の重さ(斥候)
    n=len(O); pd_=np.zeros(64); pe=np.zeros(64); ps=np.zeros(64); pw=np.zeros(64); k_=0
    eq=np.zeros(n); eqc=0.0; g=0.0; l=0.0; yp=np.zeros(20); bs=np.zeros(2); nc=0
    for i in range(n):
        tr=int(TRD[i]); loc=int(LOC[i]); okd = OKB[i] if tr>0 else OKS[i]
        if k_>0:
            d=pd_[0]
            if tr==-d:
                for k in range(k_):
                    ex=O[i] if d>0 else O[i]+spr; p=(ex-pe[k])/PIP*d*pw[k]
                    eqc+=p; yp[YEAR[i]]+=p; bs[0 if d>0 else 1]+=p
                    if p>0: g+=p
                    else: l-=p
                k_=0
            else:
                for k in range(k_):
                    sl=CHL[i] if d>0 else CHS[i]
                    if d>0 and sl>ps[k]+0.001 and sl<O[i]: ps[k]=sl
                    if d<0 and sl<ps[k]-0.001 and sl>O[i]+spr: ps[k]=sl
                ok2 = OKB[i] if d>0 else OKS[i]
                if k_<MAXPOS and loc==d and ok2:
                    px=O[i]+spr if d>0 else O[i]
                    if d*(px-pe[k_-1])>=ADDSTEP*PIP:
                        sl=CHL[i] if d>0 else CHS[i]
                        if d>0 and sl>px: sl=px-10*PIP
                        if d<0 and sl<px: sl=px+10*PIP
                        pd_[k_]=d; pe[k_]=px; ps[k_]=sl; pw[k_]=1.0; k_+=1
        if k_==0 and tr!=0 and loc==tr and okd:
            px=O[i]+spr if tr>0 else O[i]; sl=CHL[i] if tr>0 else CHS[i]
            if tr>0 and sl>px: sl=px-10*PIP
            if tr<0 and sl<px: sl=px+10*PIP
            pd_[0]=tr; pe[0]=px; ps[0]=sl; pw[0]=W1; k_=1; nc+=1
        j=0
        for k in range(k_):
            d=pd_[k]; hit=False
            if d>0 and L[i]<=ps[k]: ex=O[i] if O[i]<=ps[k] else ps[k]; hit=True
            elif d<0 and H[i]+spr>=ps[k]: ex=O[i]+spr if O[i]+spr>=ps[k] else ps[k]; hit=True
            if hit:
                p=(ex-pe[k])/PIP*d*pw[k]; eqc+=p; yp[YEAR[i]]+=p; bs[0 if d>0 else 1]+=p
                if p>0: g+=p
                else: l-=p
            else:
                pd_[j]=d; pe[j]=pe[k]; ps[j]=ps[k]; pw[j]=pw[k]; j+=1
        k_=j; fl=0.0
        for k in range(k_): fl+=((C[i]-pe[k]) if pd_[k]>0 else (pe[k]-C[i]-spr))/PIP*pw[k]
        eq[i]=eqc+fl
    return eq,g,l,yp,bs,nc

@nb.njit(cache=True)
def run_rg(O,H,L,C,SIG,MID,SLW,spr,YEAR):
    # レンジ打ち: SIG=+1 買い / -1 売り(1時間足が閉じた直後の5分足だけ立つ)。利確=1時間の真ん中、網=入値から SLW 離れた所
    n=len(O); d=0; e=0.0; sl=0.0; eq=np.zeros(n); eqc=0.0; g=0.0; l=0.0; yp=np.zeros(20); bs=np.zeros(2); nc=0
    for i in range(n):
        if d==0 and SIG[i]!=0:
            d=int(SIG[i]); e=O[i]+spr if d>0 else O[i]; sl=e-d*SLW[i]; nc+=1
        if d!=0:
            ex=0.0; hit=False
            if d>0:
                if L[i]<=sl: ex=O[i] if O[i]<=sl else sl; hit=True
                elif H[i]>=MID[i]: ex=MID[i] if O[i]<MID[i] else O[i]; hit=True
            else:
                if H[i]+spr>=sl: ex=O[i]+spr if O[i]+spr>=sl else sl; hit=True
                elif L[i]+spr<=MID[i]: ex=MID[i] if O[i]+spr>MID[i] else O[i]+spr; hit=True
            if hit:
                p=(ex-e)/PIP*d; eqc+=p; yp[YEAR[i]]+=p; bs[0 if d>0 else 1]+=p
                if p>0: g+=p
                else: l-=p
                d=0
        eq[i]=eqc+(((C[i]-e) if d>0 else (e-C[i]-spr))/PIP if d!=0 else 0.0)
    return eq,g,l,yp,bs,nc

def base(m5,h1):
    m=prep4(m5,h1,'4h',LOC='m5',NET=('4h',3)); idx=m.index
    hb=h1; mid1=hb.c.rolling(20).mean(); sd1=hb.c.rolling(20).std(ddof=0); e21=ema(hb.c,21)
    m['up2']=to_m5(mid1+2*sd1,'1h',idx); m['dn2']=to_m5(mid1-2*sd1,'1h',idx); m['mid1']=to_m5(mid1,'1h',idx)
    m['e21']=to_m5(e21,'1h',idx); m['atr1']=to_m5(atr14(hb),'1h',idx)
    b4=bigbars(h1,'4h'); w4=4*b4.c.rolling(20).std(ddof=0); m['sq4']=to_m5(w4/w4.rolling(100).mean(),'4h',idx)
    m['e200_4']=to_m5(ema(b4.c,200),'4h',idx)
    c1=to_m5(hb.c,'1h',idx); m['c1']=c1
    m['newh']=(m.index.minute==0)   # 1時間足が閉じた直後の5分足
    return m.dropna()

def go(m, SAOSAKI=False, OSHIME=0, W1=1.0, RANGE=None, MAXPOS=20, spr=0.3, start=None, end=None):
    if start or end: m=m.loc[start:end]
    n=len(m); okb=np.ones(n,bool); oks=np.ones(n,bool)
    c=m.c.shift(1).values   # 確定1本前の5分足
    if SAOSAKI: okb&=~(c>m.up2.values); oks&=~(c<m.dn2.values)
    if OSHIME:  # 直近 OSHIME 本の5分足のどこかで 1時間EMA21 に触れた
        tb=(m.l<=m.e21).rolling(OSHIME).max().shift(1).fillna(0).values>0; ts=(m.h>=m.e21).rolling(OSHIME).max().shift(1).fillna(0).values>0
        okb&=tb; oks&=ts
    yr=(m.index.year-2015).values.astype(np.int64); s=spr*PIP
    eq,g,l,yp,bs,nc=run_tr(m.o.values,m.h.values,m.l.values,m.c.values,m['loc'].values.astype(np.float64),m.trend.values.astype(np.float64),
                          m.chL.values,m.chS.values,okb,oks,s,MAXPOS,20.0,W1,yr)
    nr=0
    if RANGE:
        sq,side,k=RANGE   # sq: 4h帯幅がふだんの何倍以下ならレンジ / side: 'both' か '200'(200の向きだけ) / k: 網=1時間ATR×k
        rng=(m.sq4.values<sq)&m.newh.values
        buy=rng&(m.c1.values<m.dn2.values); sell=rng&(m.c1.values>m.up2.values)
        if side=='200':
            above=m.c1.values>m.e200_4.values; buy&=above; sell&=~above
        sig=np.where(buy,1,np.where(sell,-1,0)).astype(np.float64)
        eq2,g2,l2,yp2,bs2,nr=run_rg(m.o.values,m.h.values,m.l.values,m.c.values,sig,m.mid1.values,(k*m.atr1).values,s,yr)
        eq=eq+eq2; g+=g2; l+=l2; yp=yp+yp2; bs=bs+bs2
    peak=np.maximum.accumulate(eq); dd=(peak-eq).max()
    return dict(pips=round(eq[-1]),PF=round(g/l,3),DD=round(dd),ikusa=nc,range=nr,buy=round(bs[0]),sell=round(bs[1]),year={2015+i:round(v) for i,v in enumerate(yp) if v!=0})

def row5(tag,m,**kw):
    a=go(m,start='2022',end='2024',**kw); b=go(m,start='2015',end='2021',**kw); c=go(m,start='2025',**kw); f=go(m,**kw)
    print(f"{tag:30s} 決 {a['pips']:+7d} PF{a['PF']:.2f} | 確15-21 {b['pips']:+7d} PF{b['PF']:.2f} | 確25 {c['pips']:+6d} | 全 {f['pips']:+7d} PF{f['PF']:.2f} DD{f['DD']:6d} 戦{f['ikusa']} レンジ{f['range']} 買{f['buy']:+d} 売{f['sell']:+d}",flush=True)
    return f

# 位置関係エンジン(たくちんの決まり入り)— 1本にまとめた版
# 決まりは ../決まり帳_位置関係エンジン.md。データ: HistData USDJPY 1分足(EST)。M1DIR に置き場を渡す
import os, glob, numpy as np, pandas as pd
PIP=0.01
def load(m1dir=None):
    m1dir=m1dir or os.environ.get('M1DIR','m1')
    dfs=[]
    for f in sorted(glob.glob(m1dir+'/*.csv')):
        d=pd.read_csv(f,header=None,names=['d','t','o','h','l','c','v']); d.index=pd.to_datetime(d.d+' '+d.t,format='%Y.%m.%d %H:%M'); dfs.append(d[['o','h','l','c']])
    m1=pd.concat(dfs).sort_index(); m1=m1[~m1.index.duplicated()]
    agg=dict(o='first',h='max',l='min',c='last')
    return m1.resample('5min').agg(agg).dropna(), m1.resample('1h').agg(agg).dropna()
def ema(c,p): return c.ewm(span=p,adjust=False).mean()
def atr14(df):
    tr=pd.concat([df.h-df.l,(df.h-df.c.shift()).abs(),(df.l-df.c.shift()).abs()],axis=1).max(axis=1); return tr.rolling(14).mean()
LEN={'1h':pd.Timedelta(hours=1),'4h':pd.Timedelta(hours=4)}
def bigbars(h1,tf): return h1 if tf=='1h' else h1.resample(tf).agg(dict(o='first',h='max',l='min',c='last')).dropna()
def to_m5(s,tf,idx): s=s.copy(); s.index=s.index+LEN[tf]; return s.reindex(idx,method='ffill')   # 足が確定した時刻から使う
def angle21(df):   # だまし回避スキルの21の角度【置き換え・たくちんと決めた測り方】横1本6ドット、縦=直近150本の高安の幅を500ドット、21の3本分の傾き
    e=ema(df.c,21); rng=df.h.rolling(150).max()-df.l.rolling(150).min()
    return np.degrees(np.arctan2((e-e.shift(3))/rng*500, 18))
def karami(df,n=26): return (df.c<=df.h.shift(n))&(df.c>=df.l.shift(n))
def prep(m5,h1):
    m=m5.copy(); idx=m.index; c=m.c
    e9,e21=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    e91=ema(h1.c,9); e211=ema(h1.c,21)
    o1=to_m5(pd.Series(np.sign(e91-e211).values,index=h1.index),'1h',idx)                 # 1h 921/219
    s1=to_m5(pd.Series(np.sign(e211.diff()).values,index=h1.index),'1h',idx)              # 1h 21の傾き
    side1=to_m5(pd.Series(np.sign(h1.c-e91).values,index=h1.index),'1h',idx)               # 1h 終値と9
    okb=(o1>0)&(s1>0)&(side1>0); oks=(o1<0)&(s1<0)&(side1<0)
    nsb=c<=mid+2*sd; nss=c>=mid-2*sd                                                       # 竿先で入らない・足さない
    pos_b=(m.l<=e21)&(c>e9)&(e9>e21); pos_s=(m.h>=e21)&(c<e9)&(e9<e21)                      # 5エントリの位置
    kar=karami(m); tame=kar.shift(1).rolling(12).sum()>=8; up=c>m.h.shift(26); dn=c<m.l.shift(26)
    pon_b=tame&up&~up.shift(1).fillna(False); pon_s=tame&dn&~dn.shift(1).fillna(False)      # ポン
    tdn=(m.l<=mid-2*sd).rolling(6).max()>0; tup=(m.h>=mid+2*sd).rolling(6).max()>0
    nar_b=tdn&(c>m.o)&(c>mid-2*sd); nar_s=tup&(c<m.o)&(c<mid+2*sd)                          # 鳴神
    m['ent']=pd.Series(np.where((pos_b|pon_b)&okb&nsb,1,np.where((pos_s|pon_s)&oks&nss,-1,0)),index=idx).shift(1)
    m['add']=pd.Series(np.where(nar_b&okb&nsb,1,np.where(nar_s&oks&nss,-1,0)),index=idx).shift(1)
    m['tch']=pd.Series(np.where(m.l<=mid-2*sd,1,np.where(m.h>=mid+2*sd,-1,0)),index=idx).shift(1)   # 確定5分足が −2σ(+1)/+2σ(−1) に触れた
    goo=(angle21(h1).abs()<10)&(karami(h1).rolling(12).sum()>=8)   # グー=21が寝て(角度10度未満)遅行が絡む(12本中8本)【置き換え】
    m['goo']=to_m5(goo.astype(float),'1h',idx)>0                                            # グー
    bm=(h1.o+h1.c)/2; st=pd.Series(np.where((bm>e91)&(h1.c>e91),1.0,np.where((bm<e91)&(h1.c<e91),-1.0,np.nan)),index=h1.index).ffill().fillna(0)
    m['dir1h']=to_m5(st,'1h',idx)                                                           # 9割れ(実体が渡り切り)
    mid1=h1.c.rolling(20).mean(); sd1=h1.c.rolling(20).std(ddof=0)
    m['u35']=to_m5(mid1+3.5*sd1,'1h',idx); m['d35']=to_m5(mid1-3.5*sd1,'1h',idx)
    b4=bigbars(h1,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    return m.dropna()
def run(m,spr=0.3*PIP,MAXPOS=4,LOCK=10.0):   # LOCK: しあわせセット(建値ロック)が掛かる有利な幅 pips【置き換え:10pips。ミナデイン極EA の 10*Point=1pips だと建値で14,060回降ろされた】
    O,H,L,C=m.o.values,m.h.values,m.l.values,m.c.values; E=m.ent.values; A=m['add'].values; TC=m.tch.values; G=m.goo.values; D=m.dir1h.values
    U,DN,CL,CS=m.u35.values,m.d35.values,m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; prevD=0; armed=False; left=True   # 鳴神は1回の押し目で1発(帯から離れて、また触れたら次の1発)
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why+('(建値)' if why=='網' and p['lock'] and abs(ex-p['e'])<1e-9 else ''),pips=(ex-p['e'])/PIP*p['d'],i0=p['i0'],i1=i))
    def opn(i,d,k):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k,lock=False,i0=i))
    for i in range(len(m)):
        d1=int(D[i]); goo=bool(G[i])
        if pos:
            if int(TC[i])!=pos[0]['d']: left=True
            elif left: armed=True; left=False
        if pos:
            d=pos[0]['d']
            if d1==-d and prevD!=d1:
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'9割れ')
                pos=[]
            elif goo:
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'グー')
                pos=[]
            else:
                for p in pos:
                    sl=CL[i] if d>0 else CS[i]
                    if d>0 and sl>p['sl']+0.001 and sl<O[i]: p['sl']=sl
                    if d<0 and sl<p['sl']-0.001 and sl>O[i]+spr: p['sl']=sl
                if len(pos)<MAXPOS and int(A[i])==d and d1==d and armed: opn(i,d,'鳴神'); armed=False; left=False
        prevD=d1
        if not pos and not goo and int(E[i])!=0 and int(E[i])==d1: opn(i,int(E[i]),'5エントリ'); armed=False; left=True
        keep=[]
        for p in pos:
            d=p['d']
            if d>0 and H[i]>=U[i]: cls(i,p,max(U[i],O[i]),'3.5σ')
            elif d<0 and L[i]+spr<=DN[i]: cls(i,p,min(DN[i],O[i])+spr,'3.5σ')
            elif d>0 and L[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'網')
            elif d<0 and H[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'網')
            else: keep.append(p)
        pos=keep
        for p in pos:   # しあわせセット: 有利に LOCK pips 進んだら 網を建値へ(次の足から効く)
            if not p['lock'] and LOCK is not None:
                if p['d']>0 and H[i]-p['e']>=LOCK*PIP:
                    p['lock']=True; p['sl']=max(p['sl'],p['e'])
                elif p['d']<0 and p['e']-(L[i]+spr)>=LOCK*PIP:
                    p['lock']=True; p['sl']=min(p['sl'],p['e'])
    out=pd.DataFrame(log); out.attrs['open_left']=len(pos); return out

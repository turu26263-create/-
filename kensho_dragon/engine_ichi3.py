# 位置関係エンジン 第3版 — 決まり帳_位置関係エンジン.md の全部を入れた
from sim4 import *
def chikou_karami(df,n=26):   # 確定足の終値が n 本前のローソクの安値〜高値の間 = 絡み
    return (df.c<=df.h.shift(n))&(df.c>=df.l.shift(n))
def prep_v3(m5,h1):
    m=m5.copy(); idx=m.index; c=m.c
    e9,e21=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    b4=bigbars(h1,'4h'); s4=to_m5(pd.Series(np.sign(b4.c-ema(b4.c,21)).values,index=b4.index),'4h',idx)
    s1=to_m5(pd.Series(np.sign(ema(h1.c,21).diff()).values,index=h1.index),'1h',idx)
    e91=ema(h1.c,9); side1=to_m5(pd.Series(np.sign(h1.c-e91).values,index=h1.index),'1h',idx)
    o1=to_m5(pd.Series(np.sign(e91-ema(h1.c,21)).values,index=h1.index),'1h',idx)   # 1時間の 9と21 の並び(921=+1 / 219=-1)
    m['o1']=o1
    dirok_b=(o1>0)&(s1>0)&(side1>0); dirok_s=(o1<0)&(s1<0)&(side1<0)          # 向1(1hの921/219で向き)・ド3
    notsao_b=c<=mid+2*sd; notsao_s=c>=mid-2*sd                                  # 入2・足3
    # 入1 位置
    pos_b=(m.l<=e21)&(c>e9)&(e9>e21); pos_s=(m.h>=e21)&(c<e9)&(e9<e21)
    # 入3 ポン(5分遅行26のレンジ抜け、貯め=直近12本で8本以上絡み)
    kar=chikou_karami(m); tame=kar.shift(1).rolling(12).sum()>=8
    up=c>m.h.shift(26); dn=c<m.l.shift(26)
    pon_b=tame&up&~up.shift(1).fillna(False); pon_s=tame&dn&~dn.shift(1).fillna(False)
    # 足1 鳴神(直近6本で−2σに触れた後の陽線確定、売りは逆)【置き換え:6本】
    touch_dn=(m.l<=mid-2*sd).rolling(6).max()>0; touch_up=(m.h>=mid+2*sd).rolling(6).max()>0
    naru_b=touch_dn&(c>m.o)&(c>mid-2*sd); naru_s=touch_up&(c<m.o)&(c<mid+2*sd)
    m['ent']=pd.Series(np.where(((pos_b|pon_b)&dirok_b&notsao_b),1,np.where(((pos_s|pon_s)&dirok_s&notsao_s),-1,0)),index=idx).shift(1)
    m['add']=pd.Series(np.where((naru_b&dirok_b&notsao_b),1,np.where((naru_s&dirok_s&notsao_s),-1,0)),index=idx).shift(1)
    # グ1・出2 1時間のグー
    w1=4*h1.c.rolling(20).std(ddof=0); sq=w1<0.7*w1.rolling(100).mean(); goo=sq&chikou_karami(h1)
    m['goo']=to_m5(goo.astype(float),'1h',idx)>0
    # ド1・ド2 1時間の向き(実体の真ん中と終値が9の向こう)
    bm=(h1.o+h1.c)/2; st=pd.Series(np.where((bm>e91)&(h1.c>e91),1.0,np.where((bm<e91)&(h1.c<e91),-1.0,np.nan)),index=h1.index).ffill().fillna(0)
    m['dir1h']=to_m5(st,'1h',idx)
    # 出1 ±3.5σ(1時間、確定した足の帯の値を次の1時間に使う)
    mid1=h1.c.rolling(20).mean(); sd1=h1.c.rolling(20).std(ddof=0)
    m['u35']=to_m5(mid1+3.5*sd1,'1h',idx); m['d35']=to_m5(mid1-3.5*sd1,'1h',idx)
    m['s4']=s4
    a=to_m5(atr14(b4),'4h',idx); m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    return m.dropna()
def run_v3(m,spr=0.3*PIP,MAXPOS=4,start=None,end=None):
    if start or end: m=m.loc[start:end]
    O,H,L,C=m.o.values,m.h.values,m.l.values,m.c.values; S4=m.o1.values; E=m.ent.values; A=m['add'].values; G=m.goo.values; D=m.dir1h.values
    U,DN,CL,CS=m.u35.values,m.d35.values,m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0; prevD=0
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['k'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d']))
    def opn(i,d,k):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,ot=T[i],camp=camp,n=len(pos)+1,k=k))
    for i in range(len(m)):
        d1=int(D[i]); goo=bool(G[i])
        if pos:
            d=pos[0]['d']
            if d1==-d and prevD!=d1:   # ド1 9割れ→必ず降りる。逆に入るのは 1hの219/921 が新しい向き(入りの向き o1 で止まる)・グーでは入らない
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'9割れドテン')
                pos=[]
            elif goo:                                    # 出2 次のグー
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'グー')
                pos=[]
            else:
                for p in pos:
                    sl=CL[i] if d>0 else CS[i]
                    if d>0 and sl>p['sl']+0.001 and sl<O[i]: p['sl']=sl
                    if d<0 and sl<p['sl']-0.001 and sl>O[i]+spr: p['sl']=sl
                if len(pos)<MAXPOS and int(A[i])==d and d1==d: opn(i,d,'鳴神')
        prevD=d1
        if not pos and not goo and int(E[i])!=0 and int(E[i])==d1: opn(i,int(E[i]),'5エントリ')
        keep=[]
        for p in pos:
            d=p['d']
            if d>0 and H[i]>=U[i]: cls(i,p,max(U[i],O[i]),'3.5σ')          # 出1
            elif d<0 and L[i]+spr<=DN[i]: cls(i,p,min(DN[i],O[i])+spr,'3.5σ')
            elif d>0 and L[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'網')
            elif d<0 and H[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'網')
            else: keep.append(p)
        pos=keep
    return pd.DataFrame(log)
MARKS=[('A','01/05〜01/07 下げと戻り(直すとこ)','2017-01-04 16:00','2017-01-07 08:00'),
       ('F','01/11 22時 116.87 → 01/12 14時 113.76 下げ','2017-01-11 06:00','2017-01-13 00:00'),
       ('G','01/13 22時 115.44 → 01/18 06時 112.56 下げ','2017-01-13 06:00','2017-01-18 18:00'),
       ('B','01/19 02時 113.33 → 01/20 02時 115.62 上げ','2017-01-18 10:00','2017-01-20 12:00'),
       ('C','01/21 02時 115.20 → 01/24 06時 112.52 下げ','2017-01-20 10:00','2017-01-24 18:00'),
       ('D','01/26 14時 113.23 → 01/27 22時 115.37 上げ','2017-01-25 22:00','2017-01-27 18:00'),
       ('E','01/30 06時 114.95 → 02/02 22時 112.05 下げ','2017-01-29 14:00','2017-02-02 12:00')]
if __name__=='__main__':
    m5,h1=load(); lg=run_v3(prep_v3(m5,h1)); lg.to_pickle('ichi_v3.pkl'); J=pd.Timedelta(hours=14)
    for nm,desc,a0,a1 in MARKS:
        x=lg[(lg.close>=a0)&(lg.open<a1)]
        print(f'== 印{nm} {desc}  エンジン合計 {x.pips.sum():+.1f}p')
        for cp,g in x.groupby('camp'):
            ks='・'.join(g.kind.str[:2]); print(f"   戦{cp} {g.dir.iloc[0]} {len(g)}発({ks}) 入 {(g.open.min()+J):%m/%d %H:%M} {g.entry.iloc[0]:.3f} → 降 {(g.close.max()+J):%m/%d %H:%M} {g.exit.iloc[-1]:.3f} {g.why.iloc[-1]} {g.pips.sum():+.1f}")

# 位置関係エンジン(たくちん 11-05 の決まり入り)
# 1) 1時間足の終値が EMA9 をまたいで確定 = ドテン場所(全部降りて向きを変える)
# 2) 5分エントリ: 確定5分足が「ひげが5分9に触れた・終値が9の向き側・9と21が向き側・竿先(±2σ外)でない」→ 次の足の始値で入る
# 3) 足し: 同じ位置の条件 + 前の玉から20pips
# 4) 網: 5分22本の高安 − 4時間ATR14×3(今まで通り)
from sim4 import *
def prep_ichi(m5,h1):
    m=m5.copy(); idx=m.index; c=m.c
    e9,e21=ema(c,9),ema(c,21); mid=c.rolling(20).mean(); sd=c.rolling(20).std(ddof=0)
    sellok=(m.h>=e9)&(c<e9)&(e9<e21)&(c>=mid-2*sd)
    buyok =(m.l<=e9)&(c>e9)&(e9>e21)&(c<=mid+2*sd)
    m['pos5']=np.where(sellok,-1,np.where(buyok,1,0)); m['pos5']=m.pos5.shift(1)      # 確定1本前の5分足
    hc=h1.c; d1=pd.Series(np.where(hc>ema(hc,9),1,-1),index=h1.index)
    m['dir1h']=to_m5(d1,'1h',idx)                                                     # 確定した1時間足の 9 の上/下
    b4=bigbars(h1,'4h'); a=to_m5(atr14(b4),'4h',idx)
    m['chL']=m.h.rolling(22).max().shift(1)-3*a; m['chS']=m.l.rolling(22).min().shift(1)+3*a
    return m.dropna()
def run_ichi(m,spr=0.3*PIP,MAXPOS=20,ADD=20.0,start=None,end=None):
    if start or end: m=m.loc[start:end]
    O,H,L,C=m.o.values,m.h.values,m.l.values,m.c.values; P=m.pos5.values; D=m.dir1h.values; CL,CS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0
    def cls(i,p,ex,why): log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',open=p['ot'],entry=p['e'],sl0=p['sl0'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d']))
    def opn(i,d,kind):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CL[i] if d>0 else CS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,sl0=sl,ot=T[i],camp=camp,n=len(pos)+1,kind=kind))
    for i in range(len(m)):
        d1=int(D[i]); p5=int(P[i])
        if pos:
            d=pos[0]['d']
            if d1==-d:                                   # 1時間9割れ = ドテン場所
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'9割れドテン')
                pos=[]
            else:
                for p in pos:
                    sl=CL[i] if d>0 else CS[i]
                    if d>0 and sl>p['sl']+0.001 and sl<O[i]: p['sl']=sl
                    if d<0 and sl<p['sl']-0.001 and sl>O[i]+spr: p['sl']=sl
                if len(pos)<MAXPOS and p5==d:
                    pxc=O[i] if d>0 else O[i]+spr
                    if d*(pxc-pos[-1]['e'])>=ADD*PIP: opn(i,d,'足し')
        if not pos and p5==d1: opn(i,d1,'5エントリ')
        keep=[]
        for p in pos:
            d=p['d']
            if d>0 and L[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'網')
            elif d<0 and H[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'網')
            else: keep.append(p)
        pos=keep
    return pd.DataFrame(log)
if __name__=='__main__':
    m5,h1=load(); m=prep_ichi(m5,h1); lg=run_ichi(m); lg.to_pickle('ichi_log.pkl')
    J=pd.Timedelta(hours=14)
    a=lg[(lg.open>='2017-01-04 14:00')&(lg.open<'2017-01-06 08:00')]
    print('A の所(日本時間)')
    for _,k in a.iterrows(): print(f"  戦{k.camp} {k.n}発目 {k.dir} 入 {(k.open+J):%m/%d %H:%M} {k.entry:.3f}  降 {(k.close+J):%m/%d %H:%M} {k.exit:.3f} {k.why} {k.pips:+.1f}")

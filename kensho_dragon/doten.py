# ドテン 5/1/4:持っている向きの逆に、5分(5>9>21 確定1本前)・1時間(5>9>21)・4時間(5>9>21)が全部そろったら全決済して逆に1発
from sim3 import *
def run_d(m, h4o, h1o, spr=0.3*PIP, MAXPOS=20, ADDSTEP=20.0, DOTEN=True, KUZURE=False):
    O,H,L,C=m.o.values,m.h.values,m.l.values,m.c.values; LOC=m['loc'].values; TRD=m.trend.values; ENT=m.ent.values
    CHL,CHS=m.chL.values,m.chS.values; T=m.index; H4=h4o; H1=h1o
    pos=[]; log=[]; camp=0
    def opn(i,d,kind):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CHL[i] if d>0 else CHS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,sl0=sl,ot=T[i],kind=kind,camp=camp,n=len(pos)+1))
    def cls(i,p,ex,why):
        log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['kind'],open=p['ot'],entry=p['e'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d']))
    for i in range(len(m)):
        trend=int(TRD[i]); loc=int(LOC[i]); ent=int(ENT[i])
        if pos:
            d=pos[0]['d']
            if DOTEN and loc==-d and H1[i]==-d and H4[i]==-d:
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'ドテン')
                pos=[]; opn(i,-d,'一番槍(ドテン)')
            elif trend==-d or (KUZURE and trend==0):
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'崩れ')
                pos=[]
            else:
                bid=O[i]
                for p in pos:
                    sl=CHL[i] if d>0 else CHS[i]
                    if d>0 and sl>p['sl']+0.001 and sl<bid: p['sl']=sl
                    if d<0 and sl<p['sl']-0.001 and sl>bid+spr: p['sl']=sl
                if len(pos)<MAXPOS and loc==d:
                    px=O[i] if d>0 else O[i]+spr
                    if d*(px-pos[-1]['e'])>=ADDSTEP*PIP: opn(i,d,'足し')
        elif trend!=0 and loc==trend and ent==trend: opn(i,trend,'一番槍')
        keep=[]
        for p in pos:
            d=p['d']
            if d>0 and L[i]<=p['sl']: cls(i,p,O[i] if O[i]<=p['sl'] else p['sl'],'網')
            elif d<0 and H[i]+spr>=p['sl']: cls(i,p,O[i]+spr if O[i]+spr>=p['sl'] else p['sl'],'網')
            else: keep.append(p)
        pos=keep
    return pd.DataFrame(log)
def stats(lg, a=None, b=None):
    x=lg
    if a: x=x[x.close>=a]
    if b: x=x[x.close<b]
    cc=x.groupby('camp').pips.sum(); g=x[x.pips>0].pips.sum(); l=-x[x.pips<=0].pips.sum()
    return f"{x.pips.sum():+7.0f} PF{g/l:.2f} 戦{len(cc):4d}"
if __name__=='__main__':
    import sys
    m5,h1=load(); m=prep3(m5,h1,H1='ord'); idx=m.index
    h4o=to_m5(sig(bigbars(h1,'4h'),'ord'),'4h',idx).values.astype(int); h1o=to_m5(sig(h1,'ord'),'1h',idx).values.astype(int)
    for tag,kw in [('今の形(崩れで降りる・ドテンなし)',dict(DOTEN=False,KUZURE=True)),('ドテン5/1/4・崩れなし',dict(DOTEN=True,KUZURE=False)),('ドテン5/1/4・崩れも残す',dict(DOTEN=True,KUZURE=True))]:
        lg=run_d(m,h4o,h1o,**kw); lg.to_pickle(f"dlog_{kw['DOTEN']}_{kw['KUZURE']}.pkl")
        eq=lg.sort_values('close').pips.cumsum(); # 決済ベースの落ち込み(参考)
        print(f"{tag:28s} 決22-24 {stats(lg,'2022','2025')} | 確15-21 {stats(lg,None,'2022')} | 確25 {stats(lg,'2025')} | 全 {stats(lg)} | 終わり方 {lg.groupby('camp').why.last().value_counts().to_dict()}",flush=True)
        y=lg.groupby(lg.close.dt.year).pips.sum().round().to_dict(); print('   年ごと',y, ' 買',round(lg[lg.dir=='買'].pips.sum()),' 売',round(lg[lg.dir=='売'].pips.sum()))

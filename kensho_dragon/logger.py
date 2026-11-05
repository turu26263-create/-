# run2 と同じ決まりを素の Python で書き、玉ごとの入り・降りを全部書き出す(照らし用)
from sim3 import *
def run_log(m, spr=0.3*PIP, MAXPOS=20, ADDSTEP=20.0):
    O,H,L,C=m.o.values,m.h.values,m.l.values,m.c.values; LOC=m['loc'].values; TRD=m.trend.values; ENT=m.ent.values
    CHL,CHS=m.chL.values,m.chS.values; T=m.index
    pos=[]; log=[]; camp=0
    def opn(i,d,kind):
        nonlocal camp
        px=O[i]+spr if d>0 else O[i]; sl=CHL[i] if d>0 else CHS[i]
        if d>0 and sl>px: sl=px-10*PIP
        if d<0 and sl<px: sl=px+10*PIP
        if not pos: camp+=1
        pos.append(dict(d=d,e=px,sl=sl,sl0=sl,ot=T[i],kind=kind,camp=camp,n=len(pos)+1))
    def cls(i,p,ex,why):
        log.append(dict(camp=p['camp'],n=p['n'],dir='買' if p['d']>0 else '売',kind=p['kind'],open=p['ot'],entry=p['e'],sl0=p['sl0'],close=T[i],exit=ex,why=why,pips=(ex-p['e'])/PIP*p['d']))
    for i in range(len(m)):
        trend=int(TRD[i]); loc=int(LOC[i]); ent=int(ENT[i])
        if pos:
            d=pos[0]['d']
            if trend==-d or trend==0:
                for p in pos: cls(i,p,O[i] if d>0 else O[i]+spr,'ドテン' if trend==-d else '崩れ')
                pos=[]
                if trend==-d and loc==trend and ent==trend: opn(i,trend,'一番槍(ドテン)')
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
if __name__=='__main__':
    m5,h1=load(); m=prep3(m5,h1,H1='ord')
    lg=run_log(m); lg.to_pickle('log_4h1h_20.pkl')
    r=sim3(m,0.3,MAXPOS=20)
    print('素のPython 合計',round(lg.pips.sum()),' numba 合計',r['pips'],' 戦',lg.camp.nunique(),r['ikusa'])

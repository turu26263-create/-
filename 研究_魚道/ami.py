import itertools, numpy as np, pandas as pd, time
from gyodou import FR, prep
import sys; sys.path.insert(0,'/home/user/-/.claude/skills/kaiseki-kousoku')
from kenkyu_kousoku import sim
def run(x, kind, p, spr, yrs):
    z=x.z.values; n=len(x)
    sig=np.zeros(n,np.int8); ex=np.zeros(n,np.int8)
    wp=x.wpct.values; sl=x.slope.values
    if kind=='A':  # 逆張り:外に出ていた魚が帯の内へ戻って確定 → 真ん中へ
        wmax, slmax, k = p
        for sg in (1,-1):
            cond=(sg*np.roll(z,1)>=2)&(sg*z<2)&(wp<=wmax)&(sg*sl<=slmax)
            sig[np.r_[False,cond[:-1]]]=-sg
        tp=np.abs(x.c-x.m).values; slw=k*x.s.values
        tp=np.r_[np.nan,tp[:-1]]; slw=np.r_[np.nan,slw[:-1]]
        return sim(x,sig,slw,tp,maxbars=p[2]*0+24,spread_pips=spr)
    else:          # 順張り:広がりの中で外へ飛び出した魚に乗る → 1σの内へ戻って確定で降りる
        wmin, slmin, k = p
        out=[]
        for sg in (1,-1):
            s2=np.zeros(n,np.int8); e2=np.zeros(n,np.int8)
            cond=(sg*z>=2)&(sg*np.roll(z,1)<2)&(wp>=wmin)&(sg*sl>=slmin)
            s2[np.r_[False,cond[:-1]]]=sg
            back=sg*z<1; e2[np.r_[False,back[:-1]]]=1
            slw=np.r_[np.nan,(k*x.s.values)[:-1]]
            out.append(sim(x,s2,slw,np.full(n,1e9),maxbars=96,spread_pips=spr,exit_at=e2))
        return pd.concat(out)
def score(tr):
    if len(tr)==0: return (0,0,0)
    g=tr.pips[tr.pips>0].sum(); b=-tr.pips[tr.pips<0].sum()
    return (len(tr), round(tr.pips.sum()), round(g/b,2) if b>0 else 9)
grid={'A':list(itertools.product([0.3,0.5,0.7,1.0],[-0.5,0.0,0.5,9],[1.0,1.5,2.0])),
      'B':list(itertools.product([0.5,0.6,0.7,0.8],[0.0,0.3,0.6,1.0],[1.0,1.5,2.0]))}
if __name__=='__main__':
    t0=time.time(); rows=[]
    for tf,raw in FR.items():
        x=prep(raw)
        for kind,G in grid.items():
            for p in G:
                for spr in (0.5,1.0):
                    tr=run(x,kind,p,spr,None); tr['y']=tr.t.dt.year
                    r={'足':tf,'網':kind,'p':p,'spr':spr}
                    for y in (2021,2022): r[y]=score(tr[tr.y==y])
                    rows.append(r)
    print(f'{len(rows)}通り {time.time()-t0:.0f}秒')
    R=pd.DataFrame(rows)
    R['両年+']=R.apply(lambda r: r[2021][1]>0 and r[2022][1]>0 and min(r[2021][0],r[2022][0])>=30,axis=1)
    for (tf,k),g in R.groupby(['足','網']):
        g05=g[g.spr==0.5]; g10=g[g.spr==1.0]
        print(f'{tf} {k}: 両年プラス(30回以上) 0.5p {g05["両年+"].sum()}/{len(g05)} 1.0p {g10["両年+"].sum()}/{len(g10)}')
    R.to_pickle('ami.pkl')

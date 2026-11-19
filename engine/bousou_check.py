# 暴走チェック: 全期間を回して、決まりが1回も破られていないかを全部の玉で数える
import sys, os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import engine_ichi as E, numpy as np, pandas as pd
def check(m,lg,MAXPOS=4):
    r={}
    ev=[(t,1) for t in lg.open]+[(t,-1) for t in lg.close]; ev.sort(key=lambda x:(x[0],x[1]))
    k=0; mx=0
    for _,v in ev: k+=v; mx=max(mx,k)
    r['同時に持った玉の最大(4以下)']=mx
    r['降りていない玉(0)']=lg.attrs.get('open_left',0)
    r['入った足≦降りた足でない玉(0)']=int((lg.close<lg.open).sum())
    g=m.goo.values; first=lg[lg.n==1]
    r['グーの足で入った1発目(0)']=int(g[first.i0.values].sum())
    c=m.c.values; mid=m.c.rolling(20).mean().values; sd=m.c.rolling(20).std(ddof=0).values; j=lg.i0.values-1
    buy=lg.dir.values=='買'
    r['竿先(±2σ外)の確定足で入った玉(0)']=int(((buy&(c[j]>mid[j]+2*sd[j]))|(~buy&(c[j]<mid[j]-2*sd[j]))).sum())
    r['同じ戦で同じ足に2発(0)']=int(lg.duplicated(['camp','i0']).sum())
    r['入りの向きと1時間の向きが違う1発目(0)']=int((np.where(first.dir=='買',1,-1)!=m.dir1h.values[first.i0.values]).sum())
    r['1戦で5発以上(0)']=int((lg.groupby('camp').n.max()>MAXPOS).sum())
    r['損が200pips超えの玉(参考)']=int((lg.pips<-200).sum())
    r['一番長く持った時間(参考)']=str((lg.close-lg.open).max())
    return r
if __name__=='__main__':
    m5,h1=E.load(); m=E.prep(m5,h1); lg=E.run(m)
    # 先読みしていないか: データを2016年末で切って回し、切る前の玉が全く同じか
    m_cut=E.prep(m5.loc[:'2016-12-31'],h1.loc[:'2016-12-31']); lg_cut=E.run(m_cut)
    a=lg[lg.close<'2016-12-20'][['open','entry','close','exit','pips']].reset_index(drop=True)
    b=lg_cut[lg_cut.close<'2016-12-20'][['open','entry','close','exit','pips']].reset_index(drop=True)
    r=check(m,lg); r['先読み:未来を切っても同じ玉か(一致)']='一致' if a.equals(b) else f'不一致 {len(a)} vs {len(b)}'
    for k,v in r.items(): print(f'{k}: {v}')
    lg.to_pickle(os.environ.get('LGOUT','lg_full.pkl'))

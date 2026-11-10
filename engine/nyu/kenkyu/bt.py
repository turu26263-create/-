import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from ea_utsushi import ea_run
exec(open(sys.argv[2]).read().split("def sp(t):")[0].split("H=srv.feat('1h')")[0].split("raw=load_cached")[0])
SA={2016:0.5,2017:1.2,2018:2.0,2019:2.3,2020:0.5,2021:0.2,2022:1.8,2023:5.1,2024:5.0,2025:3.7,2026:2.8}
mk=Market(load_cached(sys.argv[1]),'server'); base=mk.feat('1h')
t=ea_run(mk,tai=True,oshime=True)  # 利確は ea_run の今の値(4.0σ); t['ent']=pd.to_datetime(t.ent); t['ext']=pd.to_datetime(t.ext)
def swap(r):
    days=pd.date_range(r.ent.normalize(),r.ext,freq='D'); days=days[(days>r.ent)&(days<=r.ext)]; v=0
    for dd in days:
        if dd.weekday()>=5: continue
        v+=(3 if dd.weekday()==2 else 1)*100*r.e*SA.get(dd.year,2.0)/100/365*(0.8 if r.d>0 else -1.2)
    return v
t['swap']=t.apply(swap,axis=1)
t['spr']=-(t.ent.dt.hour.map({23:1.0,1:1.0}).fillna(0).values+t.ext.dt.hour.map({23:1.0,1:1.0}).fillna(0).values)
t['p2']=t.pips+t.swap+t.spr
def rep(nm,col):
    x=t.copy(); x['pips']=x[col]
    st=stat(x); w=x.pips[x.pips>0]; l=x.pips[x.pips<0]
    T,s=lot_sizing(x,base,1,102000,leverage=2000,fixed_lot=0.01,stopout=20)
    eq=x.sort_values('ext').pips.cumsum(); dd=(eq.cummax()-eq).max()
    seq=(x.sort_values('ext').pips<0).astype(int); mx=0;c=0
    for v in seq: c=c+1 if v else 0; mx=max(mx,c)
    print(f"■ {nm}\n  {st['n']}玉 合計 {st['sum']:+,.0f}p  勝率 {st['win']/st['n']*100:.1f}%  PF {st['pf']}  平均勝ち {w.mean():+.0f}p 平均負け {l.mean():+.0f}p  一番の勝ち {x.pips.max():+.0f}p 一番の負け {x.pips.min():+.0f}p")
    print(f"  降りた順に足した一番の落ち込み {dd:,.0f}p  続けて負けた最大 {mx}回  持った時間の中央 {(x.ext-x.ent).median()}")
    print(f"  10.2万円・0.01ロット:最後 {s['最後の資金']:,}円({s['増えた倍率']}倍) 一番へこんだ {s['一番へこんだ資金']:,}円 落ち込み率 {s['落ち込み率']}% 強制決済 {s['強制決済']}")
    y=x.groupby(x.ext.dt.year).pips.sum().round().astype(int); print('  年ごと(p):',y.to_dict())
    m=x.groupby(x.ext.dt.to_period('M')).pips.sum(); print(f"  月ごと:勝った月 {int((m>0).sum())}/{len(m)}({(m>0).mean()*100:.0f}%) 一番良い月 {m.max():+,.0f}p({m.idxmax()}) 一番悪い月 {m.min():+,.0f}p({m.idxmin()})")
    k=x.groupby('kind').pips.agg(['count','sum']); k['pf']=x.groupby('kind').apply(lambda g: g.pips[g.pips>0].sum()/max(-g.pips[g.pips<0].sum(),1e-9)).round(2)
    print('  種類ごと:'); [print(f"    {i}: {int(r['count'])}玉 {r['sum']:+,.0f}p PF{r.pf}") for i,r in k.iterrows()]
print(f"バックテスト(EAの写し=EAと同じ手順を1時間足1本ずつ):ドル円 MT4 1時間足 {base.index[0]:%Y/%m/%d}〜{base.index[-1]:%Y/%m/%d}、スプレッド0.3p\n")
rep('費用なし','pips'); print(); rep('費用込み(スワップは年ごとの金利差の見当・23時と1時はスプレッド+1p)','p2')

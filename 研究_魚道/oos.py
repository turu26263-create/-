import pandas as pd, numpy as np
import ami
from gyodou import FR, prep
x=prep(FR['1時間'])
print('台地の確かめ(2021〜22、1.0p)  傾き × 幅')
for s in (0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5):
    line=[]
    for w in (0.5,0.6,0.7):
        tr=ami.run(x,'B',(w,s,1.5),1.0,None); y=tr.t.dt.year
        a=ami.score(tr[y==2021]); b=ami.score(tr[y==2022]); line.append(f'{a[1]:+5d}/{b[1]:+5d}({a[0]+b[0]})')
    print(f' 傾き{s}: '+'  '.join(line))
print('\n=== 2023年(見ていない年)を1回だけ:幅0.6・傾き0.3・網1.5σ ===')
for spr in (0.5,1.0):
    tr=ami.run(x,'B',(0.6,0.3,1.5),spr,None); y=tr.t.dt.year
    for yy in (2021,2022,2023): print(f' {spr}p {yy}: 回数・ピップ・損益の比', ami.score(tr[y==yy]))
    t3=tr[y==2023].sort_values('t'); eq=t3.pips.cumsum(); dd=(eq.cummax()-eq).max()
    print(f'   2023 一番の落ち込み {dd:.0f}p  勝ち率 {(t3.pips>0).mean():.0%}  1回の平均 {t3.pips.mean():.1f}p  売り{(t3.d<0).sum()}回 {t3.pips[t3.d<0].sum():.0f}p / 買い{(t3.d>0).sum()}回 {t3.pips[t3.d>0].sum():.0f}p')

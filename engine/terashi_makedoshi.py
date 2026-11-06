# A:負けの年の照らし(11-06「ac ぶん回す ご」)。買い・1hの9割れ・2σ(完成形)の1戦ずつに、入った時の 1h と 4h の21の角度の局面を付ける
# 局面はだまし回避スキルの【置き換え】:0度以下=寝ている/0〜30=起き始め・根っこ/30〜55=巡航/55超=竿先。角度は engine_ichi.angle21(横6ドット・縦150本の高安=500ドット・21の3本)
import sys; sys.path.insert(0,__file__.rsplit('/',1)[0])
from engine_tai2 import *; from engine_ichi import angle21
m1=load(sys.argv[1]); t=pd.read_csv(sys.argv[2],parse_dates=['ent','ext'])
def stage(a): return '寝ている(0度以下)' if a<=0 else '起き始め(0〜30)' if a<=30 else '巡航(30〜55)' if a<=55 else '竿先(55超)'
for tf,nm in (('1h','1h'),('4h','4h')):
    b=bars(m1,tf); b['ang']=angle21(b); a=b[['k','ang']].sort_values('k')
    t=pd.merge_asof(t.sort_values('ent'),a.rename(columns={'k':'k'+nm,'ang':'ang'+nm}),left_on='ent',right_on='k'+nm,direction='backward')   # 入った時に確定している足
    t['局面'+nm]=t['ang'+nm].apply(stage)
t['年']=t.ent.dt.year; t['負けの年']=t.年.isin([2017,2019,2020,2025]).map({True:'負けの年',False:'勝ちの年'})
for nm in ('1h','4h'):
    g=t.groupby(['負けの年','局面'+nm]).pips.agg(戦='count',合計='sum',平均='mean').round(1)
    print(f'--- 入った時の {nm} の21の局面 ---'); print(g.to_string())
t.to_csv(sys.argv[3],index=False)

# 11-11 たくちん「スキル だまし回避 と 極めて優位性の高いシグナル もっと研究して」
# 日足の竿元60回(竿元1発+4時間の押し目で5発まで・日足219まで取り切り)に、だまし回避スキルの見分けを1つずつ当てて、どの竿元が消えるかを見る(並べ比べではなく、1つずつの見分けの照らし)
# 見分け(だまし回避スキル・決まり帳 だ1〜3 をそのまま日足に):
#   だ1 遅行が絡む(爆弾岩):竿元の足の終値が21本前の足の高値〜安値の中(買いは21本前の高値より上でないと絡み)
#   だ2 21が逆向き:日足21の角度が竿元と逆符号(0以下)
#   だ3 200の向き:竿元の足の実体の真ん中と終値が日足200の向き側でない
#   局面(21の角度):寝ている 0以下/起き始め 0〜30/巡航 30〜55/竿先 55超え(スキルの置き換え)
#   角度は直近150本の高安で測るので、データの始め(2016/08〜10)の竿元は角度が出ない=不明
#   赤:竿元の足が閉じた時の4時間の終値が4時間21の向き側か
import sys,io,contextlib,runpy,warnings; warnings.filterwarnings('ignore')
with contextlib.redirect_stdout(io.StringIO()): g=runpy.run_path('/home/user/-/engine/nyu/kenkyu/saomoto_oshime.py')
run=g['run']; D=g['D']; srv=g['srv']; pd=g['pd']; np=g['np']
t=pd.concat([run(1,'oshime'),run(-1,'oshime')],ignore_index=True)
S=t.groupby(['sao','d']).agg(玉=('pips','size'),合計=('pips','sum'),降り=('ext','first')).reset_index()
F4=srv.feat('4h'); y4=pd.merge_asof(pd.DataFrame({'k':D.k.values}),F4[['k','c','e21']].sort_values('k'),on='k',direction='backward'); y4.index=D.index
rows=[]
for r in S.itertuples():
    q=D.loc[r.sao]; d=r.d; i=D.index.get_loc(r.sao)
    mid=(q.o+q.c)/2
    da1 = not ((q.c>q.h21) if d>0 else (q.c<q.l21))
    da2 = bool((q.ang<=0) if d>0 else (q.ang>=0))   # 角度が出ない所(データの始め150本)は当たらない扱い
    da3 = not (((mid>q.e200)&(q.c>q.e200)) if d>0 else ((mid<q.e200)&(q.c<q.e200)))
    a=q.ang*d; kyoku='不明' if np.isnan(a) else '寝' if a<=0 else ('起' if a<=30 else ('巡' if a<=55 else '竿'))
    aka=(y4.c[r.sao]>y4.e21[r.sao]) if d>0 else (y4.c[r.sao]<y4.e21[r.sao])
    hi=(D.h.iloc[i-20:i].max() if d>0 else D.l.iloc[i-20:i].min())
    yama20=((q.c>hi) if d>0 else (q.c<hi))                         # 参考:20日の山を終値で抜けた
    rows.append(dict(竿元=f'{r.sao:%Y/%m/%d}',向き='買い' if d>0 else '売り',玉=r.玉,合計=round(r.合計),だ1=da1,だ2=da2,だ3=da3,局面=kyoku,角度=(None if np.isnan(a) else round(a)),赤=aka,山20抜け=yama20,年=r.sao.year))
T=pd.DataFrame(rows); T['勝ち']=T.合計>0
def show(nm,m):
    k=T[m]; s=T[~m]
    sel=lambda z:z[z.年.between(2022,2024)].合計.sum(); chk=lambda z:z[~z.年.between(2022,2024)].合計.sum()
    print(f'  {nm}: 消える {len(k)}回(勝ち {int(k.勝ち.sum())}・負け {int((~k.勝ち).sum())}・{k.合計.sum():+,}p) → 残る {len(s)}回 {s.合計.sum():+,}p(選22-24 {sel(s):+,}・確かめる年 {chk(s):+,})')
print(f'もと:{len(T)}回 {T.合計.sum():+,}p(勝ち {int(T.勝ち.sum())}・負け {int((~T.勝ち).sum())})')
print('--- 見分けを1つずつ(当たった竿元は入らない)---')
show('だ1 遅行が絡む',T.だ1); show('だ2 日足21が逆向き',T.だ2); show('だ3 200の向き側でない',T.だ3)
show('赤:4時間の終値が21の向こう側でない',~T.赤)
for k in ['寝','起','巡','竿']: show(f'局面 {k}',T.局面==k)
show('だ1〜3 のどれか(1時間の根っこで使った3つを一緒に)',T.だ1|T.だ2|T.だ3)
print('--- 竿元60回の札(局面・角度・見分け)---')
print(T.drop(columns=['勝ち','年']).to_string(index=False))
# ---- 上の足:週足(月曜0時からの7日。閉じた時刻=始まり+7日。閉じた週だけ使う)
raw=g['raw']; AGG={'o':'first','h':'max','l':'min','c':'last'}
W=raw.resample('7D',origin=pd.Timestamp('2016-03-07')).agg(AGG).dropna(); W['k']=W.index+pd.Timedelta('7D')
W['e9']=W.c.ewm(span=9,adjust=False).mean(); W['e21']=W.c.ewm(span=21,adjust=False).mean()
yw=pd.merge_asof(pd.DataFrame({'k':D.k.values}),W[['k','c','e9','e21']].sort_values('k'),on='k',direction='backward'); yw.index=D.index
T['週921']=[bool((yw.e9[pd.Timestamp(s_.replace('/','-'))]>yw.e21[pd.Timestamp(s_.replace('/','-'))]) if v=='買い' else (yw.e9[pd.Timestamp(s_.replace('/','-'))]<yw.e21[pd.Timestamp(s_.replace('/','-'))])) for s_,v in zip(T.竿元,T.向き)]
T['週9の上']=[bool((yw.c[pd.Timestamp(s_.replace('/','-'))]>yw.e9[pd.Timestamp(s_.replace('/','-'))]) if v=='買い' else (yw.c[pd.Timestamp(s_.replace('/','-'))]<yw.e9[pd.Timestamp(s_.replace('/','-'))])) for s_,v in zip(T.竿元,T.向き)]
print('--- 上の足(週足)の向きを1つずつ ---')
show('週足の9と21が竿元と逆の並び',~T.週921); show('週足の終値が9の向こう側でない',~T.週9の上)
print(T[['竿元','向き','合計','週921','週9の上']].to_string(index=False))
print('--- 週足と逆向きの竿元(週の流れが変わる所)と、同じ向きの竿元 ---')
for nm,m in [('週足と逆向き',~T.週921),('週足と同じ向き',T.週921)]:
    k=T[m]; yy=k.年
    print(f"  {nm}: {len(k)}回 勝ち {int(k.勝ち.sum())} {k.合計.sum():+,}p / 選22-24 {k.合計[yy.between(2022,2024)].sum():+,}({int(yy.between(2022,2024).sum())}回)/ 確かめる年 {k.合計[~yy.between(2022,2024)].sum():+,}({int((~yy.between(2022,2024)).sum())}回)/ 年ごと {k.groupby('年').合計.sum().to_dict()}")

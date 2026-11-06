# 改良した道具を「決まった形」に当てる(11-06)。0時のスプレッド・スワップ/年ごとの強さ/並べ替えの試し/1個ずつ
import sys, warnings; warnings.filterwarnings('ignore')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
SPL={'選22-24':(2022,2024),'確16-21':(2016,2021),'確25-26':(2025,2026)}
KW=dict(mk=srv,big='1D',mid='4h',small='1h',d=1,core_exit=('1D','219'),maxpos=5,n8=True,reenter=True,tp=('4h',3.5),ts=550)
t,b=run_tai(**KW); print('決まった形', stat(t))
print('\n=== 1. 0時のスプレッドとスワップ(研究台の甘い所)===')
h=pd.to_datetime(t.ent).dt.hour; print(f"入った時刻が0時の玉 {int((h==0).sum())}/{len(t)}、降りた時刻が0時の玉 {int((pd.to_datetime(t.ext).dt.hour==0).sum())}")
for nm,kw in (('0時のスプレッド +3p',dict(spr_hour={0:3.0})),('0時のスプレッド +10p',dict(spr_hour={0:10.0})),
              ('スワップ 買い+0.05p/晩',dict(swap_long=0.05)),('スワップ 買い+0.2p/晩',dict(swap_long=0.2)),('スワップ 買い−0.1p/晩',dict(swap_long=-0.1)),
              ('0時+10p と スワップ−0.1p',dict(spr_hour={0:10.0},swap_long=-0.1))):
    z=cost_adjust(t,1,**kw); r=report(z,b,1,SPL)
    print(f"  {nm:22}: 全{r['全_p']:+7.0f} PF{r['全_pf']} 確16-21 {r['確16-21_p']:+6.0f} 確25-26 {r['確25-26_p']:+6.0f}" + (f" 平均の晩{z['晩'].mean():.1f}" if '晩' in z else ''))
print('\n=== 2. 年ごとの強さ ===')
n=nenbetsu(t); print(f"負けた年 {n['負けた年']}/{n['年の数']}、一番悪い年 {n['一番悪い年']}"); print('3年ずつのPF:',n['区切りPF'])
print('\n=== 3. 並べ替えの試し(山の順番を2000通り)===')
print(montecarlo(t,2000,capital_yen=1_000_000,lot=0.1))
print('\n=== 4. 1個ずつ(決まった形から1つ外す・変える)===')
parts={'利確を外す':dict(tp=None),'TSを外す':dict(ts=0),'縄8を外す':dict(n8=False),'5発→1発':dict(maxpos=1),'5発→3発':dict(maxpos=3),'利確を4hの+4σ':dict(tp=('4h',4.0)),'TS 450p':dict(ts=450),'TS 650p':dict(ts=650),'竿先2.5σ':dict(sao=2.5)}
df=hitotsuzutsu(run_tai,KW,parts,SPL)
print(df[['名前','全_p','全_p差','確16-21_p','確16-21_p差','確25-26_p','確25-26_p差','含み損込みDD','判定']].to_string(index=False))

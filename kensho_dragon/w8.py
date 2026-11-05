from sim5 import *
import sim5
m5,h1=load()
def mk(k):
    m=prep4(m5,h1,'4h',LOC='m5',NET=('4h',k)); b=base(m5,h1)
    return b.assign(chL=m.chL.reindex(b.index),chS=m.chS.reindex(b.index))
def line(tag,m,**kw):
    y17=go(m,start='2017',end='2017',**kw); y18=go(m,start='2018',end='2018',**kw); f=go(m,**kw)
    print(f"{tag:22s} 2017 {y17['pips']:+6d} | 2018 {y18['pips']:+6d} | 2年 {y17['pips']+y18['pips']:+6d} | 全期間 {f['pips']:+7d} PF{f['PF']:.2f} DD{f['DD']}",flush=True)
b=mk(3)
print('--- 土台 B'); line('B',b)
print('--- 網の深さ(4hATR×)')
for k in (1.5,2,4,5,6,8): line(f'網×{k}',mk(k))
print('--- スプレッド')
for s in (0.0,1.0,2.0): line(f'スプレッド{s}',b,spr=s)
print('--- 無限リーチ(足しの間)')
for a in (10,40,80): line(f'足し{a}p',b,ADD=a)
print('--- 無限リーチ(最大発数)')
for x in (1,5,10): line(f'最大{x}発',b,MAXPOS=x)
print('--- 斥候(1発目の重さ)')
for w in (0.25,0.5,2.0): line(f'斥候{w}',b,W1=w)

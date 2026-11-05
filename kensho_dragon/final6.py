from sim3 import *
m5,h1=load(); m=prep3(m5,h1,H1='ord'); m0=prep3(m5,h1)
for tag,mm,kw in [('前回 4h土台(1時間なし)',m0,{}),('4h+1h 14発',m,{}),('4h+1h 最大値 20発',m,{'MAXPOS':20}),('4h+1h 20発 足し30',m,{'MAXPOS':20,'ADDSTEP':30})]:
    for s in (0.3,1.0):
        r=sim3(mm,s,**kw); print(f"{tag:22s} spr{s}: {r['pips']:+7d}pips PF{r['PF']:.2f} DD{r['DD']:5d} 戦{r['ikusa']} 勝率{r['win']}% 買{r['buy']:+d} 売{r['sell']:+d}")
    print('   年ごと', sim3(mm,0.3,**kw)['year'])

from sim2 import *
m5,h1=load()
for tag,kw,mk in [('4h 土台 CHK3 ADD20 MAX14',{},{}),('4h MAX20(最大値)',{'MAXPOS':20},{}),('4h ADD40(落ち込み少)',{'ADDSTEP':40},{}),('4h CHK2.5',{},{'CHK':2.5}),('日足 土台',{},{'TTF':'1D'})]:
    m=prep2(m5,h1,mk.pop('TTF','4h'),**mk)
    for s in (0.3,1.0):
        r=sim(m,s,**kw); print(f"{tag:24s} spr{s}: {r['pips']:+7d}pips PF{r['PF']:.2f} DD{r['DD']} 戦{r['ikusa']} 勝率{r['win']}% 損切{r['SL']} ドテン{r['doten']} 崩れ{r['kuzure']}")
    print('   年ごと', sim(m,0.3,**kw)['year'])

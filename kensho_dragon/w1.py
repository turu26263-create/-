from sim4 import *
m5,h1=load()
print('=== 1. 200ドテンだけ(1発・網なし・足しなし)')
for tf in ('1h','4h','1D'): row(f'200ドテン {tf}',prep4(m5,h1,tf),MAXPOS=1)
print('=== 2. 200の行ったり来たり止め(200から何pips離れたら向きを変えるか) 4h')
for bf in (0,10,20,40,80): row(f'4h 離れ{bf}p',prep4(m5,h1,'4h',BUF=bf),MAXPOS=1)

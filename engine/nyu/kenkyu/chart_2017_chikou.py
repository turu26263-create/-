# 11-11 たくちん「遅刻スパンロウソクがらみでしあわせセット」:2017年の日足に遅行スパン(終値を21本前に戻した線)を描き、機械が「絡み」と見た日を色で出す
import sys,warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'); plt.rcParams['font.family']='WenQuanYi Zen Hei'
raw=load_cached(sys.argv[1]); D=Market(raw,'server').feat('1D')
lo5=D.l.shift(19).rolling(5).min(); hi5=D.h.shift(19).rolling(5).max()
k1=(D.c>=D.l21)&(D.c<=D.h21); k5=(D.c>=lo5)&(D.c<=hi5)
X=D['2016-11-15':'2018-01-20']; ch=D.c.shift(-21)['2016-11-15':'2018-01-20']   # 遅行スパン:その日の線の上に、21本あとの終値を置く
fig,ax=plt.subplots(figsize=(20,9))
up=X.c>=X.o; ax.vlines(X.index,X.l,X.h,color='#555',lw=0.6)
ax.bar(X.index[up],(X.c-X.o)[up],bottom=X.o[up],width=0.7,color='#e8f0ff',edgecolor='#1f5fe0',lw=0.6)
ax.bar(X.index[~up],(X.o-X.c)[~up],bottom=X.c[~up],width=0.7,color='#1f2a44',edgecolor='#1f2a44',lw=0.6)
ax.plot(X.index,X.e9,color='#1f77b4',lw=1.4,label='9(青)'); ax.plot(X.index,X.e21,color='#d62728',lw=1.4,label='21(赤)')
for k in (2,): ax.plot(X.index,X.md+k*X.sd,color='#888',lw=0.8); ax.plot(X.index,X.md-k*X.sd,color='#888',lw=0.8)
ax.plot(ch.index,ch.values,color='#9b30ff',lw=2.2,label='遅行スパン(終値を21本前に戻した線)')
# 21本前のロウソクに絡んだ日(その日の終値が、21本前の1本の高安の中)を、21本前の所に印
kk=k1['2016-12-15':'2018-01-20']
for t0,v in kk.items():
    if v:
        i=D.index.get_loc(t0)
        if i-21>=0: ax.scatter(D.index[i-21],D.c.iloc[i],marker='s',color='#ff9900',s=40,zorder=6)
ax.scatter([],[],marker='s',color='#ff9900',label='機械が「絡み」と見た所(終値が21本前の1本の高安の中)')
ax.set_title('2017年 日足と遅行スパン(紫)。オレンジ□=機械が「遅行スパンがロウソクに絡んだ」と見た所',fontsize=13)
ax.legend(loc='upper right',fontsize=10); ax.grid(alpha=0.25); fig.tight_layout()
out='/home/user/-/engine/kekka_tai/nyu/chart_saomoto/2017年_遅行スパン.png'; fig.savefig(out,dpi=100); print(out)
print('2017年 絡み(1本)',int(k1['2017'].sum()),'日 / 絡み(5本)',int(k5['2017'].sum()),'日 / 2017年の日数',len(D['2017']))

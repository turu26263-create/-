import sys, warnings; warnings.filterwarnings('ignore'); sys.path.insert(0,'/home/user/-/engine/nyu')
from nyu import *; from tai_parts import *
srv=Market(load_cached(sys.argv[1]),'server')
K=dict(maxpos=5,n8=False,reenter=True,tp=('4h',3.5),ts=550,avoid_in=(0,),avoid_out=(0,),kai_k9=3,big21_up=True,yasumi=True)
s,_=run_tai(srv,'1D','4h','1h',-1,('1D','219'),**K)
W={'芯の降り':'日足921','足しの降り':'日足921','TS':'TS550','利確':'利確'}; s['w']=s.why.map(W)
print('売り',len(s),'玉',round(s.pips.sum()),'p'); print(s.groupby('w').pips.agg(['count','sum','mean']).round())
L=s[s.w=='日足921']; H4=srv.feat('4h'); D=srv.feat('1D')
print('\n日足921で降りた玉:伸び(入ってから一番下へ行ったp)で分けた')
print(L.groupby(pd.cut(L.mfe,[-1,30,60,100,200,2000])).pips.agg(['count','sum','mean']).round())
print('持った日数の中央',(pd.to_datetime(L.ext)-L.ent).median(),' 利確の玉',(pd.to_datetime(s[s.w=='利確'].ext)-s[s.w=='利確'].ent).median())
# 入った後、4時間足で「新しい921」(9が21を上抜け)が出た最初の時刻で降りていたら
up=(H4.e9>H4.e21); x921=up&~up.shift(1,fill_value=False)
# 入った後、4時間の9割れ(売りの逆:実体の真ん中と終値が9の上)
rows=[]
for _,r in L.iterrows():
    a=H4[(H4.k>r.ent)&(H4.k<pd.Timestamp(r.ext))]
    c1=a[x921.loc[a.index]]; c2=a[a.ware_s]
    f=lambda c: (r.e-(c.c.iloc[0]+0.003))*100 if len(c) else r.pips
    rows.append(dict(ent=r.ent,e=r.e,pips=round(r.pips),mfe=round(r.mfe),四時間921なら=round(f(c1)),四時間9割れなら=round(f(c2))))
R=pd.DataFrame(rows); pd.set_option('display.width',200)
print('\n日足921で降りた',len(R),'玉:今',R.pips.sum(),'/ 4時間の新しい921で降りたら(足の終値で見当)',R.四時間921なら.sum(),'/ 4時間の9割れ(上へ)なら',R.四時間9割れなら.sum())
print(R.sort_values('pips').head(15).to_string(index=False))

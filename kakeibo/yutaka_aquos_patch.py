import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s
    assert s.count(a)==1,a[:60]
    s=s.replace(a,b)
# A: getUserMedia が返事をしない機種(AQUOS等)で止まらないよう7秒で打ち切る
rep("async function kameraHiraku(){",
"""/* AQUOS などで getUserMedia が返事をしないまま止まることがあるので、7秒で打ち切って次へ */
function kameraKaru(tame){return new Promise((ok,ng)=>{let owari=false;const t=setTimeout(()=>{owari=true;ng({name:'TimeoutError'})},7000);
  navigator.mediaDevices.getUserMedia({audio:false,video:tame}).then(st=>{clearTimeout(t);if(owari){st.getTracks().forEach(x=>x.stop());return}ok(st)},e=>{clearTimeout(t);if(!owari)ng(e)})})}
async function kameraHiraku(){""")
rep("let st;try{st=await navigator.mediaDevices.getUserMedia({audio:false,video:tame})}catch(e){saigo=e;if(e&&(e.name==='NotAllowedError'||e.name==='SecurityError'))break;continue}",
    "let st;try{st=await kameraKaru(tame)}catch(e){saigo=e;if(e&&(e.name==='NotAllowedError'||e.name==='SecurityError'||e.name==='TimeoutError'))break;continue}")
# B: 撮影の幕に「写真を選ぶ」を常に出す(押した指でそのまま開くので、どの機種でも止められない)
rep('<button type="button" class="usubtn" id="kameraHoka">携帯のカメラで撮る</button>',
    '<button type="button" class="usubtn" id="kameraHoka">携帯のカメラで撮る</button><button type="button" class="usubtn" id="kameraErabu">写真を選ぶ</button>')
rep("$('kameraHoka').onclick=()=>{kameraTojiru();$('fileKamera').click()};",
    "$('kameraHoka').onclick=()=>{kameraTojiru();$('fileKamera').click()};\n  $('kameraErabu').onclick=()=>{kameraTojiru();$('filePick').click()};")
# 失敗の理由を画面に出す(たくちんが読み上げれば原因が分かる)
rep("  const j=$('kameraJotai');\n  if(saigo&&saigo.name==='NotAllowedError')",
    "  const j=$('kameraJotai');\n  try{const y=$('gamenYosu');y.textContent+=' / 止まった理由:'+(saigo?saigo.name:'映像が来ない');y.hidden=false}catch(x){}\n  $('kameraAnnai').hidden=false;\n  if(saigo&&saigo.name==='TimeoutError'){if(j)j.textContent='この携帯はカメラの返事がありませんでした。下の「携帯のカメラで撮る」か「写真を選ぶ」を押してください。';return}\n  if(saigo&&saigo.name==='NotAllowedError')")
# C: 失敗後に自動で写真選びを開こうとしても指の操作から離れていて止められるので、ボタンで案内
rep("kameraHiraku().catch(()=>{kameraTojiru();$('kameraAnnai').hidden=false;ireru('カメラを開けなかったので、写真選びを開きます');try{$('filePick').click()}catch(x){}});",
    "kameraHiraku().catch(()=>{kameraTojiru();$('kameraAnnai').hidden=false;ireru('カメラを開けませんでした。「写真を選ぶ」を押すと、カメラか写真を選べます')});")
open(p,'w',encoding='utf-8').write(s);print('ok',p)

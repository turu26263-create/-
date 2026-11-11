import sys
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
old_lines="""/* Android:アプリの中(wv・枠の中)では隠す。普通のブラウザ(外のページ)ではページの中にカメラを映して撮る */
if(/Android/i.test(navigator.userAgent)){
  let naka=/; wv\\)/i.test(navigator.userAgent);try{if(window.top!==window)naka=true}catch(x){naka=true}
  const lb=document.querySelector('label[for=fileKamera]');
  if(naka||!(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia))lb.hidden=true;
  else lb.addEventListener('click',e=>{e.preventDefault();kameraHiraku().catch(()=>{kameraTojiru();ireru('カメラを開けませんでした。携帯のカメラで撮ってから「写真を選ぶ」で選んでください')})});
}"""
new_lines="""/* 「カメラで撮る」はどの機種でも出す(あすかの家計簿と同じ直し 2026-11-11)。Androidはページの中にカメラを映して撮り、画面がカメラを渡さない時は写真選びへ回して、ブラウザで開く道を出す */
if(/Android/i.test(navigator.userAgent)){
  try{const ua=navigator.userAgent,naka=/; wv\\)|Claude/i.test(ua);let waku=true;try{waku=window.top!==window}catch(x){}
    let yu='不明';try{const fp=document.featurePolicy||document.permissionsPolicy;if(fp&&fp.allowsFeature)yu=fp.allowsFeature('camera')?'あり':'なし'}catch(x){}
    const y=$('gamenYosu');y.textContent='この画面:'+(naka?'アプリの中':'ブラウザ')+' / カメラの許し:'+yu+' / 枠の中:'+(waku?'はい':'いいえ');y.hidden=false}catch(x){}
  document.querySelector('label[for=fileKamera]').addEventListener('click',e=>{
    let yurusu=!!(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia);
    try{const fp=document.featurePolicy||document.permissionsPolicy;if(fp&&fp.allowsFeature&&!fp.allowsFeature('camera'))yurusu=false}catch(x){}
    e.preventDefault();
    if(!yurusu){ireru('この画面ではカメラが使えないので、写真選びを開きます');$('kameraAnnai').hidden=false;$('filePick').click();return}
    kameraHiraku().catch(()=>{kameraTojiru();$('kameraAnnai').hidden=false;ireru('カメラを開けなかったので、写真選びを開きます');try{$('filePick').click()}catch(x){}});
  });
}"""
assert s.count(old_lines)==1,'js'
s=s.replace(old_lines,new_lines)
old_html="""      <input id="fileKamera" type="file" accept="image/*" capture="environment" hidden>
"""
new_html=old_html+"""      <div class="kaminote" id="kameraAnnai" hidden style="margin:8px 0">この画面はカメラを渡してくれません。<a id="chromeHe" href="https://turu26263-create.github.io/ayumi-kakeibo/yutaka/" target="_blank" rel="noopener">ここを押してブラウザで開く</a>と「カメラで撮る」が使えます。記録は開いた画面ごとに別々に残ります。</div>
      <p class="oshirase" id="gamenYosu" style="margin:8px 0" hidden></p>
"""
assert s.count(old_html)==1,'html'
s=s.replace(old_html,new_html)
assert s.count("'kamera-chu'")==3
s=s.replace("'kamera-chu'","'yutaka-kamera-chu'")
open(p,'w',encoding='utf-8').write(s); print('ok',p)

// マークファクトリー 動作確認(実ブラウザ Chromium)
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
const D = __dirname; const FILE = process.argv[2] || path.join(D, 'index.html');
const results = []; const ok = (name, cond, extra='') => { results.push((cond ? 'OK  ' : 'NG  ') + name + (extra ? ' | ' + extra : '')); };
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, permissions: ['clipboard-read','clipboard-write'] });
  const errs = [];
  const p = await ctx.newPage();
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error' && !/fonts|ERR_|net::/.test(m.text())) errs.push('console: ' + m.text()); });
  await p.route('**/jsqr@1.4.0/dist/jsQR.js', r => r.fulfill({ path: path.join(D, 'package/dist/jsQR.js'), contentType: 'text/javascript' }));
  await p.route('**fonts.g**', r => r.abort());
  await p.goto('file://' + FILE);
  await p.waitForTimeout(500);
  const T = async t => { await p.click(`.tab[data-tab="${t}"]`); await p.waitForTimeout(100); };
  const toast = async () => (await p.textContent('#toast')).trim();

  // 1 車
  ok('起動: 見本の車3台', (await p.$$('#carList article')).length === 3);
  ok('バッジ: 発注(足りない3品)', (await p.textContent('.tab[data-tab="order"] .dot')) === '3');
  await p.click('#carFormTitle');
  await p.fill('#car_name', '試験 一郎'); await p.fill('#car_plate', '大阪 300 あ 11-22');
  await p.fill('#car_model', 'スズキ ジムニー'); await p.fill('#car_km', '5000');
  await p.fill('#car_shaken', '2026-12-01');
  await p.click('#carForm button[type=submit]');
  ok('車の登録', (await p.$$('#carList article')).length === 4, await toast());
  await p.fill('#carSearch', 'ジムニー'); ok('車の検索', (await p.$$('#carList article')).length === 1); await p.fill('#carSearch', '');
  // 記録(在庫引き)
  const jim = await p.$('#carList article:has-text("試験 一郎")');
  await (await jim.$('[data-act=recNew]')).click();
  await p.fill('#rec_work', 'オイル交換'); await p.fill('#rec_km', '5100'); await p.fill('#rec_labor', '1650');
  await p.click('[data-act=recAddPart]');
  await p.selectOption('#recParts .rp_part', 'p1'); await p.fill('#recParts .rp_qty', '4');
  await p.click('#recForm button[type=submit]');
  const st = await p.evaluate(() => JSON.parse(localStorage.getItem('markfactory.v1')));
  ok('記録保存+在庫引き(オイル24→20)', st.parts.find(x => x.id === 'p1').qty === 20, await toast());
  ok('記録で走行距離更新', st.cars.find(c => c.name === '試験 一郎').km === '5100');

  // 2 見積もり
  await T('est');
  const tot = await p.textContent('#estTotal');
  // 見本: 18000+1800+500=20300 税2030 法定0 → 22330
  ok('見積もり計算(見本 22,330円)', tot.includes('22,330円'), tot.replace(/\s+/g,' '));
  await p.click('[data-act=estAdd][data-kind="法定費用"]');
  const rows = await p.$$('#estRows tr'); const last = rows[rows.length-1];
  await (await last.$('[data-f=name]')).fill('重量税'); await (await last.$('[data-f=price]')).fill('8200');
  ok('法定費用は非課税で加算(30,530円)', (await p.textContent('#estTotal')).includes('30,530円'));
  await p.click('[data-act=estSave]'); ok('見積もり保存', (await toast()).includes('保存'));
  await p.click('[data-act=estCopy]'); await p.waitForTimeout(200);
  ok('見積もり文面コピー', (await toast()).includes('コピー'));

  // 3 在庫
  await T('stock');
  await p.click('#partFormTitle');
  await p.fill('#pt_code', 'OF-TOY-01'); await p.fill('#pt_name', '重複');
  await p.click('#partForm button[type=submit]');
  ok('品番の重複を止める', (await toast()).includes('もう登録'));
  await p.fill('#pt_code', 'TEST-1'); await p.fill('#pt_name', '試験部品'); await p.fill('#pt_qty', '0'); await p.fill('#pt_min', '2'); await p.fill('#pt_sup', '試験商会');
  await p.click('#partForm button[type=submit]');
  ok('部品の登録', (await p.textContent('#stockSum')).includes('登録 7品'), await p.textContent('#stockSum'));
  await p.check('#onlyLow'); ok('足りない物だけ(4品)', (await p.$$('#partList .item')).length === 4); await p.uncheck('#onlyLow');

  // 4 連絡
  await T('contact');
  ok('車検60日以内(見本2+試験1=3台)', (await p.$$('#ctList .item')).length === 3);
  await p.fill('#set_tel', '06-0000-0000'); await p.waitForTimeout(400);
  ok('文面に店電話が入る', (await p.textContent('#ctList .msg')).includes('06-0000-0000'));

  // 5 発注
  await T('order');
  const groups = await p.$$('#needList > .item');
  ok('仕入先ごとにまとめ(3社)', groups.length === 3);
  await p.click('#needList .item:has-text("試験商会") [data-act=makeOrder]');
  await p.click('[data-act=gotOrder]');
  const st2 = await p.evaluate(() => JSON.parse(localStorage.getItem('markfactory.v1')));
  ok('発注→入荷で在庫に足す(試験部品 0→4)', st2.parts.find(x => x.code === 'TEST-1').qty === 4);

  // 6 QR
  await T('qr');
  await p.setInputFiles('#pick', path.join(D, 'qr_known.png')); await p.waitForTimeout(1500);
  ok('QR読み取り(在庫の品番)', (await p.textContent('#qrOut')).includes('読めました'), (await p.textContent('#qrOut')).slice(0, 60));
  await p.click('#qrOut [data-act=qty][data-d="1"]'); await p.waitForTimeout(100);
  ok('QRから入庫', (await toast()).includes('在庫'));
  await p.setInputFiles('#pick', path.join(D, 'qr_new.png')); await p.waitForTimeout(1500);
  ok('QR読み取り(在庫に無い品番)', (await p.textContent('#qrOut')).includes('NEW-PART-77'));
  await p.fill('#qr_manual', 'oil-0w20-1l'); await p.click('[data-act=qrManual]');
  ok('品番の手入れ(大小文字無視)', (await p.textContent('#qrOut')).includes('エンジンオイル'));

  // 7 法律
  await T('law');
  ok('法律の手引き7項目', (await p.$$('#lawList details')).length === 7);
  ok('AI欄(このテストでは window.claude 無しで隠れる)', await p.isHidden('#aiLawBox'));

  // 控え
  const bk = await p.evaluate(() => localStorage.getItem('markfactory.v1'));
  await p.click('footer summary'); await p.fill('#backupBox', bk); await p.click('[data-act=backupLoad]');
  ok('控えから戻す', (await toast()).includes('戻しました'));
  await p.click('[data-act=clearSample]');
  await T('cars'); ok('見本を消す(試験の車だけ残る)', (await p.$$('#carList article')).length === 1);

  // 横はみ出し
  for (const t of ['cars','est','stock','contact','order','qr','law']) { await T(t); const w = await p.evaluate(() => document.documentElement.scrollWidth); ok('横はみ出し無し 390px: ' + t, w <= 390, 'scrollWidth=' + w); }
  // extra checks from caller
  if (fs.existsSync(path.join(D, 'dousa_test_tashita_rei.js'))) { p.setDefaultTimeout(5000); try { await require(path.join(D, 'dousa_test_tashita_rei.js'))(p, ok, T, toast, D); } catch (e) { ok('テストが途中で止まった', false, e.message.split('\n')[0]); } }
  ok('JSエラー無し', errs.length === 0, errs.join(' / '));
  console.log(results.join('\n'));
  console.log('\n合計 ' + results.length + ' 件 / NG ' + results.filter(r => r.startsWith('NG')).length + ' 件');
  await b.close();
})();

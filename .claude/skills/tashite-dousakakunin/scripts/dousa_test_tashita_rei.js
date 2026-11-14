// 足した4つの機能の照らし
const path = require('path');
module.exports = async (p, ok, T, toast, D) => {
  const iso = n => { const d = new Date(); d.setDate(d.getDate() + n); const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000); return z.toISOString().slice(0, 10); };
  const mon = n => { const d = new Date(); d.setDate(1); d.setMonth(d.getMonth() + n); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2); };
  await p.evaluate(() => { localStorage.clear(); });
  await p.reload(); await p.waitForTimeout(600);
  const st = () => p.evaluate(() => JSON.parse(localStorage.getItem('markfactory.v1') || 'null'));
  // 古い版のデータ(請求・予約が無い)を読んだ時の引き継ぎ
  await p.evaluate(() => { const s = JSON.parse(localStorage.getItem('markfactory.v1') || '{}'); });
  ok('[足] バッジ: 請求 未入金1', (await p.textContent('.tab[data-tab="inv"] .dot')) === '1');
  ok('[足] バッジ: 予約 今日1', (await p.textContent('.tab[data-tab="book"] .dot')) === '1');

  // 予約
  await T('book');
  ok('[予約] カレンダーが出る', (await p.$$('#cal .d')).length >= 28);
  ok('[予約] 今日の予約(山田 入庫中)', (await p.textContent('#dayList')).includes('山田'));
  await p.click(`#cal .d[data-d="${iso(3)}"]`);
  ok('[予約] 3日後は鈴木の車検(期間の途中)', (await p.textContent('#dayList')).includes('鈴木建設'));
  ok('[予約] 3日後 代車1は貸出中', /代車1[^・]*貸出中/.test(await p.textContent('#dayLoan')), (await p.textContent('#dayLoan')));
  await p.click('[data-act=bkNew]');
  await p.selectOption('#bk_car', 'c2'); await p.fill('#bk_date', iso(3)); await p.fill('#bk_end', iso(5)); await p.selectOption('#bk_loan', 'L1'); await p.fill('#bk_work', '板金');
  await p.click('#bkForm button[type=submit]');
  ok('[予約] 代車の二重貸しを止める', (await toast()).includes('貸し出し中'), await toast());
  await p.selectOption('#bk_loan', 'L2'); await p.click('#bkForm button[type=submit]');
  ok('[予約] 別の代車なら入る', (await st()).books.length === 4, await toast());
  await p.click(`#cal .d[data-d="${iso(0)}"]`).catch(() => {});
  await p.click('#dayList .item:has-text("山田") [data-act=bkNext]');
  ok('[予約] 仕上がった→完了', (await st()).books.find(b => b.id === 'b1').st === '完了');
  await p.click('[data-act=calMove][data-d="1"]'); ok('[予約] 次の月へ', (await p.textContent('#calTitle')).length > 0);

  // 見積もり→請求書
  await T('est');
  await p.click('[data-act=estToInv]'); await p.waitForTimeout(150);
  const s1 = await st(); const ni = s1.invs[s1.invs.length - 1];
  ok('[請求] 見積もりから請求書(番号 -002)', ni.no.endsWith('-002') && ni.no.includes(mon(0).replace('-', '')), ni.no);
  ok('[請求] 部品の仕入値を写す', ni.lines.find(l => l.part === 'p4').cost === 450);
  ok('[請求] 請求書の紙が出る 22,330円', (await p.textContent(`#invList .paper`)).includes('22,330円'));
  // 入金
  await p.click(`[data-act=payOpen][data-id="${ni.id}"]`);
  await p.selectOption(`#pay_m_${ni.id}`, '振込'); await p.click(`[data-act=payOk][data-id="${ni.id}"]`);
  ok('[請求] 入金→ゴールド', (await toast()).includes('ゴールド'), await toast());
  await p.selectOption('#invFilter', 'all');
  const it = await p.$(`#invList .item:has-text("${ni.no}")`);
  ok('[領収] 5万未満は印紙不要', (await it.textContent()).includes('領収書') && (await it.textContent()).includes('5万円未満'));
  await p.click(`[data-act=invCopy][data-id="${ni.id}"]`); await p.waitForTimeout(200);
  const clip = await p.evaluate(() => navigator.clipboard.readText());
  ok('[領収] 文面コピー', clip.includes('【領収書】') && clip.includes('22,330円'), clip.split('\n')[0]);
  await p.click('[data-act=invShow][data-k=rcpt][data-id="i2"]');
  ok('[領収] 税抜56,800円(振込)は印紙200円', (await p.textContent('#invList .item:has-text("タイヤ4本")')).includes('収入印紙 200円'));
  await p.click('[data-act=invShow][data-k=rcpt][data-id="i1"]');
  ok('[領収] カード払いは印紙不要', (await p.textContent('#invList .item:has-text("バッテリー交換")')).includes('カード払い'));
  await p.click('[data-act=invShow][data-k=inv][data-id="i4"]');
  ok('[請求] 法定費用は非課税で別 38,730円', (await p.textContent('#invList .item:has-text("' + 'MF-' + mon(0).replace('-', '') + '-001")')).includes('38,730円'));
  await p.click('#shopBox summary'); await p.fill('#inv_reg', 'T1234567890123'); await p.waitForTimeout(400);
  ok('[請求] 登録番号が紙に載る', (await p.textContent('#invList .paper')).includes('T1234567890123'));
  await p.click('#monBox summary'); await p.selectOption('#mon_c', '鈴木建設');
  ok('[月まとめ] 今回ご請求額は未入金だけ 38,730円', (await p.textContent('#monOut')).includes('今回ご請求額 38,730円'));
  await p.click('[data-act=payUndo][data-id="' + ni.id + '"]');
  ok('[請求] 入金を取り消す', !(await st()).invs.find(x => x.id === ni.id).paid);

  // 売上
  await T('sales');
  const tl = await p.textContent('#slTiles');
  ok('[売上] 今月 売上(税抜)40,600円', tl.includes('40,600円'), tl.slice(0, 80));
  ok('[売上] 今月 部品の粗利1,800円', tl.includes('部品の粗利1,800円'));
  ok('[売上] 今月 法定費用16,400円', tl.includes('16,400円'));
  ok('[売上] グラフ12か月', (await p.$$('#slChart text')).length >= 12 + 5);
  await p.fill('#sl_m', mon(-2)); await p.dispatchEvent('#sl_m', 'change');
  const t2 = await p.textContent('#slTiles');
  ok('[売上] 2か月前 74,400円・粗利6,700円', t2.includes('74,400円') && t2.includes('6,700円'), t2.slice(0, 90));
  ok('[売上] 仕入値不明の行を知らせる', (await p.textContent('#slNote')).includes('1行'));

  // 写真
  await T('cars');
  await p.click('[data-act=phOpen][data-id="c1"]'); await p.waitForTimeout(300);
  await p.setInputFiles('#phPick_c1', [path.join(D, 'qr_known.png'), path.join(D, 'qr_new.png')]); await p.waitForTimeout(1500);
  ok('[写真] 2枚しまう', (await p.$$('#carList .ph')).length === 2, await toast());
  await p.click('#carList [data-act=phView]'); ok('[写真] 大きく見る', await p.isVisible('#phViewer'));
  await p.click('[data-act=phClose]'); ok('[写真] 閉じる', await p.isHidden('#phViewer'));
  await p.reload(); await p.waitForTimeout(800); await T('cars');
  ok('[写真] 読み込み直しても残る', (await p.textContent('#carList [data-act=phOpen][data-id="c1"]')).includes('2枚'));
  await p.click('[data-act=phOpen][data-id="c1"]');
  await p.click('footer summary'); await p.check('#bk_photos'); await p.click('[data-act=backupCopy]'); await p.waitForTimeout(800);
  const bk = await p.evaluate(() => navigator.clipboard.readText());
  ok('[写真] 控えに写真が入る', bk.includes('"photos"') && bk.includes('data:image/jpeg'), 'len=' + bk.length);
  await p.click('#carList [data-act=phDel]'); await p.click('#carList [data-act=phDel]'); await p.waitForTimeout(300);
  ok('[写真] 2回押しで消す', (await p.$$('#carList .ph')).length === 1);
  await p.fill('#backupBox', bk); await p.click('[data-act=backupLoad]'); await p.waitForTimeout(800);
  ok('[写真] 控えから写真も戻る', (await p.$$('#carList .ph')).length === 2);

  for (const t of ['book', 'inv', 'sales']) { await T(t); const w = await p.evaluate(() => document.documentElement.scrollWidth); ok('[足] 横はみ出し無し 390px: ' + t, w <= 390, 'scrollWidth=' + w); }
  // 見た目用(自分で見る)
  await T('inv'); await p.selectOption('#invFilter', 'all'); await p.screenshot({ path: path.join(D, 'shot_inv.png'), fullPage: true });
  await T('sales'); await p.fill('#sl_m', mon(0)); await p.dispatchEvent('#sl_m', 'change'); await p.screenshot({ path: path.join(D, 'shot_sales.png'), fullPage: true });
  await T('book'); await p.emulateMedia({ colorScheme: 'dark' }); await p.screenshot({ path: path.join(D, 'shot_book_dark.png'), fullPage: true });
};

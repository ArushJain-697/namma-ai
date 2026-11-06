// Drives the phone page in a real headless browser at phone size. Usage: node e2e_phone.js <base url>
const { chromium } = require('playwright');
(async () => {
  const base = process.argv[2];
  const quiz = await (await fetch(base + 'quiz.json')).json();
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  const external = [], errors = [];
  page.on('request', (r) => { const h = new URL(r.url()).hostname; if (!['127.0.0.1', 'localhost'].includes(h)) external.push(r.url()); });
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(base);
  await page.waitForSelector('#qtext');
  const out = { header: await page.textContent('#header'), n: quiz.items.length, verdicts: [], typed: 0, clicked: 0, retryAsked: 0 };
  const findItem = (stem) => quiz.items.find((i) => i.stem === stem);
  const answerWrong = async (hasOpts, key, options) => {
    if (hasOpts) { const wrong = options.findIndex((o) => o.toLowerCase() !== key.toLowerCase()); await page.click(`[data-opt="${wrong}"]`); out.clicked++; }
    else { await page.fill('#typed', 'zzz'); await page.click('#submit'); out.typed++; }
  };
  const answerRight = async (hasOpts, key, options) => {
    if (hasOpts) { const i = options.findIndex((o) => o.toLowerCase() === key.toLowerCase()); await page.click(`[data-opt="${i}"]`); out.clicked++; }
    else { await page.fill('#typed', key.toUpperCase() + '.'); await page.press('#typed', 'Enter'); out.typed++; }
  };
  for (let k = 0; k < quiz.items.length; k++) {
    const stem = await page.textContent('#qtext');
    const item = findItem(stem);
    if (!item) throw new Error('question not in quiz.json: ' + stem);
    const hasOpts = !!(item.options && item.options.length);
    if (k === 0) {
      await answerWrong(hasOpts, item.key, item.options);
      const verdict = await page.textContent('#verdict');
      out.firstVerdict = verdict;
      out.firstWitnessShown = (await page.textContent('#witness')).includes(item.witness);
      out.firstAnswerShown = (await page.textContent('#answer')).includes(item.key);
      out.hitCount = await page.locator('.s.hit').count();
      out.hitText = await page.locator('.s.hit').first().textContent();
      out.firstWitness = item.witness; out.firstWitnessIdx = item.witness_idx;
      out.optionsDisabled = hasOpts ? await page.locator('.opt[disabled]').count() : null;
    } else {
      await answerRight(hasOpts, item.key, item.options);
      out.verdicts.push((await page.textContent('#verdict')).split('.')[0]);
    }
    await page.click('#next');
    if (k < quiz.items.length - 1) await page.waitForFunction((prev) => document.querySelector('#qtext') && document.querySelector('#qtext').textContent !== prev, stem);
  }
  // Reread Loop for the one miss: a new question from the same sentence, unless its key was already revealed
  const first = quiz.items[0];
  const reserveUsable = first.reserve && !quiz.items.some((i) => i.key.toLowerCase() === first.reserve.key.toLowerCase());
  out.reserveUsable = !!reserveUsable;
  if (reserveUsable) {
    await page.waitForFunction(() => document.body.textContent.includes('You missed sentence'));
    out.rereadMessage = true;
    await page.waitForFunction(() => document.querySelector('#qtext'), null, { timeout: 5000 });
    out.retryStemIsReserve = (await page.textContent('#qtext')) === first.reserve.stem;
    out.retryAsked++;
    await answerWrong(!!(first.reserve.options && first.reserve.options.length), first.reserve.key, first.reserve.options);
    await page.click('#next');
  }
  await page.waitForSelector('#end');
  out.score = await page.textContent('#score');
  out.reread = (await page.locator('#reread').count()) ? await page.textContent('#reread') : null;
  out.skippedShown = (await page.locator('#skipped').count()) ? (await page.textContent('#skipped')).includes(first.witness) : false;
  out.summaryShown = (await page.locator('#summary').count()) > 0;
  out.hitAfterEnd = await page.locator('.s.hit').count();
  out.room = await (await fetch(base + 'room')).json();
  out.external = external; out.errors = errors;
  await browser.close();
  console.log('RESULT ' + JSON.stringify(out));
})().catch((e) => { console.log('FAILED ' + e.stack); process.exit(1); });

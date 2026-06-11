import { chromium } from 'playwright';

const FRONTEND = 'http://localhost:5173';
const BACKEND  = 'http://localhost:8765';

async function clearProfiles() {
  const res = await fetch(`${BACKEND}/profiles/`);
  const profiles = await res.json();
  for (const p of profiles) {
    await fetch(`${BACKEND}/profiles/${p.id}`, { method: 'DELETE' });
  }
  console.log(`[setup] Deleted ${profiles.length} profile(s)`);
}

async function snap(page, name) {
  await page.screenshot({ path: `C:/tmp/${name}.png`, fullPage: false });
  console.log(`    [screenshot] ${name}.png`);
}

(async () => {
  await clearProfiles();

  const browser = await chromium.launch({ headless: true, slowMo: 100 });
  const ctx     = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page    = await ctx.newPage();

  const errors = [];
  page.on('pageerror', e => errors.push(`JS: ${e.message}`));
  page.on('console', m => { if (m.type() === 'error') errors.push(`CON: ${m.text()}`); });

  // 1 ─ Welcome
  console.log('\n[1] Welcome screen...');
  await page.goto(FRONTEND, { waitUntil: 'domcontentloaded' });
  await page.waitForURL('**/welcome', { timeout: 8000 });
  await page.waitForTimeout(500);
  await snap(page, '01_welcome');
  console.log(`    URL: ${page.url()}`);
  console.log('    OK');

  // 2 ─ ProfileSetup
  console.log('\n[2] Navigating to ProfileSetup...');
  await page.click('button:has-text("COMEÇAR")');
  await page.waitForURL('**/profile-setup', { timeout: 8000 });
  await page.waitForTimeout(400);
  await snap(page, '02_profile_setup');
  console.log('    OK');

  // 3 ─ Fill form
  console.log('\n[3] Filling profile form...');
  await page.fill('input', 'Gabriel Zambe');
  await page.waitForTimeout(200);
  await page.locator('text=Mock Engine').click();
  await page.waitForTimeout(200);
  await page.locator('text=Normal (1000ms)').click();
  await snap(page, '03_profile_filled');
  console.log('    OK');

  // 4 ─ Submit → Calibration intro
  console.log('\n[4] Submitting profile...');
  await page.click('button:has-text("PRÓXIMO")');
  // Give React time to process navigation + Zustand state
  await page.waitForTimeout(2000);
  await snap(page, '04a_after_click');
  console.log('    URL after 2s:', page.url());
  // If redirected back to welcome, log it
  if (page.url().includes('welcome')) {
    console.log('    REDIRECT to welcome detected! Checking page content...');
    const body = await page.content();
    console.log('    Has "Calibração": ', body.includes('Calibra'));
  }
  await page.waitForURL('**/calibration', { timeout: 10000 });
  await page.waitForTimeout(1000);
  await snap(page, '04b_calibration_url');
  console.log('    URL at /calibration:', page.url());
  const html = await page.content();
  console.log('    Has "Calibração":', html.includes('Calibraç'));
  console.log('    Has SideNav:', html.includes('IrisFlow Control'));
  console.log('    JS errors so far:', JSON.stringify(errors));
  const bodySnippet = (await page.locator('body').innerHTML()).replace(/\s+/g,' ').substring(0,400);
  console.log('    Body:', bodySnippet);
  await page.waitForSelector('text=Calibração do Olhar', { timeout: 15000 });
  await snap(page, '04_calibration_intro');
  console.log('    URL:', page.url());
  console.log('    OK');

  // 5 ─ Start calibration
  console.log('\n[5] Starting calibration...');
  await page.click('text=INICIAR CALIBRAÇÃO');
  await page.waitForSelector('text=Olhe para o ponto', { timeout: 8000 });
  await page.waitForTimeout(800);
  await snap(page, '05_calibrating');
  console.log('    OK');

  // 6 ─ Click all 9 points
  console.log('\n[6] Advancing through 9 calibration points...');
  for (let i = 0; i < 9; i++) {
    await page.waitForTimeout(1200);
    await page.locator('.cal-glow').first().click({ force: true, timeout: 4000 }).catch(async () => {
      await page.mouse.click(960, 540);
    });
    console.log(`    Point ${i + 1}/9`);
  }
  await snap(page, '06_points_done');

  // 7 ─ Fitting
  console.log('\n[7] Fitting phase...');
  await page.waitForSelector('text=Processando calibração', { timeout: 10000 }).catch(() => {
    console.log('    (fitting screen brief)');
  });
  await snap(page, '07_fitting');
  console.log('    OK');

  // 8 ─ Result
  console.log('\n[8] Waiting for result...');
  await page.waitForSelector('button:has-text("CONCLUIR")', { timeout: 30000 });
  await page.waitForTimeout(500);
  await snap(page, '08_result');
  const accuracy = await page.locator('.font-display-lg').first().textContent().catch(() => '?');
  console.log(`    Accuracy: "${accuracy}"`);
  console.log('    OK');

  // 9 ─ CONCLUIR → OnboardingReady
  console.log('\n[9] Clicking CONCLUIR...');
  await page.click('button:has-text("CONCLUIR")');
  await page.waitForURL('**/onboarding-ready', { timeout: 8000 });
  await page.waitForTimeout(500);
  await snap(page, '09_onboarding_ready');
  const readyH1 = await page.locator('h1').first().textContent().catch(() => '?');
  console.log(`    H1: "${readyH1}"`);
  console.log('    OK');

  // 10 ─ ACESSAR HOME → Dashboard
  console.log('\n[10] Clicking ACESSAR HOME...');
  await page.click('button:has-text("ACESSAR HOME")');
  await page.waitForURL(`${FRONTEND}/`, { timeout: 8000 });
  await page.waitForTimeout(600);
  await snap(page, '10_dashboard');
  console.log('    URL:', page.url());
  console.log('    OK');

  // 11 ─ TopBar name check
  console.log('\n[11] Checking TopBar profile name...');
  const headerText = await page.locator('header').first().textContent().catch(() => '');
  const hasName = headerText.includes('Gabriel Zambe');
  await snap(page, '11_topbar');
  console.log(`    "Gabriel Zambe" visible: ${hasName ? 'YES' : 'NO'}`);

  // 12 ─ QuickPhrases categories
  console.log('\n[12] Checking QuickPhrases categories...');
  await page.goto(`${FRONTEND}/phrases`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  await snap(page, '12_quickphrases');
  const catHeadings = await page.$$eval('h2', els => els.map(e => e.textContent.trim()).filter(Boolean));
  console.log(`    Categories: ${JSON.stringify(catHeadings)}`);
  const hasCategories = catHeadings.some(c => ['Saúde','Necessidades','Social','Emoções'].some(k => c.includes(k.substring(0,4))));
  console.log(`    API categories shown: ${hasCategories ? 'YES' : 'NO'}`);

  // ─ Summary
  console.log('\n══════════════════════════════════════════');
  if (errors.length > 0) {
    console.log(`ERRORS (${errors.length}):`);
    errors.forEach(e => console.log(' ', e));
  } else {
    console.log('Zero JS errors during entire flow');
  }
  console.log('Screenshots: C:/tmp/*.png');

  await browser.close();
})();

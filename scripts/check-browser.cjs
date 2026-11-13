const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
  fs.mkdirSync('artifacts', {recursive:true});
  const browser = await chromium.launch({headless:true, channel:process.env.BROWSER_CHANNEL || 'msedge'});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://localhost/',{waitUntil:'networkidle'});
    assert.equal(await page.locator('article').count(),9);
    assert.equal(await page.locator('.owner, #students, #identity, #dns').count(),0);
    await page.screenshot({path:'artifacts/portal-desktop.png',fullPage:true});
    for(const width of [390,768]) {
      await page.setViewportSize({width,height:844});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
      await page.screenshot({path:`artifacts/portal-${width}.png`,fullPage:true});
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.getByRole('link',{name:'Xem sinh viên →',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#student-body').rows.length===5);
    await page.getByRole('link',{name:'← Tất cả dịch vụ',exact:true}).click();
    await page.getByRole('link',{name:'Đọc dữ liệu →',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#student-body').rows.length===3);
    await page.getByRole('link',{name:'← Tất cả dịch vụ',exact:true}).click();
    await page.getByRole('link',{name:'Xem bản ghi →',exact:true}).click();
    await page.click('#dns-reload');
    await page.waitForFunction(()=>document.querySelector('#dns-result').textContent.includes('10.10.10.20'));
    assert.equal(await page.locator('#students').isVisible(),false);
    await page.getByRole('link',{name:'← Tất cả dịch vụ',exact:true}).click();
    await page.getByRole('link',{name:'Mở dịch vụ →',exact:true}).click();
    await page.fill('[name=username]','sv01'); await page.fill('[name=password]','123456');
    await page.click('[type=submit]');
    await page.waitForFunction(()=>document.querySelector('#login-state').textContent.includes('Đã xác thực: sv01'));
    await page.getByRole('link',{name:'← Tất cả dịch vụ',exact:true}).click();
    await page.getByRole('link',{name:'Kiểm tra phân phối →',exact:true}).click();
    await page.click('#balance');
    await page.waitForFunction(()=>document.querySelector('#balance-result').textContent.includes(' → '));
    await page.screenshot({path:'artifacts/service-desktop.png',fullPage:true});
    for(const width of [390,768]) {
      await page.setViewportSize({width,height:844});
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
      assert.equal(overflow,false,`Page overflow at ${width}`);
      await page.screenshot({path:`artifacts/service-${width}.png`,fullPage:true});
    }
    assert.deepEqual(errors,[]);
    await page.setViewportSize({width:1440,height:1000});
    await page.goto('http://localhost:3000/login',{waitUntil:'domcontentloaded'});
    await page.getByPlaceholder('email or username').fill('admin');
    await page.getByPlaceholder('password').fill('admin');
    await page.getByRole('button',{name:'Log in',exact:true}).click();
    await page.waitForTimeout(1500);
    const skip=page.getByRole('button',{name:'Skip',exact:true});
    if(await skip.isVisible()) await skip.click();
    await page.goto('http://localhost:3000/d/minicloud-health',{waitUntil:'networkidle'});
    await page.getByText('CPU Usage (%)',{exact:true}).first().waitFor();
    await page.screenshot({path:'artifacts/grafana-dashboard.png',fullPage:true});
    console.log('PASS browser: JSON, DB, DNS, token, Round Robin, nine services, desktop/mobile, Grafana');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});

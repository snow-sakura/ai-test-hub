import { chromium } from 'playwright'

const paths = [
  ['/modules/aitest/projects', '项目管理'],
  ['/modules/aitest/ai-tester', 'AI评测师'],
  ['/modules/aitest/reports', '测试报告'],
  ['/modules/aitest/config/model', 'AI模型配置'],
  ['/modules/aitest/config/prompt', 'AI提示词配置'],
  ['/modules/aitest/config/generation', '生成行为配置'],
  ['/modules/aitest/config/mode', '智能模式配置'],
]

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage()
await page.goto('http://localhost:5173/login')
await page.fill('input[type="text"]', 'admin')
await page.fill('input[type="password"]', 'admin123')
await page.click('button.el-button--primary')
await page.waitForURL(u => !u.pathname.includes('/login'))

for (const [path, name] of paths) {
  await page.goto(`http://localhost:5173${path}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  const info = await page.evaluate(() => ({
    url: location.href,
    title: document.querySelector('h1,h2,.page-title')?.textContent?.trim(),
    buttons: [...document.querySelectorAll('button')].slice(0, 15).map(b => b.textContent?.trim()),
    hasTable: !!document.querySelector('.el-table'),
    hasPageWrap: !!document.querySelector('.page-wrap'),
    hasCard: !!document.querySelector('.el-card'),
    hasForm: !!document.querySelector('.el-form'),
    bodySnippet: document.body.innerText.slice(0, 500),
  }))
  console.log('\n===', name, '===')
  console.log(JSON.stringify(info, null, 2))
}
await browser.close()

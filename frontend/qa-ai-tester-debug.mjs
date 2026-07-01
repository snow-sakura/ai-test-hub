import { chromium } from 'playwright'

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage()
const errors = []
page.on('console', m => { if (m.type()==='error') errors.push(m.text()) })
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message))

await page.goto('http://localhost:5173/login')
await page.fill('input[type="text"]', 'admin')
await page.fill('input[type="password"]', 'admin123')
await page.click('button.el-button--primary')
await page.waitForURL(u => !u.pathname.includes('/login'))

await page.goto('http://localhost:5173/modules/aitest/ai-tester', { waitUntil: 'networkidle' })
await page.waitForTimeout(3000)
console.log('URL:', page.url())
console.log('Body length:', (await page.textContent('body'))?.length)
console.log('Errors:', errors)
console.log('HTML snippet:', (await page.content()).slice(0, 2000))
await browser.close()

import { chromium } from 'playwright'

async function freshPage() {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto('http://localhost:5173/login')
  await page.fill('input[type="text"]', 'admin')
  await page.fill('input[type="password"]', 'admin123')
  await page.click('button.el-button--primary')
  await page.waitForURL(u => !u.pathname.includes('/login'))
  return { browser, page }
}

const isolated = []

// 项目管理 - 详情跳转
{
  const { browser, page } = await freshPage()
  await page.goto('http://localhost:5173/modules/aitest/projects', { waitUntil: 'networkidle' })
  await page.locator('.el-table__row').first().locator('button').filter({ hasText: '查看' }).click()
  await page.waitForTimeout(1500)
  isolated.push({ test: '项目管理-查看详情', pass: page.url().includes('/projects/'), url: page.url() })
  await browser.close()
}

// 测试报告
{
  const { browser, page } = await freshPage()
  await page.goto('http://localhost:5173/modules/aitest/reports', { waitUntil: 'networkidle' })
  const checks = {
    title: await page.getByText('AI 测试报告').isVisible(),
    rows: (await page.locator('.el-table__row').count()) > 0,
  }
  await page.locator('button').filter({ hasText: '查看详情' }).first().click()
  await page.waitForTimeout(1000)
  checks.dialog = await page.locator('.el-dialog').isVisible()
  isolated.push({ test: '测试报告', pass: Object.values(checks).every(Boolean), checks })
  await browser.close()
}

// 配置页
for (const [path, name, kw] of [
  ['/modules/aitest/config/model', 'AI模型配置', '新建模型配置'],
  ['/modules/aitest/config/prompt', 'AI提示词配置', '新建提示词'],
  ['/modules/aitest/config/generation', '生成行为配置', '保存配置'],
  ['/modules/aitest/config/mode', '智能模式配置', '启用 AI 模式'],
]) {
  const { browser, page } = await freshPage()
  await page.goto(`http://localhost:5173${path}`, { waitUntil: 'networkidle' })
  const body = await page.textContent('body')
  isolated.push({ test: name, pass: body?.includes(kw), keyword: kw })
  await browser.close()
}

// AI用例生成 - 展开管线选项
{
  const { browser, page } = await freshPage()
  await page.goto('http://localhost:5173/modules/aitest/generate', { waitUntil: 'networkidle' })
  await page.locator('.el-collapse-item').first().click()
  await page.waitForTimeout(500)
  const body = await page.textContent('body')
  isolated.push({ test: 'AI用例生成-管线类型', pass: body?.includes('LangGraph') || body?.includes('传统管线') })
  await browser.close()
}

console.log(JSON.stringify(isolated, null, 2))

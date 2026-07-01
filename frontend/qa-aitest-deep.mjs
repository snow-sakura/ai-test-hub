/**
 * AI智能测试 - 深度交互验证（修正选择器 + 业务逻辑）
 */
import { chromium } from 'playwright'
import { writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

const BASE = 'http://localhost:5173'
const SCREENSHOT_DIR = join(process.cwd(), 'qa-screenshots')
mkdirSync(SCREENSHOT_DIR, { recursive: true })

const results = []

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
  await page.fill('input[type="text"]', 'admin')
  await page.fill('input[type="password"]', 'admin123')
  await page.click('button.el-button--primary')
  await page.waitForURL(u => !u.pathname.includes('/login'))
}

async function navSidebar(page, text) {
  await page.locator('.sidebar-menu a, .el-menu-item').filter({ hasText: text }).first().click()
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(600)
}

async function testModule(page, name, fn) {
  const pageErrors = []
  const handler = (e) => pageErrors.push(e.message)
  page.on('pageerror', handler)
  const r = { module: name, pass: false, checks: [], pageErrors: [] }
  try {
    r.checks = await fn(page)
    r.pass = r.checks.every(c => c.pass !== false)
  } catch (e) {
    r.error = e.message
  }
  r.pageErrors = [...pageErrors]
  page.off('pageerror', handler)
  results.push(r)
}

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
await login(page)
await page.goto(`${BASE}/modules/aitest/dashboard`, { waitUntil: 'networkidle' })

// 1. 测试总览
await testModule(page, '测试总览', async (p) => {
  await navSidebar(p, '测试总览')
  return [
    { name: 'KPI卡片', pass: await p.locator('.stat-label').filter({ hasText: '项目总数' }).isVisible() },
    { name: '趋势图', pass: await p.locator('.card-title').filter({ hasText: '用例趋势' }).isVisible() },
    { name: '快速入口可点击', pass: (await p.locator('.entry-card').count()) >= 3 },
    { name: '快速入口跳转', pass: await (async () => {
      const before = p.url()
      await p.locator('.entry-card').first().click()
      await p.waitForTimeout(800)
      return p.url() !== before
    })() },
  ]
})

// 2. 项目管理
await testModule(page, '项目管理', async (p) => {
  await navSidebar(p, '项目管理')
  const checks = [
    { name: '页面标题', pass: await p.locator('h1.page-title').filter({ hasText: '测试项目管理' }).isVisible() },
    { name: '新建项目按钮', pass: await p.locator('button').filter({ hasText: '新建项目' }).isVisible() },
    { name: '项目表格有数据', pass: (await p.locator('.el-table__row').count()) > 0 },
    { name: '搜索筛选', pass: await p.locator('.filter-bar input').first().isVisible() },
    { name: '状态筛选', pass: await p.locator('.status-select, .filter-bar .el-select').first().isVisible() },
  ]
  // 交互：搜索
  await p.locator('.filter-bar input').first().fill('测试项目')
  await p.waitForTimeout(500)
  checks.push({ name: '搜索过滤生效', pass: (await p.locator('.el-table__row').count()) > 0 })
  // 交互：打开详情
  await p.locator('button').filter({ hasText: '查看' }).first().click()
  await p.waitForLoadState('networkidle')
  checks.push({ name: '项目详情页跳转', pass: p.url().includes('/projects/') })
  return checks
})

// 3. 用例列表
await testModule(page, '用例列表', async (p) => {
  await navSidebar(p, '用例列表')
  return [
    { name: '用例表格', pass: await p.locator('.el-table').isVisible() },
    { name: '新建用例', pass: await p.locator('button').filter({ hasText: /新建/ }).first().isVisible() },
    { name: '用例数据', pass: (await p.locator('.el-table__row').count()) > 0 },
  ]
})

// 4. 用例评审
await testModule(page, '用例评审', async (p) => {
  await navSidebar(p, '用例评审')
  return [
    { name: '评审统计', pass: await p.locator('.stat-label').filter({ hasText: '待评审' }).isVisible() },
    { name: '新建评审', pass: await p.locator('button').filter({ hasText: '新建评审' }).isVisible() },
    { name: '状态筛选', pass: await p.locator('.filter-bar .el-select').first().isVisible() },
  ]
})

// 5. AI用例生成
await testModule(page, 'AI用例生成', async (p) => {
  await navSidebar(p, 'AI用例生成')
  const checks = [
    { name: '需求输入区', pass: await p.locator('textarea').first().isVisible() },
    { name: '文档上传区', pass: await p.getByText('上传文档').isVisible() },
    { name: '模型选择', pass: await p.locator('.config-row .el-select').first().isVisible() },
    { name: '自动评审选项', pass: await p.getByText('自动评审').isVisible() },
    { name: '管线类型', pass: await p.getByText('LangGraph').isVisible() },
  ]
  await p.locator('textarea').first().fill('用户登录：用户名密码校验、验证码、错误提示')
  checks.push({ name: '填写需求后生成按钮可用', pass: await p.locator('button').filter({ hasText: '开始生成' }).isEnabled() })
  return checks
})

// 6. AI生成记录
await testModule(page, 'AI生成记录', async (p) => {
  await navSidebar(p, 'AI生成记录')
  return [
    { name: '记录列表', pass: await p.locator('.el-table').isVisible() },
    { name: '有历史记录', pass: (await p.locator('.el-table__row').count()) > 0 },
  ]
})

// 7. AI评测师 - 已知 bug
await testModule(page, 'AI评测师', async (p) => {
  await navSidebar(p, 'AI评测师')
  await p.waitForTimeout(2000)
  const bodyText = await p.textContent('body') || ''
  return [
    { name: '页面正常渲染', pass: bodyText.includes('会话历史') || bodyText.includes('AI 评测师'), note: bodyText.length < 100 ? '页面白屏' : '' },
    { name: '新建对话按钮', pass: await p.locator('button').filter({ hasText: /新建对话/ }).first().isVisible().catch(() => false) },
    { name: '模型选择器', pass: await p.locator('.chat-header .el-select').isVisible().catch(() => false) },
  ]
})

// 8. 测试报告
await testModule(page, '测试报告', async (p) => {
  await navSidebar(p, '测试报告')
  const checks = [
    { name: '报告标题', pass: await p.getByText('AI 测试报告').isVisible() },
    { name: '项目筛选', pass: await p.getByText('全部项目').isVisible() },
    { name: '时间范围', pass: await p.getByText('时间范围').isVisible() },
    { name: '报告列表', pass: (await p.locator('.el-table__row').count()) > 0 },
  ]
  // 交互：查看详情
  await p.locator('button').filter({ hasText: '查看详情' }).first().click()
  await p.waitForTimeout(800)
  checks.push({ name: '报告详情弹窗', pass: await p.locator('.el-dialog, .el-drawer').isVisible().catch(() => false) })
  return checks
})

// 9-12 配置页
const configTests = [
  ['AI模型配置', '新建模型配置', ['writer', 'reviewer', '测试连接']],
  ['AI提示词配置', '新建提示词', ['编写提示词', '评审']],
  ['生成行为配置', '保存配置', ['启用 AI 评审', '默认输出模式', '评审超时']],
  ['智能模式配置', '保存配置', ['启用 AI 模式', '自动触发策略', '通知设置']],
]

for (const [name, btnText, keywords] of configTests) {
  await testModule(page, name, async (p) => {
    await navSidebar(p, name)
    const checks = [
      { name: '主操作按钮', pass: await p.locator('button').filter({ hasText: btnText }).isVisible() },
    ]
    const body = await p.textContent('body') || ''
    for (const kw of keywords) {
      checks.push({ name: `包含「${kw}」`, pass: body.includes(kw) })
    }
    return checks
  })
}

await browser.close()

const passed = results.filter(r => r.pass).length
const report = {
  summary: { total: results.length, passed, failed: results.length - passed, passRate: `${Math.round(passed/results.length*100)}%` },
  results,
  bugs: results.filter(r => r.pageErrors.length > 0 || r.error).map(r => ({ module: r.module, errors: r.pageErrors, error: r.error })),
}
writeFileSync(join(SCREENSHOT_DIR, 'deep-report.json'), JSON.stringify(report, null, 2))
console.log(JSON.stringify(report, null, 2))

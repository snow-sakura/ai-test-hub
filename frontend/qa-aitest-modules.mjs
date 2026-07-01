/**
 * AI智能测试模块 - 侧边栏各子模块自动化验证
 * 运行: node qa-aitest-modules.mjs
 */
import { chromium } from 'playwright'
import { writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

const BASE = 'http://localhost:5173'
const SCREENSHOT_DIR = join(process.cwd(), 'qa-screenshots')
mkdirSync(SCREENSHOT_DIR, { recursive: true })

/** 侧边栏菜单及业务验证规则 */
const MODULES = [
  {
    name: '测试总览',
    path: '/modules/aitest/dashboard',
    sidebarText: '测试总览',
    pageTitle: '测试总览',
    businessChecks: [
      { type: 'text', selector: '.stat-label', expectAny: ['项目总数', '用例总数', '成员总数', '待评审'] },
      { type: 'text', selector: '.card-title', expectAny: ['用例趋势', '用例优先级分布', '快速入口'] },
    ],
    industryLogic: '测试总览应聚合项目/用例/成员/待评审等核心 KPI，并提供快速入口跳转至常用功能（行业标准：质量看板）',
  },
  {
    name: '项目管理',
    path: '/modules/aitest/projects',
    sidebarText: '项目管理',
    pageTitle: '测试项目管理',
    businessChecks: [
      { type: 'visible', selector: 'button:has-text("新建项目")' },
      { type: 'visible', selector: '.filter-bar input[placeholder*="搜索"]' },
      { type: 'visible', selector: '.el-table' },
    ],
    interaction: async (page) => {
      const search = page.locator('.filter-bar input').first()
      await search.fill('test')
      await page.waitForTimeout(500)
      await search.clear()
    },
    industryLogic: '项目管理是测试资产组织单元，应支持创建/搜索/状态筛选/批量操作（TestBrain、企业级AI Test平台标准）',
  },
  {
    name: '用例列表',
    path: '/modules/aitest/testcases',
    sidebarText: '用例列表',
    pageTitle: null,
    businessChecks: [
      { type: 'visible', selector: 'button:has-text("新建用例"), button:has-text("新建")' },
      { type: 'visible', selector: '.el-table, .config-table-card' },
    ],
    industryLogic: '用例列表是测试设计核心资产库，应支持 CRUD、优先级/类型/状态筛选（结构化用例管理）',
  },
  {
    name: '用例评审',
    path: '/modules/aitest/review-cases',
    sidebarText: '用例评审',
    pageTitle: '用例评审',
    businessChecks: [
      { type: 'text', selector: '.stat-label', expectAny: ['全部评审', '待评审', '已通过', '已驳回'] },
      { type: 'visible', selector: 'button:has-text("新建评审")' },
    ],
    industryLogic: '用例评审用于质量门禁，应区分待评审/通过/驳回状态，支持人工+AI协同评审（行业：覆盖率与规范性检查）',
  },
  {
    name: 'AI用例生成',
    path: '/modules/aitest/generate',
    sidebarText: 'AI用例生成',
    pageTitle: 'AI 用例生成',
    businessChecks: [
      { type: 'visible', selector: 'textarea, .el-textarea__inner' },
      { type: 'visible', selector: 'button:has-text("开始生成")' },
      { type: 'text', selector: 'body', expectAny: ['需求输入', '手动输入', '上传文档', '选择模型'] },
    ],
    interaction: async (page) => {
      const textarea = page.locator('textarea').first()
      await textarea.fill('用户登录功能：支持用户名密码登录，失败显示错误提示')
      const btn = page.locator('button:has-text("开始生成")')
      const enabled = await btn.isEnabled()
      return { generateButtonEnabled: enabled }
    },
    industryLogic: 'AI用例生成应支持需求文本/文档输入、模型与提示词选择、自动评审选项（Spec2Case/TestBrain：需求→结构化用例）',
  },
  {
    name: 'AI生成记录',
    path: '/modules/aitest/generate/records',
    sidebarText: 'AI生成记录',
    pageTitle: null,
    businessChecks: [
      { type: 'visible', selector: '.el-table, .config-table-card, .page-wrap' },
    ],
    industryLogic: '生成记录应追踪每次 AI 生成任务的状态、进度与结果，支持审计与回溯（多Agent协作平台标准）',
  },
  {
    name: 'AI评测师',
    path: '/modules/aitest/ai-tester',
    sidebarText: 'AI评测师',
    pageTitle: null,
    businessChecks: [
      { type: 'text', selector: 'body', expectAny: ['会话历史', '新建对话', 'AI 评测师', 'AI评测师'] },
      { type: 'visible', selector: 'button:has-text("新建对话"), button:has-text("+ 新建对话")' },
    ],
    interaction: async (page) => {
      const newChat = page.locator('button:has-text("新建对话")').first()
      if (await newChat.isVisible()) await newChat.click()
      await page.waitForTimeout(300)
    },
    industryLogic: 'AI评测师是对话式测试助手，应支持多会话、模型切换、测试咨询与用例评审建议（质量数字人Agent）',
  },
  {
    name: '测试报告',
    path: '/modules/aitest/reports',
    sidebarText: '测试报告',
    pageTitle: null,
    businessChecks: [
      { type: 'visible', selector: '.page-wrap, .el-card' },
    ],
    industryLogic: '测试报告应汇总执行结果、缺陷分布与质量趋势，支持可视化分析（企业级平台：报告分析闭环）',
  },
  {
    name: 'AI模型配置',
    path: '/modules/aitest/config/model',
    sidebarText: 'AI模型配置',
    pageTitle: null,
    businessChecks: [
      { type: 'visible', selector: 'button:has-text("新增"), button:has-text("新建"), button:has-text("添加")' },
      { type: 'visible', selector: '.el-table, .config-table-card' },
    ],
    industryLogic: '模型配置应管理 LLM 连接（API Key、Base URL、温度等），支持 writer/reviewer 等角色分工',
  },
  {
    name: 'AI提示词配置',
    path: '/modules/aitest/config/prompt',
    sidebarText: 'AI提示词配置',
    pageTitle: null,
    businessChecks: [
      { type: 'visible', selector: '.el-table, .config-table-card, .page-wrap' },
    ],
    industryLogic: '提示词配置驱动 Prompt 工程，定义用例生成/评审规则（双驱动：Prompt + 领域知识库）',
  },
  {
    name: '生成行为配置',
    path: '/modules/aitest/config/generation',
    sidebarText: '生成行为配置',
    pageTitle: null,
    businessChecks: [
      { type: 'visible', selector: '.page-wrap, .el-form, .el-card' },
    ],
    industryLogic: '生成行为配置控制输出模式、自动评审开关、管线类型等传统/ LangGraph / AutoGen 编排',
  },
  {
    name: '智能模式配置',
    path: '/modules/aitest/config/mode',
    sidebarText: '智能模式配置',
    pageTitle: null,
    businessChecks: [
      { type: 'visible', selector: '.page-wrap, .el-form, .el-card, .el-switch' },
    ],
    industryLogic: '智能模式配置定义 AI 自主测试策略（高/低信心场景的人机协作模式）',
  },
]

const results = []

async function checkBusiness(page, checks) {
  const details = []
  for (const c of checks) {
    try {
      if (c.type === 'visible') {
        const loc = page.locator(c.selector).first()
        const ok = await loc.isVisible({ timeout: 5000 })
        details.push({ check: c.selector, pass: ok })
      } else if (c.type === 'text') {
        const texts = await page.locator(c.selector).allTextContents()
        const combined = texts.join(' ')
        const ok = c.expectAny.some((t) => combined.includes(t))
        details.push({ check: c.expectAny.join('|'), pass: ok, found: combined.slice(0, 200) })
      }
    } catch (e) {
      details.push({ check: c.selector || c.expectAny?.join('|'), pass: false, error: e.message })
    }
  }
  return details
}

async function main() {
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  const page = await context.newPage()

  const consoleErrors = []
  const networkErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('response', (resp) => {
    if (resp.url().includes('/api/') && resp.status() >= 400) {
      networkErrors.push({ url: resp.url(), status: resp.status() })
    }
  })

  // === 登录 ===
  let loginOk = false
  try {
    await page.goto(`${BASE}/login`, { waitUntil: 'networkidle', timeout: 30000 })
    await page.fill('input[placeholder*="用户名"], input[type="text"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button:has-text("登录"), button.el-button--primary')
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15000 })
    loginOk = true
    results.push({ step: '登录', pass: true, detail: `跳转至 ${page.url()}` })
  } catch (e) {
    results.push({ step: '登录', pass: false, detail: e.message })
    console.log(JSON.stringify({ results, summary: 'LOGIN_FAILED' }, null, 2))
    await browser.close()
    process.exit(1)
  }

  // === 首页进入 AI智能测试 ===
  try {
    await page.goto(`${BASE}/dashboard`, { waitUntil: 'networkidle' })
    const card = page.locator('.module-card, .card-item, [class*="module"]').filter({ hasText: 'AI智能测试' }).first()
    if (await card.isVisible({ timeout: 3000 }).catch(() => false)) {
      await card.click()
      await page.waitForLoadState('networkidle')
    } else {
      await page.goto(`${BASE}/modules/aitest/dashboard`, { waitUntil: 'networkidle' })
    }
    results.push({ step: '首页→AI智能测试', pass: page.url().includes('/modules/aitest'), detail: page.url() })
  } catch (e) {
    results.push({ step: '首页→AI智能测试', pass: false, detail: e.message })
  }

  // === 逐模块验证 ===
  for (const mod of MODULES) {
    const modResult = {
      module: mod.name,
      path: mod.path,
      industryLogic: mod.industryLogic,
      uiPass: false,
      businessPass: false,
      interactionPass: true,
      sidebarActive: false,
      pageTitleMatch: null,
      businessDetails: [],
      interactionDetails: null,
      consoleErrors: [],
      apiErrors: [],
      screenshot: null,
    }

    const errBefore = consoleErrors.length
    const netBefore = networkErrors.length

    try {
      // 点击侧边栏
      const sidebarItem = page.locator('.sidebar-menu a, .el-menu-item, .menu-item').filter({ hasText: mod.sidebarText }).first()
      if (await sidebarItem.isVisible({ timeout: 3000 }).catch(() => false)) {
        await sidebarItem.click()
      } else {
        await page.goto(`${BASE}${mod.path}`, { waitUntil: 'networkidle' })
      }
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(800)

      modResult.uiPass = page.url().includes(mod.path.split('?')[0])
      modResult.sidebarActive = await sidebarItem.evaluate((el) => el.classList.contains('active') || el.classList.contains('is-active')).catch(() => false)

      if (mod.pageTitle) {
        const titleEl = page.locator('h1.page-title, h2.page-title, .page-title').first()
        const titleText = await titleEl.textContent().catch(() => '')
        modResult.pageTitleMatch = titleText?.includes(mod.pageTitle.replace('AI ', '')) || titleText?.includes(mod.pageTitle)
      } else {
        modResult.pageTitleMatch = true
      }

      modResult.businessDetails = await checkBusiness(page, mod.businessChecks)
      modResult.businessPass = modResult.businessDetails.every((d) => d.pass)

      if (mod.interaction) {
        try {
          modResult.interactionDetails = await mod.interaction(page)
        } catch (e) {
          modResult.interactionPass = false
          modResult.interactionDetails = { error: e.message }
        }
      }

      const shotName = mod.name.replace(/\s/g, '_') + '.png'
      modResult.screenshot = shotName
      await page.screenshot({ path: join(SCREENSHOT_DIR, shotName), fullPage: true })
    } catch (e) {
      modResult.uiPass = false
      modResult.error = e.message
    }

    modResult.consoleErrors = consoleErrors.slice(errBefore)
    modResult.apiErrors = networkErrors.slice(netBefore)

    const overallPass =
      modResult.uiPass &&
      modResult.businessPass &&
      modResult.interactionPass &&
      (modResult.pageTitleMatch !== false) &&
      modResult.apiErrors.filter((e) => e.status >= 500).length === 0

    modResult.pass = overallPass
    results.push(modResult)
  }

  await browser.close()

  const passed = results.filter((r) => r.pass === true).length
  const failed = results.filter((r) => r.pass === false).length
  const summary = {
    total: results.length,
    passed,
    failed,
    passRate: `${Math.round((passed / results.length) * 100)}%`,
    timestamp: new Date().toISOString(),
  }

  const report = { summary, results }
  writeFileSync(join(SCREENSHOT_DIR, 'report.json'), JSON.stringify(report, null, 2))
  console.log(JSON.stringify(report, null, 2))
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})

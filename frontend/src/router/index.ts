import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

/**
 * 路由配置（重构后）
 *
 * 路由结构：
 *   /login                          -> 登录页（无 Layout 包裹）
 *   /register                       -> 注册页（无 Layout 包裹）
 *   /                               -> HomeLayout（无侧边栏）
 *     /home                         -> 首页仪表盘
 *   /modules                        -> ModuleLayout（有侧边栏）
 *     /modules/aitest/...           -> AI 智能测试模块（合并）
 *     /modules/configuration/...    -> 配置中心模块
 *     /modules/system-admin/...     -> 系统管理模块
 */

// ====== 布局组件（懒加载）======
const HomeLayout = () => import('@/components/layout/HomeLayout.vue')
const ModuleLayout = () => import('@/components/layout/ModuleLayout.vue')

// ====== 模块页面组件（懒加载）======
// AI 智能测试 - 合并（aitest）
const AITestDashboard = () => import('@/views/modules/aitest/dashboard/DashboardView.vue')
const AITestProjects = () => import('@/views/modules/aitest/project/ProjectListView.vue')
const AITestProjectDetail = () => import('@/views/modules/aitest/project/ProjectDetailView.vue')
// 项目管理的 AITestMembers 已合并到 ProjectDetailView 中
// 版本管理已整合到 ProjectDetailView Tab 中，不再需要独立路由
// const AITestVersions = () => import('@/views/modules/aitest/version/TestVersionList.vue')
const AITestCaseList = () => import('@/views/modules/aitest/testcase/TestCaseListView.vue')
const AITestCaseForm = () => import('@/views/modules/aitest/testcase/TestCaseFormView.vue')
const AITestCaseDetail = () => import('@/views/modules/aitest/testcase/TestCaseDetailView.vue')
const AITestReviews = () => import('@/views/modules/aitest/review/ReviewListView.vue')
const AITestReviewForm = () => import('@/views/modules/aitest/review/ReviewFormView.vue')
const AITestReviewDetail = () => import('@/views/modules/aitest/review/ReviewDetailView.vue')
const AITestCaseReview = () => import('@/views/modules/aitest/review/CaseReview.vue')
const AITestGenerate = () => import('@/views/modules/aitest/generation/GenerationView.vue')
const AITestGenRecords = () => import('@/views/modules/aitest/generation/GenerationRecordsView.vue')
const AITestTaskDetail = () => import('@/views/modules/aitest/generation/TaskDetailView.vue')
const AITestAiTester = () => import('@/views/modules/aitest/ai-tester/AITesterView.vue')
const AITestAiTesterConfig = () => import('@/views/modules/aitest/ai-tester/AITesterConfigView.vue')
const AITestReports = () => import('@/views/modules/aitest/report/TestReportView.vue')
const AITestConfigMode = () => import('@/views/modules/aitest/config/AIModeConfigView.vue')

// 系统管理
const UserManagement = () => import('@/views/modules/system/UserManagement.vue')
const RoleManagement = () => import('@/views/modules/system/RoleManagement.vue')
const SystemSettings = () => import('@/views/modules/system/SystemSettings.vue')
const AuditLog = () => import('@/views/modules/system/AuditLog.vue')

// 配置中心
const AIModelConfig = () => import('@/views/modules/configuration/AIModelConfig.vue')
const PromptConfig = () => import('@/views/modules/configuration/PromptConfig.vue')
const GenerationConfig = () => import('@/views/modules/configuration/GenerationConfig.vue')

// API 接口测试
const ApiDashboard = () => import('@/views/modules/api-testing/ApiDashboard.vue')
const ApiTestReport = () => import('@/views/modules/api-testing/ApiTestReport.vue')
const EnvironmentMgr = () => import('@/views/modules/api-testing/EnvironmentMgr.vue')
const ScheduleMgr = () => import('@/views/modules/api-testing/ScheduleMgr.vue')
const RequestHistory = () => import('@/views/modules/api-testing/RequestHistory.vue')
const NotificationList = () => import('@/views/modules/api-testing/NotificationList.vue')
const ApiProjectList = () => import('@/views/modules/api-testing/ApiProjectList.vue')
const ApiEndpointList = () => import('@/views/modules/api-testing/ApiEndpointList.vue')
const ApiAutoTest = () => import('@/views/modules/api-testing/ApiAutoTest.vue')

// 占位组件（预留模块）
const Placeholder = () => import('@/views/Placeholder.vue')

const routes: RouteRecordRaw[] = [
  // ====== 认证页（无布局）======
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Login.vue'), // 复用登录组件（含注册模式切换）
    meta: { requiresAuth: false },
  },

  // ====== 首页（HomeLayout - 无侧边栏）======
  {
    path: '/',
    component: HomeLayout,
    children: [
      {
        path: '',
        redirect: '/home',
      },
      {
        path: 'home',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Home.vue'),
        meta: {
          requiresAuth: true,
          title: '首页仪表盘',
          icon: 'HomeFilled',
        },
      },
    ],
  },

  // ====== 模块页（ModuleLayout - 有侧边栏）======
  {
    path: '/modules',
    component: ModuleLayout,
    children: [
      // ---- AI 智能测试（合并）----
      {
        path: 'aitest',
        redirect: '/modules/aitest/dashboard',
        meta: { module: 'aitest', requiresAuth: true, title: 'AI智能测试' },
        children: [
          // 数据看板
          { path: 'dashboard', name: 'AITestDashboard', component: AITestDashboard, meta: { module: 'aitest', requiresAuth: true, title: '测试总览' } },
          // 项目管理
          { path: 'projects', name: 'AITestProjects', component: AITestProjects, meta: { module: 'aitest', requiresAuth: true, title: '项目列表' } },
          { path: 'projects/:id', name: 'AITestProjectDetail', component: AITestProjectDetail, meta: { module: 'aitest', requiresAuth: true, title: '项目详情' } },
          // 用例管理
          { path: 'testcases', name: 'AITestCaseList', component: AITestCaseList, meta: { module: 'aitest', requiresAuth: true, title: '用例列表' } },
          { path: 'testcases/create', name: 'AITestCaseCreate', component: AITestCaseForm, meta: { module: 'aitest', requiresAuth: true, title: '新建用例' } },
          { path: 'testcases/:id', name: 'AITestCaseDetail', component: AITestCaseDetail, meta: { module: 'aitest', requiresAuth: true, title: '用例详情' } },
          { path: 'testcases/:id/edit', name: 'AITestCaseEdit', component: AITestCaseForm, meta: { module: 'aitest', requiresAuth: true, title: '编辑用例' } },
          // 用例评审
          { path: 'reviews', name: 'AITestReviews', component: AITestReviews, meta: { module: 'aitest', requiresAuth: true, title: '评审列表' } },
          { path: 'reviews/create', name: 'AITestReviewCreate', component: AITestReviewForm, meta: { module: 'aitest', requiresAuth: true, title: '新建评审' } },
          { path: 'reviews/:id', name: 'AITestReviewDetail', component: AITestReviewDetail, meta: { module: 'aitest', requiresAuth: true, title: '评审详情' } },
          { path: 'review-cases', name: 'AITestCaseReview', component: AITestCaseReview, meta: { module: 'aitest', requiresAuth: true, title: '用例评审' } },
          // AI 用例生成
          { path: 'generate', name: 'AITestGenerate', component: AITestGenerate, meta: { module: 'aitest', requiresAuth: true, title: 'AI用例生成' } },
          { path: 'generate/records', name: 'AITestGenRecords', component: AITestGenRecords, meta: { module: 'aitest', requiresAuth: true, title: 'AI生成记录' } },
          { path: 'generate/tasks/:id', name: 'AITestTaskDetail', component: AITestTaskDetail, meta: { module: 'aitest', requiresAuth: true, title: '生成任务详情' } },
          // AI 评测师
          { path: 'ai-tester', name: 'AITestAiTester', component: AITestAiTester, meta: { module: 'aitest', requiresAuth: true, title: 'AI评测师' } },
          { path: 'ai-tester/config', name: 'AITestAiTesterConfig', component: AITestAiTesterConfig, meta: { module: 'aitest', requiresAuth: true, title: '评测师配置' } },
          // 测试报告
          { path: 'reports', name: 'AITestReports', component: AITestReports, meta: { module: 'aitest', requiresAuth: true, title: '测试报告' } },
          // AI 配置
          { path: 'config', redirect: '/modules/aitest/config/model', meta: { module: 'aitest', requiresAuth: true, title: 'AI配置' } },
          { path: 'config/model', name: 'AITestConfigModel', component: AIModelConfig, meta: { module: 'aitest', requiresAuth: true, title: 'AI模型配置' } },
          { path: 'config/prompt', name: 'AITestConfigPrompt', component: PromptConfig, meta: { module: 'aitest', requiresAuth: true, title: 'AI提示词配置' } },
          { path: 'config/generation', name: 'AITestConfigGeneration', component: GenerationConfig, meta: { module: 'aitest', requiresAuth: true, title: '生成行为配置' } },
          { path: 'config/mode', name: 'AITestConfigMode', component: AITestConfigMode, meta: { module: 'aitest', requiresAuth: true, title: '智能模式配置' } },
        ],
      },

      // ---- API 接口测试 ----
      {
        path: 'api-testing',
        redirect: '/modules/api-testing/dashboard',
        meta: { module: 'api-testing', requiresAuth: true, title: 'API接口测试' },
        children: [
          {
            path: 'dashboard',
            name: 'ApiDashboard',
            component: ApiDashboard,
            meta: { module: 'api-testing', requiresAuth: true, title: '数据看板' },
          },
          {
            path: 'projects',
            name: 'ApiProjectList',
            component: ApiProjectList,
            meta: { module: 'api-testing', requiresAuth: true, title: '项目管理' },
          },
          {
            path: 'projects/:id/endpoints',
            name: 'ApiEndpointList',
            component: ApiEndpointList,
            meta: { module: 'api-testing', requiresAuth: true, title: '接口管理' },
          },
          {
            path: 'auto-test',
            name: 'ApiAutoTest',
            component: ApiAutoTest,
            meta: { module: 'api-testing', requiresAuth: true, title: '自动化测试' },
          },
          {
            path: 'reports',
            name: 'ApiTestReport',
            component: ApiTestReport,
            meta: { module: 'api-testing', requiresAuth: true, title: '测试报告' },
          },
          {
            path: 'environments',
            name: 'EnvironmentMgr',
            component: EnvironmentMgr,
            meta: { module: 'api-testing', requiresAuth: true, title: '环境管理' },
          },
          {
            path: 'schedules',
            name: 'ScheduleMgr',
            component: ScheduleMgr,
            meta: { module: 'api-testing', requiresAuth: true, title: '定时任务' },
          },
          {
            path: 'history',
            name: 'RequestHistory',
            component: RequestHistory,
            meta: { module: 'api-testing', requiresAuth: true, title: '请求历史' },
          },
          {
            path: 'notifications',
            name: 'NotificationList',
            component: NotificationList,
            meta: { module: 'api-testing', requiresAuth: true, title: '通知列表' },
          },
        ],
      },

      // ---- UI 自动化测试（预留）----
      {
        path: 'ui-automation',
        name: 'UiAutomation',
        component: Placeholder,
        meta: { module: 'ui-automation', requiresAuth: true, title: 'UI自动化测试' },
      },

      // ---- APP 自动化测试（预留）----
      {
        path: 'app-automation',
        name: 'AppAutomation',
        component: Placeholder,
        meta: { module: 'app-automation', requiresAuth: true, title: 'APP自动化测试' },
      },


      // ---- 配置中心 ----
      {
        path: 'configuration',
        redirect: '/modules/configuration/ai-models',
        meta: { module: 'configuration', requiresAuth: true, title: '配置中心' },
        children: [
          {
            path: 'ai-models',
            name: 'AIModelConfig',
            component: AIModelConfig,
            meta: { module: 'configuration', requiresAuth: true, title: 'AI模型配置' },
          },
          {
            path: 'prompts',
            name: 'PromptConfig',
            component: PromptConfig,
            meta: { module: 'configuration', requiresAuth: true, title: '提示词配置' },
          },
          {
            path: 'generation',
            name: 'GenerationConfig',
            component: GenerationConfig,
            meta: { module: 'configuration', requiresAuth: true, title: '生成行为配置' },
          },
        ],
      },

      // ---- AI 聊天室 ----
      {
        path: 'ai-chat',
        name: 'AiChat',
        component: () => import('@/views/modules/ai-chat/ChatView.vue'),
        meta: { module: 'ai-chat', requiresAuth: true, title: 'AI聊天室' },
      },

      // ---- 知识库 ----
      {
        path: 'knowledge-base',
        name: 'KnowledgeBase',
        component: () => import('@/views/modules/knowledge-base/KnowledgeBaseView.vue'),
        meta: { module: 'knowledge-base', requiresAuth: true, title: '知识库' },
      },

      // ---- 系统管理 ----
      {
        path: 'system-admin',
        redirect: '/modules/system-admin/users',
        meta: { module: 'system-admin', requiresAuth: true, title: '系统管理' },
        children: [
          {
            path: 'users',
            name: 'AdminUsers',
            component: UserManagement,
            meta: { module: 'system-admin', requiresAuth: true, title: '用户管理' },
          },
          {
            path: 'roles',
            name: 'AdminRoles',
            component: RoleManagement,
            meta: { module: 'system-admin', requiresAuth: true, title: '角色权限' },
          },
          {
            path: 'settings',
            name: 'AdminSettings',
            component: SystemSettings,
            meta: { module: 'system-admin', requiresAuth: true, title: '系统设置' },
          },
          {
            path: 'audit-logs',
            name: 'AdminAuditLogs',
            component: AuditLog,
            meta: { module: 'system-admin', requiresAuth: true, title: '审计日志' },
          },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 全局导航守卫 —— 校验登录状态
 *
 * - 需要登录但无 token 时，重定向到 /login
 * - 已登录访问 /login 或 /register 时，重定向到 /home
 */
router.beforeEach((to, _from, next) => {
  const hasToken = !!localStorage.getItem('access_token')

  // 需要登录但无 token，重定向到登录页
  if (to.meta.requiresAuth && !hasToken) {
    next({ name: 'Login' })
    return
  }

  // 已登录且访问登录/注册页，重定向到首页
  if ((to.name === 'Login' || to.name === 'Register') && hasToken) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router

/**
 * 移动端路由配置
 * 独立于桌面端路由，路径使用 /m/ 前缀
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ====== 登录 ======
    {
      path: '/m/login',
      name: 'm-login',
      component: () => import('../views/auth/Login.vue'),
      meta: { requiresAuth: false },
    },

    // ====== 主布局（带 TabBar） ======
    {
      path: '/m',
      component: () => import('../components/layout/MobileLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        // 首页仪表盘
        {
          path: 'home',
          name: 'm-home',
          component: () => import('../views/dashboard/Home.vue'),
          meta: { title: '首页', icon: 'home-o' },
        },

        // AI 聊天室
        {
          path: 'ai-chat',
          name: 'm-ai-chat',
          component: () => import('../views/modules/ai-chat/ChatView.vue'),
          meta: { title: 'AI 聊天', icon: 'chat-o' },
        },

        // 测试模块入口（展开子模块）
        {
          path: 'aitest',
          name: 'm-aitest',
          component: () => import('../views/modules/aitest/dashboard/DashboardView.vue'),
          meta: { title: '测试', icon: 'label-o', module: 'aitest' },
        },
        {
          path: 'aitest/projects',
          name: 'm-aitest-projects',
          component: () => import('../views/modules/aitest/project/ProjectListView.vue'),
          meta: { title: '项目管理', module: 'aitest' },
        },
        {
          path: 'aitest/projects/:id',
          name: 'm-aitest-project-detail',
          component: () => import('../views/modules/aitest/project/ProjectDetailView.vue'),
          meta: { title: '项目详情', module: 'aitest' },
        },
        {
          path: 'aitest/testcases',
          name: 'm-aitest-testcases',
          component: () => import('../views/modules/aitest/testcase/TestCaseListView.vue'),
          meta: { title: '用例管理', module: 'aitest' },
        },
        {
          path: 'aitest/testcases/create',
          name: 'm-aitest-testcase-create',
          component: () => import('../views/modules/aitest/testcase/TestCaseFormView.vue'),
          meta: { title: '新建用例', module: 'aitest' },
        },
        {
          path: 'aitest/testcases/:id',
          name: 'm-aitest-testcase-detail',
          component: () => import('../views/modules/aitest/testcase/TestCaseDetailView.vue'),
          meta: { title: '用例详情', module: 'aitest' },
        },
        {
          path: 'aitest/testcases/:id/edit',
          name: 'm-aitest-testcase-edit',
          component: () => import('../views/modules/aitest/testcase/TestCaseFormView.vue'),
          meta: { title: '编辑用例', module: 'aitest' },
        },
        {
          path: 'aitest/reviews',
          name: 'm-aitest-reviews',
          component: () => import('../views/modules/aitest/review/ReviewListView.vue'),
          meta: { title: '评审管理', module: 'aitest' },
        },
        {
          path: 'aitest/reviews/create',
          name: 'm-aitest-review-create',
          component: () => import('../views/modules/aitest/review/ReviewFormView.vue'),
          meta: { title: '新建评审', module: 'aitest' },
        },
        {
          path: 'aitest/reviews/:id',
          name: 'm-aitest-review-detail',
          component: () => import('../views/modules/aitest/review/ReviewDetailView.vue'),
          meta: { title: '评审详情', module: 'aitest' },
        },
        {
          path: 'aitest/review-cases',
          name: 'm-aitest-review-cases',
          component: () => import('../views/modules/aitest/review/CaseReview.vue'),
          meta: { title: '用例评审', module: 'aitest' },
        },
        {
          path: 'aitest/generate',
          name: 'm-aitest-generate',
          component: () => import('../views/modules/aitest/generation/GenerationView.vue'),
          meta: { title: 'AI 用例生成', module: 'aitest' },
        },
        {
          path: 'aitest/generate/records',
          name: 'm-aitest-generate-records',
          component: () => import('../views/modules/aitest/generation/GenerationRecordsView.vue'),
          meta: { title: '生成记录', module: 'aitest' },
        },
        {
          path: 'aitest/generate/tasks/:id',
          name: 'm-aitest-task-detail',
          component: () => import('../views/modules/aitest/generation/TaskDetailView.vue'),
          meta: { title: '任务详情', module: 'aitest' },
        },
        {
          path: 'aitest/ai-tester',
          name: 'm-aitest-ai-tester',
          component: () => import('../views/modules/aitest/ai-tester/AITesterView.vue'),
          meta: { title: 'AI 评测师', module: 'aitest' },
        },
        {
          path: 'aitest/ai-tester/config',
          name: 'm-aitest-ai-tester-config',
          component: () => import('../views/modules/aitest/ai-tester/AITesterConfigView.vue'),
          meta: { title: '评测师配置', module: 'aitest' },
        },
        {
          path: 'aitest/reports',
          name: 'm-aitest-reports',
          component: () => import('../views/modules/aitest/report/TestReportView.vue'),
          meta: { title: '测试报告', module: 'aitest' },
        },

        // API 接口测试
        {
          path: 'api-testing',
          name: 'm-api-testing',
          component: () => import('../views/modules/api-testing/ApiDashboard.vue'),
          meta: { title: 'API 测试', icon: 'wap-o' },
        },

        // 知识库
        {
          path: 'knowledge-base',
          name: 'm-knowledge-base',
          component: () => import('../views/modules/knowledge-base/KnowledgeBaseView.vue'),
          meta: { title: '知识库', icon: 'records-o' },
        },

        // 我的（系统管理/配置）
        {
          path: 'profile',
          name: 'm-profile',
          component: () => import('../views/modules/system/UserManagement.vue'),
          meta: { title: '我的', icon: 'user-o' },
        },
      ],
    },

    // 默认跳转
    {
      path: '/',
      redirect: () => {
        const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
          || window.innerWidth < 768
        return isMobile ? '/m/home' : '/home'
      },
    },

    // 未匹配路由
    {
      path: '/:pathMatch(.*)*',
      redirect: '/m/home',
    },
  ],
})

// 全局前置守卫
router.beforeEach((to, _from, next) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth !== false)
  const token = localStorage.getItem('access_token')

  if (requiresAuth && !token) {
    next({ name: 'm-login' })
  } else {
    next()
  }
})

export default router

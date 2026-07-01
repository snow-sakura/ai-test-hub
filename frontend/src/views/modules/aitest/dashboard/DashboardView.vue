<template>
  <div class="page-wrap">
    <h1 class="page-title">测试总览</h1>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(198,123,92,0.1);color:#C67B5C">
          <el-icon :size="22"><FolderOpened /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.project_count }}</div>
          <div class="stat-label">项目总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(16,185,129,0.1);color:#10b981">
          <el-icon :size="22"><Document /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.case_count }}</div>
          <div class="stat-label">用例总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(59,130,246,0.1);color:#3b82f6">
          <el-icon :size="22"><UserFilled /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.member_count }}</div>
          <div class="stat-label">成员总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(245,158,11,0.1);color:#f59e0b">
          <el-icon :size="22"><Edit /></el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.review_count }}</div>
          <div class="stat-label">待评审</div>
        </div>
      </div>
    </div>

    <!-- 中间行：图表 + 活动 -->
    <div class="mid-row">
      <!-- SVG 折线趋势图 -->
      <div class="chart-card">
        <h3 class="card-title">用例趋势（近 7 天）</h3>
        <div class="chart-wrap">
          <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="trend-svg">
            <!-- 网格线 -->
            <line v-for="(y, i) in gridLines" :key="'g'+i" :x1="0" :y1="y" :x2="svgW" :y2="y" stroke="rgba(180,150,120,0.1)" stroke-width="1" />
            <!-- Y 轴标签 -->
            <text v-for="(y, i) in gridLines" :key="'yl'+i" x="-8" :y="y + 4" fill="#8B7355" font-size="10" text-anchor="end">{{ gridLabels[i] }}</text>
            <!-- X 轴标签 -->
            <text v-for="(d, i) in trendDays" :key="'xl'+i" :x="trendX(i)" :y="svgH - 4" fill="#8B7355" font-size="10" text-anchor="middle">{{ d }}</text>
            <!-- 渐变填充 -->
            <defs>
              <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#C67B5C" stop-opacity="0.25" />
                <stop offset="100%" stop-color="#C67B5C" stop-opacity="0.02" />
              </linearGradient>
            </defs>
            <!-- 面积 -->
            <path :d="areaPath" fill="url(#trendGrad)" />
            <!-- 折线 -->
            <path :d="linePath" fill="none" stroke="#C67B5C" stroke-width="2" stroke-linejoin="round" />
            <!-- 数据圆点 -->
            <circle v-for="(pt, i) in trendPoints" :key="'p'+i" :cx="pt.x" :cy="pt.y" r="3" fill="#C67B5C" stroke="#fff" stroke-width="1.5">
              <title>{{ pt.value }}</title>
            </circle>
          </svg>
        </div>
      </div>

      <!-- 优先级饼图 -->
      <div class="chart-card" style="flex:1">
        <h3 class="card-title">用例优先级分布</h3>
        <div class="pie-wrap">
          <div class="pie-visual" :style="{ background: pieBg }"></div>
          <div class="pie-legend">
            <div v-for="(item, idx) in priorityData" :key="idx" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-label">{{ item.label }}</span>
              <span class="legend-value">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速入口 + 最近活动 -->
    <div class="bottom-row">
      <!-- 快速入口 -->
      <div class="quick-entries">
        <h3 class="card-title">快速入口</h3>
        <div class="entry-grid">
          <div v-for="entry in entries" :key="entry.path" class="entry-card" @click="goTo(entry.path)">
            <el-icon :size="28" :color="entry.color"><component :is="entry.icon" /></el-icon>
            <span class="entry-title">{{ entry.title }}</span>
            <span class="entry-desc">{{ entry.desc }}</span>
          </div>
        </div>
      </div>

      <!-- 最近活动 -->
      <div class="activity-timeline">
        <h3 class="card-title">最近活动</h3>
        <div v-if="activities.length === 0" class="empty-timeline">暂无活动</div>
        <div v-else class="timeline">
          <div v-for="(act, idx) in activities" :key="idx" class="timeline-item">
            <div class="timeline-dot" :style="{ background: act.color || '#C67B5C' }"></div>
            <div class="timeline-content">
              <div class="timeline-text">{{ act.text }}</div>
              <div class="timeline-time">{{ act.time }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { FolderOpened, Document, UserFilled, Edit, Folder, MagicStick } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'

const router = useRouter()

const stats = reactive({
  project_count: 0, version_count: 0, case_count: 0, member_count: 0, review_count: 0,
  task_count: 0, completed_task_count: 0,
})

// SVG 趋势图
const svgW = 280
const svgH = 160
const pad = { top: 16, right: 8, bottom: 28, left: 36 }
const plotW = svgW - pad.left - pad.right
const plotH = svgH - pad.top - pad.bottom

const trendDays = ref<string[]>([])
const trendValues = ref<number[]>([])

// 后端 case_by_priority 真实数据
const rawPriority = ref<Record<string, number>>({})

// 后端 recent_activities 原始数据
const rawActivities = ref<any[]>([])

const maxVal = computed(() => {
  const max = Math.max(...trendValues.value, 0)
  return max === 0 ? 1 : max
})
const gridLines = computed(() => {
  const lines = []
  for (let i = 0; i <= 4; i++) {
    lines.push(pad.top + (plotH * (1 - i / 4)))
  }
  return lines
})
const gridLabels = computed(() => {
  return [0, 1, 2, 3, 4].map(i => Math.round(maxVal.value * i / 4))
})

function trendX(i: number) {
  const len = trendDays.value.length
  if (len <= 1) return pad.left
  return pad.left + (plotW * i / (len - 1))
}
function trendY(val: number) {
  return pad.top + plotH * (1 - val / maxVal.value)
}

const trendPoints = computed(() =>
  trendValues.value.map((v, i) => ({ x: trendX(i), y: trendY(v), value: v }))
)

const linePath = computed(() => {
  return trendPoints.value.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
})

const areaPath = computed(() => {
  if (trendPoints.value.length === 0) return ''
  const pts = trendPoints.value
  const bottom = pad.top + plotH
  return `M${pts[0].x},${bottom} ${pts.map(p => `L${p.x},${p.y}`).join(' ')} L${pts[pts.length - 1].x},${bottom} Z`
})

// 优先级饼图（使用后端真实数据）
const priorityData = computed(() => {
  const p = rawPriority.value
  const total = Object.values(p).reduce((a, b) => a + b, 0) || 1
  const entries = [
    { key: 'p0', label: 'P0 紧急', color: '#dc2626' },
    { key: 'p1', label: 'P1 高', color: '#ea580c' },
    { key: 'p2', label: 'P2 中', color: '#2563eb' },
    { key: 'p3', label: 'P3 低', color: '#7A6855' },
  ]
  return entries.map(e => ({
    label: e.label,
    value: p[e.key] || 0,
    color: e.color,
    pct: (p[e.key] || 0) / total,
  }))
})

const pieBg = computed(() => {
  const parts = priorityData.value.filter(p => p.value > 0)
  if (parts.length === 0) return '#F0EBE3'
  // Sort by percentage descending for better visual
  parts.sort((a, b) => b.pct - a.pct)
  let startPct = 0
  const stops = parts.map((p) => {
    const start = Math.round(startPct * 100)
    const end = Math.round((startPct + p.pct) * 100)
    startPct += p.pct
    return `${p.color} ${start}% ${end}%`
  })
  return `conic-gradient(${stops.join(', ')})`
})

// 快速入口
const entries = [
  { title: '项目列表', desc: '查看和管理项目', path: '/modules/aitest/projects', icon: Folder, color: '#C67B5C' },
  { title: '测试用例', desc: '管理测试用例', path: '/modules/aitest/testcases', icon: Document, color: '#10b981' },
  { title: '用例评审', desc: '评审测试用例', path: '/modules/aitest/reviews', icon: Edit, color: '#f59e0b' },
  { title: 'AI 生成', desc: 'AI 自动生成用例', path: '/modules/aitest/generate', icon: MagicStick, color: '#3b82f6' },
]

// 最近活动
const activities = ref<Array<{ text: string; time: string; color?: string }>>([])

async function loadStats() {
  try {
    const res = await aitestApi.getDashboardStats()
    const d = res.data
    if (!d) return

    // 基础统计
    stats.project_count = d.project_count || 0
    stats.case_count = d.case_count || 0
    stats.review_count = d.review_count || 0
    stats.member_count = d.member_count || 0
    stats.version_count = d.version_count || 0
    stats.task_count = d.task_count || 0
    stats.completed_task_count = d.completed_task_count || 0

    // 优先级分布（真实数据）
    rawPriority.value = d.case_by_priority || {}

    // 趋势图：从 recent_activities 推算近 7 天每日新增
    const acts = d.recent_activities || []
    rawActivities.value = acts
    buildTrendFromActivities(acts)
    buildTimeline(acts)
  } catch {
    ElMessage.error('加载仪表盘数据失败')
  }
}

/** 从活动记录推算近 7 天趋势 */
function buildTrendFromActivities(acts: any[]) {
  const now = new Date()
  const days: string[] = []
  const counts: number[] = []
  // 统计每天的 activity 数量
  const dayMap: Record<string, number> = {}
  for (const a of acts) {
    if (!a.created_at) continue
    const d = new Date(a.created_at)
    const key = `${d.getMonth() + 1}/${d.getDate()}`
    dayMap[key] = (dayMap[key] || 0) + 1
  }
  // 生成近 7 天
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    const key = `${d.getMonth() + 1}/${d.getDate()}`
    days.push(key)
    counts.push(dayMap[key] || 0)
  }
  trendDays.value = days
  trendValues.value = counts
}

/** 构建活动时间线 */
function buildTimeline(acts: any[]) {
  const now = new Date()
  const colors: Record<string, string> = {
    project: '#C67B5C', case: '#10b981', review: '#f59e0b', task: '#3b82f6',
  }
  activities.value = acts.slice(0, 8).map((a: any) => ({
    text: a.action || `${a.entity_type} #${a.entity_id}`,
    time: a.created_at ? formatRelativeTime(a.created_at, now) : '',
    color: colors[a.entity_type] || '#C67B5C',
  }))
}

function formatRelativeTime(isoStr: string, now: Date): string {
  const d = new Date(isoStr)
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} 小时前`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 7) return `${diffDay} 天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function goTo(path: string) { router.push(path) }

onMounted(loadStats)
</script>

<style scoped>
.page-wrap { padding: 24px 16px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); margin: 0 0 24px; letter-spacing: -0.02em; }

/* 统计卡片 */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card {
  padding: 20px 24px; text-align: center;
  background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12));
  border-radius: 12px; transition: box-shadow 0.2s;
}
.stat-card:hover { box-shadow: 0 4px 16px rgba(180,150,120,0.1); }
.stat-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  margin: 0 auto 8px;
}
.stat-body { }
.stat-value { font-size: 28px; font-weight: 700; color: var(--text, #3D2E1F); line-height: 1.2; }
.stat-label { font-size: 13px; color: var(--text-muted, #8B7355); margin-top: 2px; }

/* 中间行 */
.mid-row { display: flex; gap: 16px; margin-bottom: 20px; }
.chart-card { flex: 2; padding: 20px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; }
.card-title { font-size: 15px; font-weight: 600; color: var(--text, #3D2E1F); margin: 0 0 12px; }
.chart-wrap { width: 100%; }
.trend-svg { width: 100%; height: 160px; }

/* 饼图 */
.pie-wrap { display: flex; align-items: center; gap: 24px; }
.pie-visual { width: 120px; height: 120px; border-radius: 50%; flex-shrink: 0; }
.pie-legend { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-label { color: var(--text-secondary, #5C4A38); flex: 1; }
.legend-value { font-weight: 600; color: var(--text, #3D2E1F); }

/* 底部行 */
.bottom-row { display: flex; gap: 16px; }
.quick-entries { flex: 2; padding: 20px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; }
.entry-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.entry-card {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 20px 12px; border-radius: 10px; cursor: pointer;
  border: 1px solid transparent; transition: all 0.2s;
}
.entry-card:hover { border-color: rgba(198,123,92,0.2); background: rgba(198,123,92,0.04); }
.entry-title { font-size: 13px; font-weight: 600; color: var(--text, #3D2E1F); }
.entry-desc { font-size: 11px; color: var(--text-muted, #8B7355); }

/* 活动时间线 */
.activity-timeline { flex: 1.5; padding: 20px; background: var(--card-bg, #FFFDF9); border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; }
.empty-timeline { font-size: 13px; color: var(--text-muted, #8B7355); padding: 24px 0; text-align: center; }
.timeline { display: flex; flex-direction: column; gap: 12px; }
.timeline-item { display: flex; gap: 10px; position: relative; padding-left: 12px; }
.timeline-item::before {
  content: ''; position: absolute; left: 15px; top: 20px; bottom: -12px;
  width: 1px; background: rgba(180,150,120,0.15);
}
.timeline-item:last-child::before { display: none; }
.timeline-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.timeline-content { flex: 1; }
.timeline-text { font-size: 13px; color: var(--text, #3D2E1F); line-height: 1.4; }
.timeline-time { font-size: 11px; color: var(--text-muted, #8B7355); margin-top: 2px; }

@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .mid-row { flex-direction: column; }
  .bottom-row { flex-direction: column; }
}
</style>

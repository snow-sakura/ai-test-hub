<template>
  <div class="api-auto-test">
    <!-- 页面标题 -->
    <div class="page-title">
      <h2>API 自动化测试</h2>
      <span class="page-desc">创建和执行 API 测试套件</span>
    </div>

    <!-- 左右分栏布局 -->
    <div class="split-layout">
      <!-- 左侧：项目选择 + 套件列表 -->
      <div class="left-panel">
        <div class="panel-section">
          <h3 class="panel-title">选择项目</h3>
          <el-select
            v-model="selectedProjectId"
            placeholder="请选择项目"
            style="width: 100%"
            @change="onProjectChange"
          >
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </div>

        <div class="panel-section">
          <div class="section-header">
            <h3 class="panel-title">测试套件</h3>
            <el-button size="small" type="primary" :disabled="!selectedProjectId" @click="openCreateSuite">
              <el-icon><Plus /></el-icon>
              新建
            </el-button>
          </div>

          <div v-if="loadingSuites" class="loading-wrap">
            <el-skeleton :rows="4" animated />
          </div>

          <div v-else-if="suites.length === 0" class="empty-tip">
            暂无测试套件
          </div>

          <div v-else class="suite-list">
            <div
              v-for="suite in suites"
              :key="suite.id"
              class="suite-item"
              :class="{ active: selectedSuiteId === suite.id }"
              @click="selectSuite(suite)"
            >
              <div class="suite-info">
                <span class="suite-name">{{ suite.name }}</span>
                <el-tag
                  :type="statusTagType(suite.status)"
                  size="small"
                  effect="plain"
                >
                  {{ statusLabel(suite.status) }}
                </el-tag>
              </div>
              <div class="suite-actions">
                <el-button text size="small" @click.stop="openEditSuite(suite)">编辑</el-button>
                <el-button text size="small" type="danger" @click.stop="confirmDeleteSuite(suite)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：配置区 + 执行结果 -->
      <div class="right-panel">
        <template v-if="selectedSuite">
          <!-- 3 个 Tab：基本信息 / 接口选择 / 断言配置 -->
          <el-tabs v-model="activeTab" type="border-card">
            <el-tab-pane label="基本信息" name="basic">
              <el-form label-width="100px">
                <el-form-item label="套件名称">
                  <el-input v-model="suiteForm.name" placeholder="请输入套件名称" />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input
                    v-model="suiteForm.description"
                    type="textarea"
                    :rows="3"
                    placeholder="套件描述（可选）"
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="接口选择" name="endpoints">
              <div class="endpoint-select-area">
                <p class="section-tip">从当前项目中拖拽选择要测试的接口</p>

                <!-- 级联选择器：项目→接口 -->
                <div class="cascader-row">
                  <el-select
                    v-model="endpointToAdd"
                    placeholder="选择接口添加"
                    filterable
                    style="width: 100%"
                    @change="addEndpointToSuite"
                  >
                    <el-option
                      v-for="ep in availableEndpoints"
                      :key="ep.id"
                      :label="`[${ep.method}] ${ep.path} - ${ep.name}`"
                      :value="ep.id"
                    >
                      <span style="float: left">
                        <el-tag :color="METHOD_COLORS[ep.method]" size="small" effect="dark" style="margin-right: 6px">
                          {{ ep.method }}
                        </el-tag>
                        {{ ep.path }}
                      </span>
                      <span style="float: right; color: #909399; font-size: 12px">{{ ep.name }}</span>
                    </el-option>
                  </el-select>
                </div>

                <!-- 已选接口列表（拖拽排序） -->
                <div class="selected-endpoints">
                  <div
                    v-for="(ep, idx) in suiteEndpoints"
                    :key="ep.endpoint_id"
                    class="selected-endpoint"
                    draggable="true"
                    @dragstart="onDragStart(idx)"
                    @dragover.prevent="onDragOver(idx)"
                    @drop="onDrop(idx)"
                  >
                    <span class="drag-handle">
                      <el-icon><Rank /></el-icon>
                    </span>
                    <el-tag
                      :color="METHOD_COLORS[ep.method || 'GET'] || '#909399'"
                      size="small"
                      effect="dark"
                      class="method-badge"
                    >
                      {{ ep.method }}
                    </el-tag>
                    <span class="ep-path">{{ ep.path }}</span>
                    <span class="ep-name">{{ ep.name }}</span>
                    <div class="ep-actions">
                      <el-popover placement="left" :width="300" trigger="click">
                        <template #reference>
                          <el-button text size="small">
                            <el-icon><Setting /></el-icon>
                          </el-button>
                        </template>
                        <div class="var-override-form">
                          <h4 style="margin: 0 0 8px 0">变量覆盖</h4>
                          <div v-for="(_, key) in ep.variable_overrides" :key="key" class="var-row">
                            <el-tag size="small">{{ key }}</el-tag>
                            <el-input v-model="ep.variable_overrides![key]" size="small" />
                          </div>
                          <div v-if="!ep.variable_overrides || Object.keys(ep.variable_overrides).length === 0" class="empty-var">
                            暂无变量覆盖
                          </div>
                        </div>
                      </el-popover>
                      <el-button text size="small" type="danger" @click="removeEndpointFromSuite(idx)">移除</el-button>
                    </div>
                  </div>
                  <el-empty v-if="suiteEndpoints.length === 0" description="尚未选择接口" :image-size="80" />
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="断言配置" name="assertions">
              <div class="assertion-area">
                <div class="assertion-logic">
                  <span>断言逻辑：</span>
                  <el-radio-group v-model="assertionLogic" size="small">
                    <el-radio value="and">全部通过（AND）</el-radio>
                    <el-radio value="or">任一通过（OR）</el-radio>
                  </el-radio-group>
                </div>

                <div class="assertion-rules">
                  <div
                    v-for="(rule, idx) in assertionRules"
                    :key="idx"
                    class="assertion-rule"
                  >
                    <el-row :gutter="8" align="middle">
                      <el-col :span="5">
                        <el-select v-model="rule.type" size="small" style="width: 100%" @change="resetAssertionRule(rule)">
                          <el-option
                            v-for="opt in ASSERTION_TYPE_OPTIONS"
                            :key="opt.value"
                            :label="opt.label"
                            :value="opt.value"
                          />
                        </el-select>
                      </el-col>

                      <!-- 状态码规则 -->
                      <template v-if="rule.type === 'status_code'">
                        <el-col :span="5">
                          <el-select v-model="rule.operator" size="small" style="width: 100%">
                            <el-option label="等于" value="eq" />
                            <el-option label="不等于" value="ne" />
                          </el-select>
                        </el-col>
                        <el-col :span="5">
                          <el-input-number v-model="rule.expected" :min="100" :max="599" size="small" style="width: 100%" />
                        </el-col>
                      </template>

                      <!-- 响应头规则 -->
                      <template v-else-if="rule.type === 'response_header'">
                        <el-col :span="4">
                          <el-input v-model="rule.header" size="small" placeholder="响应头名" />
                        </el-col>
                        <el-col :span="4">
                          <el-select v-model="rule.operator" size="small" style="width: 100%">
                            <el-option label="等于" value="eq" />
                            <el-option label="包含" value="contains" />
                            <el-option label="存在" value="exists" />
                          </el-select>
                        </el-col>
                        <el-col :span="5">
                          <el-input
                            v-if="rule.operator !== 'exists'"
                            v-model="rule.expected"
                            size="small"
                            placeholder="预期值"
                          />
                        </el-col>
                      </template>

                      <!-- JSON Path 规则 -->
                      <template v-else-if="rule.type === 'json_path'">
                        <el-col :span="4">
                          <el-input v-model="rule.jsonPath" size="small" placeholder="data.id" />
                        </el-col>
                        <el-col :span="4">
                          <el-select v-model="rule.operator" size="small" style="width: 100%">
                            <el-option label="等于" value="eq" />
                            <el-option label="不等于" value="ne" />
                            <el-option label="包含" value="contains" />
                            <el-option label="存在" value="exists" />
                          </el-select>
                        </el-col>
                        <el-col :span="5">
                          <el-input
                            v-if="rule.operator !== 'exists'"
                            v-model="rule.expected"
                            size="small"
                            placeholder="预期值"
                          />
                        </el-col>
                      </template>

                      <!-- 响应时间规则 -->
                      <template v-else-if="rule.type === 'response_time'">
                        <el-col :span="5">
                          <span class="time-label">不超过</span>
                        </el-col>
                        <el-col :span="5">
                          <el-input-number v-model="rule.maxMs" :min="100" :step="500" size="small" style="width: 100%" />
                        </el-col>
                        <el-col :span="3">
                          <span class="time-label">ms</span>
                        </el-col>
                      </template>

                      <el-col :span="2">
                        <el-button text size="small" type="danger" @click="assertionRules.splice(idx, 1)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </el-col>
                    </el-row>
                  </div>
                </div>

                <el-button size="small" style="margin-top: 8px" @click="addAssertionRule">
                  <el-icon><Plus /></el-icon>
                  添加断言
                </el-button>
              </div>
            </el-tab-pane>
          </el-tabs>

          <!-- 操作栏 -->
          <div class="action-bar">
            <el-button type="primary" @click="saveSuiteConfig">
              <el-icon><Check /></el-icon>
              保存配置
            </el-button>
            <el-button
              type="success"
              :loading="executing"
              :disabled="suiteEndpoints.length === 0"
              @click="executeSuite"
            >
              <el-icon><VideoPlay /></el-icon>
              执行测试
            </el-button>
          </div>

          <!-- 执行进度条 -->
          <div v-if="executing" class="progress-bar">
            <el-progress :percentage="execProgress" :stroke-width="8" />
            <span class="progress-text">{{ execStatusText }}</span>
          </div>

          <!-- 执行结果 -->
          <div v-if="execResult" class="exec-result">
            <div class="result-summary">
              <h3>执行结果</h3>
              <div class="result-stats">
                <div class="stat-item stat-pass">
                  <span class="stat-value">{{ execResult.passed }}</span>
                  <span class="stat-label">通过</span>
                </div>
                <div class="stat-item stat-fail">
                  <span class="stat-value">{{ execResult.failed }}</span>
                  <span class="stat-label">失败</span>
                </div>
                <div class="stat-item stat-total">
                  <span class="stat-value">{{ execResult.total_endpoints }}</span>
                  <span class="stat-label">总数</span>
                </div>
              </div>
            </div>

            <!-- 逐接口详情 -->
            <div v-for="r in execResult.results" :key="r.endpoint_id" class="result-detail">
              <div
                class="result-header"
                :class="{ 'result-pass': r.passed, 'result-fail': !r.passed }"
                @click="toggleResultExpand(r.endpoint_id)"
              >
                <el-tag :color="METHOD_COLORS[r.method]" size="small" effect="dark">{{ r.method }}</el-tag>
                <span class="result-path">{{ r.path }}</span>
                <span class="result-name">{{ r.endpoint_name }}</span>
                <el-tag :type="r.passed ? 'success' : 'danger'" size="small" effect="plain">
                  {{ r.passed ? '通过' : '失败' }}
                </el-tag>
                <span class="result-elapsed">{{ r.elapsed_ms.toFixed(0) }}ms</span>
                <el-icon class="expand-icon">
                  <ArrowDown v-if="!expandedResults[r.endpoint_id]" />
                  <ArrowUp v-else />
                </el-icon>
              </div>

              <div v-if="expandedResults[r.endpoint_id]" class="result-body">
                <el-tabs type="border-card" size="small">
                  <el-tab-pane label="请求报文">
                    <div class="code-block">
                      <pre>{{ formatResultRequest(r) }}</pre>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="响应报文">
                    <div class="code-block">
                      <pre>{{ formatResultResponse(r) }}</pre>
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="断言结果">
                    <div v-if="r.assertion_details && r.assertion_details.length > 0">
                      <div
                        v-for="(ad, aidx) in r.assertion_details"
                        :key="aidx"
                        class="assertion-item"
                        :class="{ 'ad-pass': ad.passed, 'ad-fail': !ad.passed }"
                      >
                        <el-icon>
                          <SuccessFilled v-if="ad.passed" />
                          <WarningFilled v-else />
                        </el-icon>
                        <span>{{ ad.detail }}</span>
                      </div>
                    </div>
                    <div v-else-if="r.error" class="error-message">
                      <el-alert :title="r.error" type="error" show-icon :closable="false" />
                    </div>
                    <div v-else class="no-assertion">无断言配置</div>
                  </el-tab-pane>
                </el-tabs>
              </div>
            </div>
          </div>
        </template>

        <!-- 未选择套件时的占位 -->
        <template v-else>
          <div class="placeholder">
            <el-empty description="请从左侧选择一个测试套件" :image-size="120" />
          </div>
        </template>
      </div>
    </div>

    <!-- 新建套件对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建测试套件" width="420px">
      <el-form label-width="80px">
        <el-form-item label="套件名称" required>
          <el-input v-model="createForm.name" placeholder="登录流程测试" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="套件描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createSuite">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * API 自动化测试页面
 *
 * 左右分栏布局，左侧为项目选择和套件列表，右侧为配置区和执行结果。
 * 支持接口选择（级联选择+拖拽排序）、断言配置、测试执行和结果查看。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Check,
  VideoPlay,
  Setting,
  Rank,
  Delete,
  ArrowDown,
  ArrowUp,
  SuccessFilled,
  WarningFilled,
} from '@element-plus/icons-vue'
import { apiTestingApi } from '@/api/apiTesting'
import type {
  ApiProject,
  ApiEndpoint,
  ApiTestSuite,
  EndpointConfig,
  AssertionItem,
  ApiTestReport,
} from '@/types/api-testing'
import { METHOD_COLORS, ASSERTION_TYPE_OPTIONS } from '@/types/api-testing'

// ==================== 状态 ====================
const projects = ref<ApiProject[]>([])
const selectedProjectId = ref<number | null>(null)
const suites = ref<ApiTestSuite[]>([])
const loadingSuites = ref(false)
const selectedSuiteId = ref<number | null>(null)
const selectedSuite = ref<ApiTestSuite | null>(null)

// 右侧 tab
const activeTab = ref('basic')

// 套件编辑表单
const suiteForm = ref({ name: '', description: '' })

// 接口选择
const availableEndpoints = ref<ApiEndpoint[]>([])
const endpointToAdd = ref<number | null>(null)
const suiteEndpoints = ref<(EndpointConfig & { method?: string; path?: string; name?: string })[]>([])
const dragIndex = ref<number | null>(null)

// 断言配置
const assertionLogic = ref<'and' | 'or'>('and')
const assertionRules = ref<AssertionItem[]>([])

// 执行
const executing = ref(false)
const execProgress = ref(0)
const execStatusText = ref('')
const execResult = ref<ApiTestReport | null>(null)
const expandedResults = ref<Record<number, boolean>>({})

// 新建
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({ name: '', description: '' })

// ==================== 方法 ====================

/** 加载项目列表 */
async function fetchProjects() {
  try {
    const res = await apiTestingApi.listProjects()
    projects.value = res.data
  } catch {
    ElMessage.error('获取项目列表失败')
  }
}

/** 项目变更 */
async function onProjectChange() {
  suites.value = []
  selectedSuiteId.value = null
  selectedSuite.value = null
  execResult.value = null
  if (!selectedProjectId.value) return
  await fetchSuites()
  await fetchAvailableEndpoints()
}

/** 加载套件列表 */
async function fetchSuites() {
  if (!selectedProjectId.value) return
  loadingSuites.value = true
  try {
    const res = await apiTestingApi.listTestSuites(selectedProjectId.value)
    suites.value = res.data
  } catch {
    ElMessage.error('获取测试套件列表失败')
  } finally {
    loadingSuites.value = false
  }
}

/** 加载可用接口 */
async function fetchAvailableEndpoints() {
  if (!selectedProjectId.value) return
  try {
    const res = await apiTestingApi.listEndpoints(selectedProjectId.value)
    availableEndpoints.value = res.data
  } catch {
    ElMessage.error('获取接口列表失败')
  }
}

/** 选择套件 */
function selectSuite(suite: ApiTestSuite) {
  selectedSuiteId.value = suite.id
  selectedSuite.value = suite
  execResult.value = null

  suiteForm.value = {
    name: suite.name,
    description: suite.description || '',
  }

  // 还原接口配置
  suiteEndpoints.value = (suite.endpoints_config || []).map((ec: any) => {
    const ep = availableEndpoints.value.find((e) => e.id === (ec.endpoint_id || ec))
    return {
      endpoint_id: ec.endpoint_id || ec,
      name: ec.name || ep?.name || '',
      path: ec.path || ep?.path || '',
      method: ec.method || ep?.method || 'GET',
      variable_overrides: ec.variable_overrides || {},
    }
  })

  // 还原断言配置
  if (suite.assertions) {
    assertionLogic.value = suite.assertions.logic || 'and'
    assertionRules.value = suite.assertions.rules || []
  } else {
    assertionLogic.value = 'and'
    assertionRules.value = []
  }

  activeTab.value = 'basic'
}

/** 添加接口到套件 */
function addEndpointToSuite(endpointId: number | null) {
  if (!endpointId) return
  const ep = availableEndpoints.value.find((e) => e.id === endpointId)
  if (!ep) return
  if (suiteEndpoints.value.find((s) => s.endpoint_id === endpointId)) {
    ElMessage.warning('该接口已添加')
    return
  }
  suiteEndpoints.value.push({
    endpoint_id: endpointId,
    name: ep.name,
    path: ep.path,
    method: ep.method,
    variable_overrides: {},
  })
  endpointToAdd.value = null
}

/** 从套件移除接口 */
function removeEndpointFromSuite(index: number) {
  suiteEndpoints.value.splice(index, 1)
}

// 拖拽排序
function onDragStart(index: number) {
  dragIndex.value = index
}
function onDragOver(_index: number) {
  // 不执行操作，允许放置
}
function onDrop(index: number) {
  if (dragIndex.value === null || dragIndex.value === index) return
  const item = suiteEndpoints.value.splice(dragIndex.value, 1)[0]
  suiteEndpoints.value.splice(index, 0, item)
  dragIndex.value = null
}

/** 添加断言规则 */
function addAssertionRule() {
  assertionRules.value.push({
    type: 'status_code',
    operator: 'eq',
    expected: 200,
  })
}

/** 切换断言类型时重置字段 */
function resetAssertionRule(rule: AssertionItem) {
  rule.operator = 'eq'
  rule.expected = undefined
  rule.header = undefined
  rule.jsonPath = undefined
  rule.maxMs = undefined
  if (rule.type === 'status_code') rule.expected = 200
  if (rule.type === 'response_time') rule.maxMs = 3000
}

/** 保存套件配置 */
async function saveSuiteConfig() {
  if (!selectedSuite.value || !selectedProjectId.value) return

  try {
    const data = {
      name: suiteForm.value.name,
      description: suiteForm.value.description || null,
      endpoints_config: suiteEndpoints.value.map((ep) => ({
        endpoint_id: ep.endpoint_id,
        variable_overrides: ep.variable_overrides,
      })),
      assertions: {
        logic: assertionLogic.value,
        rules: assertionRules.value,
      },
    }
    await apiTestingApi.updateTestSuite(selectedSuite.value.id, data)
    ElMessage.success('配置已保存')
    await fetchSuites()
    // 更新本地 selectedSuite
    const updated = suites.value.find((s) => s.id === selectedSuite.value?.id)
    if (updated) selectedSuite.value = updated
  } catch {
    ElMessage.error('保存配置失败')
  }
}

/** 执行测试 */
async function executeSuite() {
  if (!selectedSuite.value) return
  executing.value = true
  execProgress.value = 10
  execStatusText.value = '正在执行...'

  try {
    const res = await apiTestingApi.executeTestSuite(selectedSuite.value.id)
    execProgress.value = 100
    execStatusText.value = '执行完成'

    // 获取详细报告
    const reportRes = await apiTestingApi.getTestReports(selectedSuite.value.id)
    const reports = reportRes.data
    if (reports.length > 0) {
      const latest = reports[reports.length - 1]
      execResult.value = latest as unknown as ApiTestReport
    }

    ElMessage.success(res.message || '执行完成')
    await fetchSuites()
  } catch {
    execProgress.value = 0
    execStatusText.value = '执行失败'
    ElMessage.error('执行失败')
  } finally {
    executing.value = false
  }
}

/** 展开/收起接口详情 */
function toggleResultExpand(endpointId: number) {
  expandedResults.value[endpointId] = !expandedResults.value[endpointId]
}

/** 格式化请求报文 */
function formatResultRequest(r: any): string {
  const lines: string[] = []
  lines.push(`${r.method} ${r.path}`)
  if (r.response_headers) {
    lines.push('')
    lines.push('--- Headers ---')
    Object.entries(r.response_headers).slice(0, 10).forEach(([k, v]) => {
      lines.push(`${k}: ${v}`)
    })
  }
  return lines.join('\n')
}

/** 格式化响应报文 */
function formatResultResponse(r: any): string {
  if (r.response_body) {
    try {
      return JSON.stringify(r.response_body, null, 2)
    } catch {
      return String(r.response_body)
    }
  }
  return r.error || '无响应'
}

/** 状态标签类型 */
function statusTagType(status: string): 'info' | 'primary' | 'warning' | 'success' | 'danger' {
  const map: Record<string, 'info' | 'primary' | 'warning' | 'success' | 'danger'> = {
    draft: 'info',
    ready: 'primary',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

/** 状态中文标签 */
function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    ready: '就绪',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

/** 新建套件对话框 */
function openCreateSuite() {
  createForm.value = { name: '', description: '' }
  showCreateDialog.value = true
}

/** 创建套件 */
async function createSuite() {
  if (!createForm.value.name) {
    ElMessage.warning('请输入套件名称')
    return
  }
  if (!selectedProjectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  creating.value = true
  try {
    const res = await apiTestingApi.createTestSuite({
      project_id: selectedProjectId.value,
      name: createForm.value.name,
      description: createForm.value.description || null,
    })
    ElMessage.success('套件创建成功')
    showCreateDialog.value = false
    await fetchSuites()
    // 自动选中新创建的套件
    if (res.data) {
      selectSuite(res.data as unknown as ApiTestSuite)
    }
  } catch {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

/** 编辑套件（在左侧列表中编辑就是在右侧编辑） */
function openEditSuite(suite: ApiTestSuite) {
  selectSuite(suite)
}

/** 删除套件 */
async function confirmDeleteSuite(suite: ApiTestSuite) {
  try {
    await ElMessageBox.confirm(`确定要删除套件「${suite.name}」吗？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await apiTestingApi.deleteTestSuite(suite.id)
    ElMessage.success('删除成功')
    if (selectedSuiteId.value === suite.id) {
      selectedSuiteId.value = null
      selectedSuite.value = null
      execResult.value = null
    }
    await fetchSuites()
  } catch {
    // 取消删除不处理
  }
}

// ==================== 初始化 ====================
onMounted(fetchProjects)
</script>

<style scoped>
.api-auto-test {
  padding: 20px;
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.page-title {
  margin-bottom: 16px;
}

.page-title h2 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.page-desc {
  font-size: 13px;
  color: #909399;
}

.split-layout {
  display: flex;
  gap: 16px;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 300px;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.right-panel {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-section {
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #ebeef5;
}

.panel-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-header .panel-title {
  margin: 0;
}

.loading-wrap {
  padding: 8px 0;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 20px 0;
  font-size: 13px;
}

.suite-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.suite-item {
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  border: 1px solid transparent;
}

.suite-item:hover {
  background: #f5f7fa;
}

.suite-item.active {
  background: #ecf5ff;
  border-color: #409eff;
}

.suite-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.suite-name {
  font-size: 13px;
  font-weight: 500;
}

.suite-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

.section-tip {
  font-size: 12px;
  color: #909399;
  margin: 0 0 8px 0;
}

.cascader-row {
  margin-bottom: 12px;
}

.selected-endpoints {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.selected-endpoint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: grab;
}

.selected-endpoint:active {
  cursor: grabbing;
}

.drag-handle {
  color: #909399;
  display: flex;
  align-items: center;
}

.method-badge {
  min-width: 56px;
  text-align: center;
  font-weight: 600;
}

.ep-path {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  flex: 1;
}

.ep-name {
  font-size: 12px;
  color: #303133;
  min-width: 80px;
}

.ep-actions {
  display: flex;
  gap: 2px;
}

.var-override-form {
  padding: 4px;
}

.var-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.empty-var {
  color: #909399;
  font-size: 12px;
  text-align: center;
}

.assertion-area {
  padding: 4px 0;
}

.assertion-logic {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.assertion-rule {
  margin-bottom: 8px;
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.time-label {
  font-size: 13px;
  color: #606266;
  line-height: 32px;
}

.action-bar {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 12px;
}

.progress-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.progress-text {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.exec-result {
  margin-top: 16px;
}

.result-summary {
  margin-bottom: 12px;
}

.result-summary h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
}

.result-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px 20px;
  border-radius: 6px;
  min-width: 80px;
}

.stat-pass {
  background: #f0f9eb;
}

.stat-fail {
  background: #fef0f0;
}

.stat-total {
  background: #f5f7fa;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
}

.stat-pass .stat-value {
  color: #67c23a;
}

.stat-fail .stat-value {
  color: #f56c6c;
}

.stat-total .stat-value {
  color: #606266;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.result-detail {
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.result-header:hover {
  background: #f5f7fa;
}

.result-pass {
  border-left: 3px solid #67c23a;
}

.result-fail {
  border-left: 3px solid #f56c6c;
}

.result-path {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  flex: 1;
}

.result-name {
  font-size: 12px;
  color: #303133;
}

.result-elapsed {
  font-size: 11px;
  color: #909399;
}

.expand-icon {
  color: #909399;
}

.result-body {
  border-top: 1px solid #ebeef5;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
}

.code-block pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.assertion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 13px;
  border-radius: 4px;
  margin-bottom: 4px;
}

.ad-pass {
  background: #f0f9eb;
  color: #67c23a;
}

.ad-fail {
  background: #fef0f0;
  color: #f56c6c;
}

.error-message {
  margin: 8px 0;
}

.no-assertion {
  text-align: center;
  color: #909399;
  padding: 16px;
  font-size: 13px;
}

.placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}
</style>

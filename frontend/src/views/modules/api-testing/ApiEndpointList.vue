<template>
  <div class="page-wrap">
    <!-- 面包屑导航 -->
    <div class="breadcrumb-bar">
      <el-breadcrumb>
        <el-breadcrumb-item :to="{ path: '/modules/api-testing/projects' }">
          API 项目管理
        </el-breadcrumb-item>
        <el-breadcrumb-item>{{ projectName }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 页面标题与操作栏 -->
    <div class="page-header">
      <div class="title-group">
        <h1 class="page-title">{{ projectName }} - 接口管理</h1>
        <span class="page-desc">管理 API 接口定义</span>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建接口
        </el-button>
      </div>
    </div>

    <!-- 方法计数栏 -->
    <div class="method-bar">
      <div
        v-for="m in methodCounts"
        :key="m.method"
        class="method-stat"
        :style="{ borderLeftColor: METHOD_COLORS[m.method] }"
      >
        <span class="method-label" :style="{ color: METHOD_COLORS[m.method] }">{{ m.method }}</span>
        <span class="method-count">{{ m.count }}</span>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="filterMethod" placeholder="方法筛选" clearable style="width: 140px" @change="fetchEndpoints">
        <el-option label="全部方法" value="" />
        <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
      </el-select>
      <el-select v-model="filterTag" placeholder="标签筛选" clearable style="width: 140px" @change="fetchEndpoints">
        <el-option label="全部标签" value="" />
        <el-option v-for="t in tagOptions" :key="t" :label="t" :value="t" />
      </el-select>
    </div>

    <!-- 视图切换 -->
    <div class="view-toggle">
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button value="tree">
          <el-icon><FolderOpened /></el-icon>
        </el-radio-button>
        <el-radio-button value="table">
          <el-icon><List /></el-icon>
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 树形视图（按标签分组） -->
    <template v-else-if="viewMode === 'tree'">
      <div v-for="(group, tag) in groupedEndpoints" :key="tag" class="tag-group">
        <div class="tag-group-header">
          <el-tag>{{ tag || '未分类' }}</el-tag>
          <span class="tag-count">{{ group.length }} 个接口</span>
        </div>
        <div class="tag-group-body">
          <div v-for="ep in group" :key="ep.id" class="endpoint-row" @click="openEditDialog(ep)">
            <el-tag
              :color="METHOD_COLORS[ep.method] || '#909399'"
              class="method-tag"
              size="small"
              effect="dark"
            >
              {{ ep.method }}
            </el-tag>
            <span class="endpoint-path">{{ ep.path }}</span>
            <span class="endpoint-name">{{ ep.name }}</span>
            <div class="row-actions">
              <el-button text size="small" type="danger" @click.stop="confirmDelete(ep)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-if="endpoints.length === 0" description="暂无接口" />
    </template>

    <!-- 表格视图 -->
    <el-card v-else shadow="never" class="config-table-card">
      <el-table :data="endpoints" stripe>
        <el-table-column label="方法" min-width="90" align="center">
          <template #default="{ row }">
            <el-tag
              :color="METHOD_COLORS[row.method] || '#909399'"
              effect="dark"
              size="small"
            >
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" min-width="200" align="center" show-overflow-tooltip />
        <el-table-column prop="name" label="名称" min-width="160" align="center" show-overflow-tooltip />
        <el-table-column prop="tag" label="标签" min-width="120" align="center" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag v-if="row.tag" size="small" effect="plain">{{ row.tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button text size="small" @click.stop="openEditDialog(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click.stop="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑接口对话框 -->
    <el-dialog
      v-model="showEndpointDialog"
      :title="isEditing ? '编辑接口' : '新建接口'"
      width="680px"
      :close-on-click-modal="false"
    >
      <el-form ref="endpointFormRef" :model="endpointForm" :rules="endpointRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="方法" prop="method">
              <el-select v-model="endpointForm.method" placeholder="选择方法">
                <el-option v-for="m in methodOptions" :key="m" :label="m" :value="m" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="路径" prop="path">
              <el-input v-model="endpointForm.path" placeholder="/api/v1/users" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="名称" prop="name">
          <el-input v-model="endpointForm.name" placeholder="获取用户列表" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标签">
              <el-input v-model="endpointForm.tag" placeholder="用户管理" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="endpointForm.status" placeholder="状态">
                <el-option label="启用" value="active" />
                <el-option label="禁用" value="disabled" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 4 个 Tab：请求参数、请求头、请求体、响应示例 -->
        <el-tabs type="border-card" class="detail-tabs">
          <el-tab-pane label="请求参数">
            <el-table :data="paramRows" size="small" max-height="240" style="width: 100%">
              <el-table-column label="参数名" min-width="140">
                <template #default="{ $index }">
                  <el-input v-model="paramRows[$index].key" size="small" placeholder="参数名" />
                </template>
              </el-table-column>
              <el-table-column label="值" min-width="140">
                <template #default="{ $index }">
                  <el-input v-model="paramRows[$index].value" size="small" placeholder="默认值" />
                </template>
              </el-table-column>
              <el-table-column label="类型" width="100">
                <template #default="{ $index }">
                  <el-select v-model="paramRows[$index].type" size="small" placeholder="类型">
                    <el-option label="string" value="string" />
                    <el-option label="number" value="number" />
                    <el-option label="boolean" value="boolean" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="必需" width="60" align="center">
                <template #default="{ $index }">
                  <el-checkbox v-model="paramRows[$index].required" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60">
                <template #default="{ $index }">
                  <el-button text size="small" type="danger" @click="paramRows.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button size="small" style="margin-top: 8px" @click="paramRows.push({ key: '', value: '', type: 'string', required: false })">
              添加参数
            </el-button>
          </el-tab-pane>

          <el-tab-pane label="请求头">
            <el-table :data="headerRows" size="small" max-height="240" style="width: 100%">
              <el-table-column label="请求头名" min-width="160">
                <template #default="{ $index }">
                  <el-input v-model="headerRows[$index].key" size="small" placeholder="Content-Type" />
                </template>
              </el-table-column>
              <el-table-column label="值" min-width="160">
                <template #default="{ $index }">
                  <el-input v-model="headerRows[$index].value" size="small" placeholder="application/json" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60">
                <template #default="{ $index }">
                  <el-button text size="small" type="danger" @click="headerRows.splice($index, 1)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button size="small" style="margin-top: 8px" @click="headerRows.push({ key: '', value: '', description: '' })">
              添加请求头
            </el-button>
          </el-tab-pane>

          <el-tab-pane label="请求体">
            <el-input
              v-model="requestBodyText"
              type="textarea"
              :rows="8"
              placeholder="请输入 JSON Schema 或示例 JSON"
            />
          </el-tab-pane>

          <el-tab-pane label="响应示例">
            <el-input
              v-model="responseExampleText"
              type="textarea"
              :rows="8"
              placeholder="请输入响应 JSON 示例"
            />
          </el-tab-pane>
        </el-tabs>

        <el-form-item label="描述" style="margin-top: 12px">
          <el-input v-model="endpointForm.description" type="textarea" :rows="2" placeholder="接口描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEndpointDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEndpoint">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * API 接口管理页面
 *
 * 方法计数栏、树形/表格视图切换、按方法/标签筛选、新建/编辑弹窗含 4 个 Tab。
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, FolderOpened, List } from '@element-plus/icons-vue'
import { apiTestingApi } from '@/api/apiTesting'
import type { ApiEndpoint, ApiParam } from '@/types/api-testing'
import { METHOD_COLORS, METHOD_OPTIONS } from '@/types/api-testing'

const route = useRoute()
const router = useRouter()
const projectId = Number(route.params.id)

// ==================== 状态 ====================
const loading = ref(false)
const saving = ref(false)
const projectName = ref('')
const endpoints = ref<ApiEndpoint[]>([])
const viewMode = ref<'tree' | 'table'>('tree')
const filterMethod = ref('')
const filterTag = ref('')
const showEndpointDialog = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const endpointFormRef = ref<FormInstance>()
const methodOptions = METHOD_OPTIONS.map((m) => m.value)

const endpointForm = ref({
  name: '',
  path: '',
  method: 'GET',
  tag: '',
  description: '',
  status: 'active',
})

const paramRows = ref<ApiParam[]>([])
const headerRows = ref<ApiParam[]>([])
const requestBodyText = ref('')
const responseExampleText = ref('')

const endpointRules: FormRules = {
  name: [{ required: true, message: '请输入接口名称', trigger: 'blur' }],
  path: [{ required: true, message: '请输入接口路径', trigger: 'blur' }],
  method: [{ required: true, message: '请选择 HTTP 方法', trigger: 'change' }],
}

// ==================== 计算属性 ====================

/** 方法计数 */
const methodCounts = computed(() => {
  const counts: Record<string, number> = { GET: 0, POST: 0, PUT: 0, DELETE: 0, PATCH: 0 }
  endpoints.value.forEach((ep) => {
    if (counts[ep.method] !== undefined) counts[ep.method]++
  })
  return Object.entries(counts)
    .filter(([, count]) => count > 0)
    .map(([method, count]) => ({ method, count }))
})

/** 标签选项（去重） */
const tagOptions = computed(() => {
  const tags = new Set<string>()
  endpoints.value.forEach((ep) => {
    if (ep.tag) tags.add(ep.tag)
  })
  return Array.from(tags).sort()
})

/** 按标签分组 */
const groupedEndpoints = computed(() => {
  const groups: Record<string, ApiEndpoint[]> = {}
  endpoints.value.forEach((ep) => {
    const key = ep.tag || '__untagged__'
    if (!groups[key]) groups[key] = []
    groups[key].push(ep)
  })
  // 对组名排序，未分类放最后
  const sorted: Record<string, ApiEndpoint[]> = {}
  const keys = Object.keys(groups).sort()
  const untaggedKey = '__untagged__'
  keys.forEach((k) => {
    if (k !== untaggedKey) sorted[k] = groups[k]
  })
  if (groups[untaggedKey]) sorted['未分类'] = groups[untaggedKey]
  return sorted
})

// ==================== 方法 ====================

/** 获取项目信息和接口列表 */
async function fetchProjectInfo() {
  try {
    const res = await apiTestingApi.listProjects()
    const project = res.data.find((p) => p.id === projectId)
    if (project) {
      projectName.value = project.name
    } else {
      ElMessage.error('项目不存在')
      router.push('/modules/api-testing/projects')
    }
  } catch {
    ElMessage.error('获取项目信息失败')
  }
}

async function fetchEndpoints() {
  loading.value = true
  try {
    const res = await apiTestingApi.listEndpoints(
      projectId,
      filterMethod.value || undefined,
      filterTag.value || undefined,
    )
    endpoints.value = res.data
  } catch {
    ElMessage.error('获取接口列表失败')
  } finally {
    loading.value = false
  }
}

/** 填充分段表数据到弹窗 */
function populateTabData(endpoint: ApiEndpoint | null) {
  if (endpoint) {
    paramRows.value = endpoint.request_params || []
    headerRows.value = endpoint.request_headers || []
    requestBodyText.value = endpoint.request_body
      ? JSON.stringify(endpoint.request_body, null, 2)
      : ''
    responseExampleText.value = endpoint.response_example
      ? JSON.stringify(endpoint.response_example, null, 2)
      : ''
  } else {
    paramRows.value = []
    headerRows.value = []
    requestBodyText.value = ''
    responseExampleText.value = ''
  }
}

/** 打开新建对话框 */
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  endpointForm.value = { name: '', path: '', method: 'GET', tag: '', description: '', status: 'active' }
  populateTabData(null)
  showEndpointDialog.value = true
}

/** 打开编辑对话框 */
function openEditDialog(endpoint: ApiEndpoint) {
  isEditing.value = true
  editingId.value = endpoint.id
  endpointForm.value = {
    name: endpoint.name,
    path: endpoint.path,
    method: endpoint.method,
    tag: endpoint.tag || '',
    description: endpoint.description || '',
    status: endpoint.status,
  }
  populateTabData(endpoint)
  showEndpointDialog.value = true
}

/** 解析 JSON 文本，失败返回 null */
function tryParseJson(text: string): Record<string, unknown> | null {
  if (!text.trim()) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

/** 保存接口 */
async function saveEndpoint() {
  const valid = await endpointFormRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const data = {
      name: endpointForm.value.name,
      path: endpointForm.value.path,
      method: endpointForm.value.method,
      tag: endpointForm.value.tag || null,
      description: endpointForm.value.description || null,
      request_params: paramRows.value.filter((p) => p.key) || null,
      request_headers: headerRows.value.filter((h) => h.key) || null,
      request_body: tryParseJson(requestBodyText.value),
      response_example: tryParseJson(responseExampleText.value),
    }

    if (isEditing.value && editingId.value) {
      await apiTestingApi.updateEndpoint(projectId, editingId.value, data)
      ElMessage.success('接口更新成功')
    } else {
      await apiTestingApi.createEndpoint(projectId, data)
      ElMessage.success('接口创建成功')
    }
    showEndpointDialog.value = false
    await fetchEndpoints()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

/** 确认删除 */
async function confirmDelete(endpoint: ApiEndpoint) {
  try {
    await ElMessageBox.confirm(`确定要删除接口「${endpoint.name}」吗？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await apiTestingApi.deleteEndpoint(projectId, endpoint.id)
    ElMessage.success('删除成功')
    await fetchEndpoints()
  } catch {
    // 取消删除不处理
  }
}

// ==================== 初始化 ====================
onMounted(async () => {
  await fetchProjectInfo()
  await fetchEndpoints()
})
</script>

<style scoped lang="scss">
.page-wrap {
  padding: 24px 16px;

  .breadcrumb-bar {
    margin-bottom: 16px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;

    .title-group {
      .page-title {
        margin: 0 0 4px 0;
        font-size: 22px;
        font-weight: 700;
        color: #3d2e1f;
      }

      .page-desc {
        font-size: 13px;
        color: #8b7355;
      }
    }

    .page-actions {
      display: flex;
      gap: 8px;
    }
  }

  .method-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    flex-wrap: wrap;

    .method-stat {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      background: var(--card-bg, #fafafa);
      border-radius: 4px;
      border-left: 3px solid;

      .method-label {
        font-weight: 600;
        font-size: 13px;
      }

      .method-count {
        font-size: 18px;
        font-weight: 700;
        color: var(--text, #3d2e1f);
      }
    }
  }

  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
  }

  .view-toggle {
    margin-bottom: 16px;
  }

  .loading-wrap {
    padding: 20px 0;
  }

  .config-table-card {
    border: 1px solid rgba(180, 150, 120, 0.12);
    border-radius: 8px;
    background: #fffdf9;

    :deep(.el-card__body) {
      padding: 0;
    }
  }

  .tag-group {
    margin-bottom: 20px;

    .tag-group-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      padding: 8px 12px;
      background: var(--card-bg, #f5f7fa);
      border-radius: 4px;

      .tag-count {
        font-size: 12px;
        color: #8b7355;
      }
    }

    .tag-group-body {
      border: 1px solid rgba(180, 150, 120, 0.12);
      border-radius: 4px;
      overflow: hidden;
    }
  }

  .endpoint-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    border-bottom: 1px solid rgba(180, 150, 120, 0.08);
    cursor: pointer;
    transition: background 0.2s;

    &:last-child {
      border-bottom: none;
    }

    &:hover {
      background: var(--card-bg, #f5f7fa);
    }

    .method-tag {
      min-width: 60px;
      text-align: center;
      font-weight: 600;
    }

    .endpoint-path {
      font-family: monospace;
      font-size: 13px;
      color: var(--text-secondary, #5c4a38);
      flex: 1;
    }

    .endpoint-name {
      font-size: 13px;
      color: var(--text, #3d2e1f);
      min-width: 120px;
    }

    .row-actions {
      margin-left: auto;
      white-space: nowrap;
    }
  }

  .detail-tabs {
    margin-top: 12px;
  }
}
</style>

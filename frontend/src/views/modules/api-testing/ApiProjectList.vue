<template>
  <div class="page-wrap">
    <!-- 页面标题与操作栏 -->
    <div class="page-header">
      <div class="title-group">
        <h1 class="page-title">API 项目管理</h1>
        <span class="page-desc">管理 API 项目和接口定义</span>
      </div>
      <div class="page-actions">
        <el-button @click="showSwaggerDialog = true">
          <el-icon><Upload /></el-icon>
          导入 Swagger
        </el-button>
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建项目
        </el-button>
      </div>
    </div>

    <!-- 搜索与筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索项目名称..."
        clearable
        style="flex: 1; min-width: 200px; max-width: 420px"
        @clear="fetchProjects"
        @keyup.enter="fetchProjects"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 140px" @change="fetchProjects">
        <el-option label="全部" value="" />
        <el-option label="启用" value="active" />
        <el-option label="归档" value="archived" />
      </el-select>
      <el-button @click="fetchProjects">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>

    <!-- 视图切换 -->
    <div class="view-toggle">
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button value="card">
          <el-icon><Grid /></el-icon>
        </el-radio-button>
        <el-radio-button value="table">
          <el-icon><List /></el-icon>
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrap">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 卡片视图 -->
    <div v-else-if="viewMode === 'card'" class="card-grid">
      <el-card
        v-for="project in projects"
        :key="project.id"
        shadow="hover"
        class="project-card"
        @click="goToEndpoints(project.id)"
      >
        <div class="card-header">
          <span class="card-name">{{ project.name }}</span>
          <el-tag :type="project.status === 'active' ? 'success' : 'info'" size="small" effect="plain">
            {{ project.status === 'active' ? '启用' : '归档' }}
          </el-tag>
        </div>
        <p class="card-desc">{{ project.description || '暂无描述' }}</p>
        <div class="card-meta">
          <span class="meta-item">
            <el-icon><Connection /></el-icon>
            {{ project.endpoint_count || 0 }} 接口
          </span>
          <span v-if="project.version" class="meta-item">
            <el-icon><PriceTag /></el-icon>
            {{ project.version }}
          </span>
        </div>
        <div class="card-footer">
          <el-button text size="small" @click.stop="openEditDialog(project)">编辑</el-button>
          <el-button text size="small" type="danger" @click.stop="confirmDelete(project)">删除</el-button>
        </div>
      </el-card>

      <el-empty v-if="projects.length === 0" description="暂无项目" />
    </div>

    <!-- 表格视图 -->
    <el-card v-else-if="viewMode === 'table'" shadow="never" class="config-table-card">
      <el-table :data="projects" stripe @row-click="(row: any) => goToEndpoints(row.id)">
        <el-table-column prop="name" label="项目名称" min-width="160" align="center" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="200" align="center" show-overflow-tooltip />
        <el-table-column label="接口数" min-width="80" align="center">
          <template #default="{ row }">
            {{ row.endpoint_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" min-width="100" align="center" show-overflow-tooltip />
        <el-table-column label="状态" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '归档' }}
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

    <!-- 新建/编辑项目对话框 -->
    <el-dialog
      v-model="showProjectDialog"
      :title="isEditing ? '编辑项目' : '新建项目'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form ref="projectFormRef" :model="projectForm" :rules="projectRules" label-width="120px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="projectForm.description" type="textarea" :rows="2" placeholder="项目描述（可选）" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="projectForm.base_url" placeholder="https://api.example.com" />
        </el-form-item>
        <el-form-item label="Swagger URL">
          <el-input v-model="projectForm.swagger_url" placeholder="Swagger 文档地址（可选）" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="projectForm.version" placeholder="v1.0.0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProjectDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>

    <!-- Swagger 导入对话框 -->
    <el-dialog v-model="showSwaggerDialog" title="导入 Swagger 文档" width="520px">
      <el-form label-width="120px">
        <el-form-item label="目标项目" required>
          <el-select v-model="swaggerForm.project_id" placeholder="请选择项目" style="width: 100%">
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Swagger URL" required>
          <el-input
            v-model="swaggerForm.url"
            placeholder="https://petstore.swagger.io/v2/swagger.json"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSwaggerDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="importSwagger">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * API 项目管理页面
 *
 * 支持卡片/表格视图切换、名称搜索、状态筛选、新建/编辑/删除、Swagger 导入。
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Grid,
  List,
  Upload,
  Connection,
  PriceTag,
} from '@element-plus/icons-vue'
import { apiTestingApi } from '@/api/apiTesting'
import type { ApiProject } from '@/types/api-testing'

const router = useRouter()

// ==================== 状态 ====================
const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
const projects = ref<ApiProject[]>([])
const searchQuery = ref('')
const statusFilter = ref('')
const viewMode = ref<'card' | 'table'>('card')
const showProjectDialog = ref(false)
const showSwaggerDialog = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const projectFormRef = ref<FormInstance>()

const projectForm = ref({
  name: '',
  description: '',
  base_url: '',
  swagger_url: '',
  version: '',
})

const swaggerForm = ref({
  project_id: null as number | null,
  url: '',
})

const projectRules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

// ==================== 方法 ====================

/** 获取项目列表 */
async function fetchProjects() {
  loading.value = true
  try {
    const res = await apiTestingApi.listProjects(
      searchQuery.value || undefined,
      statusFilter.value || undefined,
    )
    projects.value = res.data
  } catch {
    ElMessage.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

/** 打开新建对话框 */
function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  projectForm.value = { name: '', description: '', base_url: '', swagger_url: '', version: '' }
  showProjectDialog.value = true
}

/** 打开编辑对话框 */
function openEditDialog(project: ApiProject) {
  isEditing.value = true
  editingId.value = project.id
  projectForm.value = {
    name: project.name,
    description: project.description || '',
    base_url: project.base_url || '',
    swagger_url: project.swagger_url || '',
    version: project.version || '',
  }
  showProjectDialog.value = true
}

/** 保存项目（新建或更新） */
async function saveProject() {
  const valid = await projectFormRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEditing.value && editingId.value) {
      await apiTestingApi.updateProject(editingId.value, projectForm.value)
      ElMessage.success('项目更新成功')
    } else {
      await apiTestingApi.createProject(projectForm.value)
      ElMessage.success('项目创建成功')
    }
    showProjectDialog.value = false
    await fetchProjects()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

/** 确认删除 */
async function confirmDelete(project: ApiProject) {
  try {
    await ElMessageBox.confirm(`确定要删除项目「${project.name}」吗？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await apiTestingApi.deleteProject(project.id)
    ElMessage.success('删除成功')
    await fetchProjects()
  } catch {
    // 取消删除不处理
  }
}

/** 导入 Swagger */
async function importSwagger() {
  if (!swaggerForm.value.project_id || !swaggerForm.value.url) {
    ElMessage.warning('请选择项目和填写 Swagger URL')
    return
  }
  importing.value = true
  try {
    const res = await apiTestingApi.importSwagger({
      project_id: swaggerForm.value.project_id,
      url: swaggerForm.value.url,
    })
    ElMessage.success(res.message || '导入成功')
    showSwaggerDialog.value = false
    await fetchProjects()
  } catch {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

/** 跳转到接口管理页面 */
function goToEndpoints(projectId: number) {
  router.push(`/modules/api-testing/projects/${projectId}/endpoints`)
}

// ==================== 初始化 ====================
onMounted(fetchProjects)
</script>

<style scoped lang="scss">
.page-wrap {
  padding: 24px 16px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;

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

  .filter-bar {
    display: flex;
    gap: 12px;
    align-items: center;
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

  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }

  .project-card {
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid rgba(180, 150, 120, 0.12);
    background: #fffdf9;

    &:hover {
      transform: translateY(-2px);
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;

      .card-name {
        font-size: 15px;
        font-weight: 600;
        color: #3d2e1f;
      }
    }

    .card-desc {
      color: #8b7355;
      font-size: 13px;
      margin: 0 0 12px 0;
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .card-meta {
      display: flex;
      gap: 16px;
      margin-bottom: 12px;

      .meta-item {
        font-size: 12px;
        color: #8b7355;
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }

    .card-footer {
      border-top: 1px solid rgba(180, 150, 120, 0.12);
      padding-top: 8px;
      display: flex;
      justify-content: flex-end;
      gap: 4px;
    }
  }
}
</style>

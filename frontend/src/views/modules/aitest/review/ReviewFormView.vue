<template>
  <div class="page-wrap">
    <div class="back-nav">
      <span class="back-arrow" @click="router.push('/modules/aitest/reviews')">←</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-link" @click="router.push('/modules/aitest/reviews')">评审列表</span>
      <span class="breadcrumb-sep">/</span>
      <span class="breadcrumb-current">{{ isEdit ? '编辑评审' : '新建评审' }}</span>
    </div>

    <h1 class="page-title">{{ isEdit ? '编辑评审' : '新建评审' }}</h1>

    <el-card shadow="never" class="form-card">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="left" v-loading="submitting">
        <!-- 关联项目 -->
        <el-form-item label="关联项目" prop="project_id">
          <el-select
            v-model="form.project_id"
            placeholder="请选择关联项目"
            style="width: 360px"
            filterable
            @change="onProjectChange"
          >
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>

        <!-- 评审名称 -->
        <el-form-item label="评审名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入评审名称" style="width: 480px" maxlength="200" show-word-limit />
        </el-form-item>

        <!-- 评审描述 -->
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入评审描述（可选）" style="width: 480px" />
        </el-form-item>

        <!-- 选择评审人 -->
        <el-form-item label="评审人" prop="reviewer_ids">
          <el-select
            v-model="form.reviewer_ids"
            multiple
            filterable
            placeholder="选择评审人（可选）"
            style="width: 360px"
          >
            <el-option v-for="u in allUsers" :key="u.id" :label="u.username || u.email" :value="u.id" />
          </el-select>
        </el-form-item>

        <!-- 选择用例 -->
        <el-form-item label="选择用例" prop="case_ids">
          <div style="width:100%">
            <el-button :disabled="!form.project_id" @click="showCaseSelector = true">
              选择用例
            </el-button>
            <span v-if="form.case_ids.length" style="margin-left:12px;font-size:13px;color:var(--text-secondary)">
              已选 {{ form.case_ids.length }} 条
            </span>
            <span v-else style="margin-left:12px;font-size:13px;color:var(--text-muted)">请先选择项目</span>
          </div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="form-actions">
            <el-button type="primary" :loading="submitting" @click="handleSave">
              {{ submitting ? '保存中...' : '保存' }}
            </el-button>
            <el-button @click="handleCancel">取消</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用例选择弹窗 -->
    <el-dialog v-model="showCaseSelector" title="选择用例" width="700px" top="5vh">
      <div class="case-selector">
        <div class="selector-toolbar">
          <el-select v-model="caseFilter.project_id" placeholder="按项目筛选" clearable size="small" style="width:200px" @change="loadAllCases">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
          <el-input v-model="caseFilter.search" placeholder="搜索用例..." clearable size="small" style="width:200px" @input="loadAllCasesDebounced" />
          <div style="flex:1" />
          <el-checkbox v-model="selectAllCases" :indeterminate="isIndeterminate" @change="handleSelectAllCases">
            全选
          </el-checkbox>
        </div>
        <div class="selector-list" v-loading="loadingCases">
          <div v-for="tc in allCases" :key="tc.id" class="selector-item">
            <el-checkbox v-model="form.case_ids" :label="tc.id" @change="onCaseSelect">
              <div class="case-info">
                <div class="case-title">{{ tc.name }}</div>
                <div class="case-meta">
                  <PriorityBadge :priority="tc.priority" />
                  <span v-if="tc.module">· {{ tc.module }}</span>
                </div>
              </div>
            </el-checkbox>
          </div>
          <div v-if="allCases.length === 0 && !loadingCases" class="empty-hint">
            暂无可用用例，请先创建测试用例
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showCaseSelector = false">取消</el-button>
        <el-button type="primary" @click="confirmCaseSelection">确认选择 ({{ form.case_ids.length }})</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { aitestApi } from '@/api/aitest'
import { adminApi } from '@/api/admin'
import type { TestProject, TestCase } from '@/types/aitest'
import PriorityBadge from '@/components/aitest/common/PriorityBadge.vue'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.query.edit)

interface ReviewFormData {
  project_id: number | undefined
  name: string
  description: string
  reviewer_ids: number[]
  case_ids: number[]
}

const form = reactive<ReviewFormData>({
  project_id: undefined,
  name: '',
  description: '',
  reviewer_ids: [],
  case_ids: [],
})

const formRef = ref()
const submitting = ref(false)
const projects = ref<TestProject[]>([])
const allUsers = ref<{ id: number; username: string; email: string }[]>([])
const showCaseSelector = ref(false)
const allCases = ref<TestCase[]>([])
const loadingCases = ref(false)

const caseFilter = reactive({
  project_id: undefined as number | undefined,
  search: '',
})

const selectAllCases = computed({
  get: () => allCases.value.length > 0 && form.case_ids.length === allCases.value.length,
  set: () => {},
})
const isIndeterminate = computed(
  () => form.case_ids.length > 0 && form.case_ids.length < allCases.value.length,
)

const rules = {
  project_id: [{ required: true, message: '请选择关联项目', trigger: 'change' }],
  name: [
    { required: true, message: '请输入评审名称', trigger: 'blur' },
    { min: 1, max: 200, message: '名称长度在 1 到 200 个字符', trigger: 'blur' },
  ],
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null
function loadAllCasesDebounced() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadAllCases, 300)
}

async function loadAllCases() {
  loadingCases.value = true
  try {
    const params: Record<string, string> = {}
    if (caseFilter.project_id) params.project_id = String(caseFilter.project_id)
    if (caseFilter.search) params.search = caseFilter.search
    const res = await aitestApi.listTestCases(params)
    allCases.value = res.data || []
  } catch {
    allCases.value = []
  } finally {
    loadingCases.value = false
  }
}

function onProjectChange() {
  form.case_ids = []
  loadAllCases()
}

function handleSelectAllCases(checked: boolean) {
  if (checked) {
    form.case_ids = allCases.value.map(tc => tc.id)
  } else {
    form.case_ids = []
  }
}

function onCaseSelect() {
  // 自动更新全选状态（计算属性已处理）
}

function confirmCaseSelection() {
  showCaseSelector.value = false
}

async function loadProjects() {
  try {
    const res = await aitestApi.listProjects()
    projects.value = res.data || []
  } catch { /* ignore */ }
}

async function loadUsers() {
  try {
    const res = await adminApi.getUsers({ page: 1, page_size: 999 })
    allUsers.value = (res.data || []).map(u => ({
      id: u.id,
      username: u.username,
      email: u.email,
    }))
  } catch { /* ignore */ }
}

async function handleSave() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const res = await aitestApi.createReview({
      project_id: form.project_id!,
      name: form.name,
      cases: form.case_ids.length > 0 ? form.case_ids : null,
      reviewer_ids: form.reviewer_ids.length > 0 ? form.reviewer_ids : null,
    })
    ElMessage.success('评审创建成功')
    router.push(`/modules/aitest/reviews/${res.data.id}`)
  } catch (e: any) {
    const msg = e?.response?.data?.message || e?.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  router.push('/modules/aitest/reviews')
}

onMounted(() => {
  loadProjects()
  loadUsers()
})
</script>

<style scoped>
.page-wrap { max-width: 800px; margin: 0 auto; padding: 32px 24px 64px; }
.back-nav { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #7A6855; margin-bottom: 20px; }
.back-arrow { font-size: 16px; cursor: pointer; color: var(--primary, #C67B5C); }
.back-arrow:hover { color: var(--primary-light, #D49472); }
.breadcrumb-link { cursor: pointer; }
.breadcrumb-link:hover { color: var(--primary, #C67B5C); }
.breadcrumb-sep { color: rgba(180,150,120,0.3); }
.breadcrumb-current { color: var(--text, #3D2E1F); font-weight: 500; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text, #3D2E1F); margin: 0 0 20px; }
.form-card { border: 1px solid var(--border, rgba(180,150,120,0.12)); border-radius: 12px; background: var(--card-bg, #FFFDF9); }
.form-actions { display: flex; gap: 12px; margin-top: 8px; }
.case-selector { min-height: 300px; }
.selector-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.selector-list { max-height: 400px; overflow-y: auto; }
.selector-item { padding: 8px 4px; border-bottom: 1px solid rgba(180,150,120,0.06); }
.selector-item:hover { background: rgba(180,150,120,0.04); }
.case-info { display: flex; flex-direction: column; gap: 2px; }
.case-title { font-size: 13px; font-weight: 500; color: var(--text, #3D2E1F); }
.case-meta { font-size: 11px; color: var(--text-muted, #8B7355); display: flex; align-items: center; gap: 6px; }
.empty-hint { text-align: center; padding: 48px 16px; color: var(--text-muted, #8B7355); }
</style>

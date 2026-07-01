<template>
  <!--
    测试用例表单页面（创建/编辑）

    根据路由参数决定创建或编辑模式。
    - /modules/aitest/testcases/create -> 新建
    - /modules/aitest/testcases/:id/edit -> 编辑
  -->
  <div class="testcase-form-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>{{ isEditMode ? '编辑测试用例' : '创建测试用例' }}</h2>
      <p class="page-desc">
        {{ isEditMode ? '修改已有测试用例的详细信息' : '填写表单创建新的测试用例' }}
      </p>
    </div>

    <!-- 表单卡片 -->
    <el-card class="form-card" shadow="never">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="left"
        class="case-form"
        v-loading="pageLoading"
      >
        <!-- 项目选择（仅在创建时显示） -->
        <el-form-item
          v-if="!isEditMode"
          label="所属项目"
          prop="project_id"
        >
          <el-select
            v-model="form.project_id"
            placeholder="请选择所属项目"
            style="width: 360px"
            clearable
            filterable
          >
            <el-option
              v-for="proj in projectList"
              :key="proj.id"
              :label="proj.name"
              :value="proj.id"
            />
          </el-select>
        </el-form-item>

        <!-- 用例名称 -->
        <el-form-item label="用例名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入测试用例名称"
            style="width: 480px"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 所属模块 -->
        <el-form-item label="所属模块" prop="module">
          <el-input
            v-model="form.module"
            placeholder="请输入所属模块，如：登录、支付"
            style="width: 360px"
          />
        </el-form-item>

        <!-- 优先级 -->
        <el-form-item label="优先级" prop="priority">
          <el-select
            v-model="form.priority"
            placeholder="请选择优先级"
            style="width: 200px"
          >
            <el-option label="P0 - 最高" value="p0" />
            <el-option label="P1 - 高" value="p1" />
            <el-option label="P2 - 中" value="p2" />
            <el-option label="P3 - 低" value="p3" />
          </el-select>
        </el-form-item>

        <!-- 用例类型 -->
        <el-form-item label="用例类型" prop="test_type">
          <el-select
            v-model="form.test_type"
            placeholder="请选择用例类型"
            style="width: 200px"
          >
            <el-option label="功能测试" value="functional" />
            <el-option label="接口测试" value="api" />
            <el-option label="UI 测试" value="ui" />
            <el-option label="应用测试" value="app" />
          </el-select>
        </el-form-item>

        <!-- 前置条件 -->
        <el-form-item label="前置条件" prop="precondition">
          <el-input
            v-model="form.precondition"
            type="textarea"
            :rows="3"
            placeholder="请输入前置条件（可选）"
            style="width: 480px"
          />
        </el-form-item>

        <!-- 测试步骤 -->
        <el-form-item label="测试步骤" prop="test_steps">
          <el-input
            v-model="form.test_steps"
            type="textarea"
            :rows="5"
            placeholder="请输入测试步骤，每步一行"
            style="width: 480px"
          />
        </el-form-item>

        <!-- 预期结果 -->
        <el-form-item label="预期结果" prop="expected_result">
          <el-input
            v-model="form.expected_result"
            type="textarea"
            :rows="3"
            placeholder="请输入预期结果（可选）"
            style="width: 480px"
          />
        </el-form-item>

        <!-- 状态 -->
        <el-form-item label="状态" prop="status">
          <el-select
            v-model="form.status"
            placeholder="请选择状态"
            style="width: 200px"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="启用" value="active" />
            <el-option label="已废弃" value="deprecated" />
          </el-select>
        </el-form-item>

        <!-- 标签 -->
        <el-form-item label="标签" prop="tags">
          <el-select
            v-model="form.tags"
            multiple
            allow-create
            filterable
            default-first-option
            placeholder="输入标签后按回车创建"
            style="width: 480px"
          >
            <el-option
              v-for="tag in existingTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="form-actions">
            <el-button
              type="primary"
              :loading="submitting"
              @click="handleSave"
            >
              {{ submitting ? '保存中...' : '保存' }}
            </el-button>
            <el-button @click="handleCancel">取消</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { aitestApi } from '@/api/aitest'
import type { TestCase, TestProject } from '@/types/aitest'

// ====================================================================
// 路由
// ====================================================================

const route = useRoute()
const router = useRouter()

/** 是否为编辑模式（路由包含 :id 参数） */
const isEditMode = computed(() => !!route.params.id)

/** 用例 ID（编辑模式时有效） */
const caseId = computed(() => Number(route.params.id))

// ====================================================================
// 表单定义
// ====================================================================

/** 表单数据接口 */
interface TestCaseForm {
  project_id: number | undefined
  name: string
  module: string
  priority: string
  test_type: string
  precondition: string
  test_steps: string
  expected_result: string
  status: string
  tags: string[]
}

/** 默认表单数据 */
const defaultForm = (): TestCaseForm => ({
  project_id: undefined,
  name: '',
  module: '',
  priority: 'p2',
  test_type: 'functional',
  precondition: '',
  test_steps: '',
  expected_result: '',
  status: 'draft',
  tags: [],
})

// ====================================================================
// 状态管理
// ====================================================================

/** 表单引用 */
const formRef = ref()
/** 页面加载中 */
const pageLoading = ref(false)
/** 提交中 */
const submitting = ref(false)
/** 项目列表 */
const projectList = ref<TestProject[]>([])
/** 已有标签列表（用于提示） */
const existingTags = ref<string[]>([])

/** 表单数据 */
const form = reactive<TestCaseForm>(defaultForm())

// ====================================================================
// 表单校验规则
// ====================================================================

const rules = {
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' },
    { min: 1, max: 200, message: '名称长度在 1 到 200 个字符', trigger: 'blur' },
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' },
  ],
  test_type: [
    { required: true, message: '请选用例类型', trigger: 'change' },
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' },
  ],
}

// ====================================================================
// 数据加载
// ====================================================================

/** 加载项目列表 */
async function loadProjects() {
  try {
    const res = await aitestApi.listProjects()
    projectList.value = res.data || []
  } catch {
    // 静默失败
  }
}

/** 加载已有标签（从用例列表中提取） */
async function loadExistingTags() {
  try {
    const res = await aitestApi.listTestCases()
    const cases = res.data || []
    const tagSet = new Set<string>()
    cases.forEach((c: TestCase) => {
      if (c.tags) {
        c.tags.forEach((t) => tagSet.add(t))
      }
    })
    existingTags.value = Array.from(tagSet)
  } catch {
    // 静默失败
  }
}

/** 加载已有用例数据（编辑模式） */
async function loadTestCase() {
  if (!isEditMode.value) return

  pageLoading.value = true
  try {
    const res = await aitestApi.getTestCase(caseId.value)
    if (res.code === 0 && res.data) {
      const tc = res.data
      form.name = tc.name || ''
      form.module = tc.module || ''
      form.priority = tc.priority || 'p2'
      form.test_type = tc.test_type || 'functional'
      form.precondition = tc.precondition || ''
      form.test_steps = tc.test_steps || ''
      form.expected_result = tc.expected_result || ''
      form.status = tc.status || 'draft'
      form.tags = tc.tags || []
      form.project_id = tc.project_id ?? undefined
    }
  } catch {
    ElMessage.error('加载用例失败')
  } finally {
    pageLoading.value = false
  }
}

// ====================================================================
// 操作方法
// ====================================================================

/** 保存表单 */
async function handleSave() {
  // 表单校验
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEditMode.value) {
      // 编辑模式：调用更新接口
      await aitestApi.updateTestCase(caseId.value, {
        name: form.name,
        module: form.module || null,
        priority: form.priority,
        test_type: form.test_type,
        precondition: form.precondition || null,
        test_steps: form.test_steps || null,
        expected_result: form.expected_result || null,
        status: form.status,
        tags: form.tags.length > 0 ? form.tags : null,
      })
      ElMessage.success('用例更新成功')
    } else {
      // 创建模式：调用创建接口
      await aitestApi.createTestCase({
        project_id: form.project_id || null,
        name: form.name,
        module: form.module || null,
        priority: form.priority,
        test_type: form.test_type,
        precondition: form.precondition || null,
        test_steps: form.test_steps || null,
        expected_result: form.expected_result || null,
        status: form.status,
        source: 'manual',
        tags: form.tags.length > 0 ? form.tags : null,
      })
      ElMessage.success('用例创建成功')
    }
    // 保存成功后跳转到用例列表页
    router.push('/modules/aitest/testcases')
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

/** 取消返回 */
function handleCancel() {
  router.push('/modules/aitest/testcases')
}

// ====================================================================
// 初始化
// ====================================================================

onMounted(async () => {
  if (!isEditMode.value) {
    // 创建模式：加载项目列表
    await loadProjects()
  }
  // 加载已有标签列表
  loadExistingTags()
  // 加载用例数据（编辑模式）
  await loadTestCase()
})
</script>

<style scoped lang="scss">
.testcase-form-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 6px;
    font-size: 22px;
    color: var(--el-text-color-primary);
  }

  .page-desc {
    margin: 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.form-card {
  max-width: 720px;
  margin: 0 auto;
  border: 1px solid rgba(180, 150, 120, 0.12);
  border-radius: 8px;
  background: #fffdf9;
}

.case-form {
  padding: 8px 0;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
</style>

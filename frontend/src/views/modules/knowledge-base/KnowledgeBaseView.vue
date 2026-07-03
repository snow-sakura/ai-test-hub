<template>
  <div class="kb-page">
    <div class="kb-header">
      <div class="header-left">
        <div class="page-title-wrap">
          <div class="title-icon">
            <el-icon :size="18" color="#fff"><FolderOpened /></el-icon>
          </div>
          <h2 class="page-title">知识库管理</h2>
        </div>
        <span class="page-desc">管理您的知识库和文档，支持多种格式文件上传</span>
      </div>
      <div class="header-right">
        <div class="view-toggle">
          <el-button
            text
            :type="viewMode === 'grid' ? 'primary' : 'default'"
            @click="viewMode = 'grid'"
            class="toggle-btn"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
          <el-button
            text
            :type="viewMode === 'list' ? 'primary' : 'default'"
            @click="viewMode = 'list'"
            class="toggle-btn"
          >
            <el-icon><List /></el-icon>
          </el-button>
        </div>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索知识库..."
          prefix-icon="Search"
          style="width: 280px"
          size="small"
          class="search-input"
        />
        <el-button type="primary" @click="handleCreateKB" class="create-btn">
          <el-icon :size="14"><Plus /></el-icon>
          新建知识库
        </el-button>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon-wrap">
          <div class="stat-icon" style="background: linear-gradient(135deg, rgba(198, 123, 92, 0.15) 0%, rgba(212, 148, 114, 0.1) 100%); color: #C67B5C">
            <el-icon :size="24"><FolderOpened /></el-icon>
          </div>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ knowledgeBases.length }}</div>
          <div class="stat-label">知识库总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap">
          <div class="stat-icon" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(52, 211, 153, 0.1) 100%); color: #10b981">
            <el-icon :size="24"><Document /></el-icon>
          </div>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ totalDocuments }}</div>
          <div class="stat-label">文档总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap">
          <div class="stat-icon" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(96, 165, 250, 0.1) 100%); color: #3b82f6">
            <el-icon :size="24"><CircleCheck /></el-icon>
          </div>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ activeCount }}</div>
          <div class="stat-label">已启用</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-wrap">
          <div class="stat-icon" style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(251, 191, 36, 0.1) 100%); color: #f59e0b">
            <el-icon :size="24"><Clock /></el-icon>
          </div>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ processingCount }}</div>
          <div class="stat-label">处理中</div>
        </div>
      </div>
    </div>

    <div :class="['kb-content', viewMode]">
      <div v-if="viewMode === 'grid'" class="kb-grid">
        <div
          v-for="kb in filteredKnowledgeBases"
          :key="kb.id"
          class="kb-card"
          @click="handleViewDetails(kb)"
        >
          <div class="kb-card-header">
            <div class="kb-icon-wrapper" :style="{ background: getKBIconBg(kb) }">
              <el-icon :size="28" :color="getKBIconColor(kb)"><FolderOpened /></el-icon>
            </div>
            <div class="kb-header-info">
              <h3 class="kb-name">{{ kb.name }}</h3>
              <p v-if="kb.description" class="kb-desc">{{ kb.description }}</p>
            </div>
            <el-tag :type="getStatusType(kb.status)" size="small" class="kb-status">
              {{ getStatusText(kb.status) }}
            </el-tag>
          </div>

          <div class="kb-card-body">
            <div class="kb-metrics">
              <div class="metric-item">
                <el-icon :size="14" color="#8B7355"><Document /></el-icon>
                <span>{{ kb.document_count }} 个文档</span>
              </div>
              <div class="metric-item">
                <el-icon :size="14" color="#8B7355"><Calendar /></el-icon>
                <span>{{ formatTime(kb.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="kb-card-footer">
            <el-button text size="small" @click.stop="handleUploadDocuments(kb)" class="footer-btn">
              <el-icon :size="14"><Upload /></el-icon>
              上传文档
            </el-button>
            <el-button text size="small" @click.stop="handleViewDocuments(kb)" class="footer-btn">
              <el-icon :size="14"><List /></el-icon>
              管理文档
            </el-button>
            <el-button text size="small" type="danger" @click.stop="handleDeleteKB(kb)" class="footer-btn danger">
              <el-icon :size="14"><Delete /></el-icon>
            </el-button>
          </div>
        </div>

        <div v-if="filteredKnowledgeBases.length === 0" class="empty-kb">
          <div class="empty-icon-wrap">
            <div class="empty-icon">
              <el-icon :size="64" color="#D4A574"><FolderOpened /></el-icon>
            </div>
            <div class="empty-ring"></div>
          </div>
          <h3 class="empty-title">暂无知识库</h3>
          <p class="empty-desc">点击右上角按钮创建您的第一个知识库</p>
          <el-button type="primary" @click="handleCreateKB" class="create-btn-lg">
            <el-icon><Plus /></el-icon>
            新建知识库
          </el-button>
        </div>
      </div>

      <div v-else class="kb-list-view">
        <div v-if="filteredKnowledgeBases.length === 0" class="empty-kb">
          <div class="empty-icon-wrap">
            <div class="empty-icon">
              <el-icon :size="64" color="#D4A574"><FolderOpened /></el-icon>
            </div>
            <div class="empty-ring"></div>
          </div>
          <h3 class="empty-title">暂无知识库</h3>
          <p class="empty-desc">点击右上角按钮创建您的第一个知识库</p>
          <el-button type="primary" @click="handleCreateKB" class="create-btn-lg">
            <el-icon><Plus /></el-icon>
            新建知识库
          </el-button>
        </div>

        <div v-else class="list-container">
          <div
            v-for="kb in filteredKnowledgeBases"
            :key="kb.id"
            class="kb-list-item"
            @click="handleViewDetails(kb)"
          >
            <div class="list-item-left">
              <div class="list-icon-wrapper" :style="{ background: getKBIconBg(kb) }">
                <el-icon :size="24" :color="getKBIconColor(kb)"><FolderOpened /></el-icon>
              </div>
              <div class="list-info">
                <div class="list-name">{{ kb.name }}</div>
                <div class="list-meta">
                  <span class="meta-item">
                    <el-icon :size="12" color="#8B7355"><Document /></el-icon>
                    {{ kb.document_count }} 个文档
                  </span>
                  <span class="meta-divider">|</span>
                  <span class="meta-item">
                    <el-icon :size="12" color="#8B7355"><Calendar /></el-icon>
                    {{ formatTime(kb.created_at) }}
                  </span>
                  <span v-if="kb.description" class="meta-divider">|</span>
                  <span v-if="kb.description" class="meta-item">{{ kb.description }}</span>
                </div>
              </div>
            </div>
            <div class="list-item-right">
              <el-tag :type="getStatusType(kb.status)" size="small" class="list-status">
                {{ getStatusText(kb.status) }}
              </el-tag>
              <div class="list-actions">
                <el-button text size="small" @click.stop="handleUploadDocuments(kb)" class="list-action-btn">
                  <el-icon :size="14"><Upload /></el-icon>
                </el-button>
                <el-button text size="small" @click.stop="handleViewDocuments(kb)" class="list-action-btn">
                  <el-icon :size="14"><List /></el-icon>
                </el-button>
                <el-button text size="small" type="danger" @click.stop="handleDeleteKB(kb)" class="list-action-btn danger">
                  <el-icon :size="14"><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCreateDialog" title="新建知识库" width="560px" class="custom-dialog">
      <el-form :model="createForm" class="kb-create-form">
        <el-form-item label="知识库名称" required>
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" class="form-input" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入知识库描述" class="form-input" />
        </el-form-item>
        <el-form-item label="上传文档（可选）">
          <el-upload
            ref="createUploadRef"
            :auto-upload="false"
            :on-change="handleCreateFileChange"
            :on-remove="handleCreateFileRemove"
            :file-list="createFiles"
            multiple
            accept=".docx,.doc,.xmind,.md,.xlsx,.xls,.csv,.txt,.htm,.html,.pdf,.xml"
            drag
            class="file-upload"
          >
            <el-icon class="el-icon--upload" :size="48" color="#C67B5C"><UploadFilled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitCreate" :loading="isCreating">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showUploadDialog" :title="`上传文档到 ${currentKB?.name || ''}`" width="560px" class="custom-dialog">
      <el-form class="kb-upload-form">
        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="uploadFiles"
            multiple
            accept=".docx,.doc,.xmind,.md,.xlsx,.xls,.csv,.txt,.htm,.html,.pdf,.xml"
            drag
            class="file-upload"
          >
            <el-icon class="el-icon--upload" :size="48" color="#C67B5C"><UploadFilled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <div class="el-upload__tip">支持 docx、doc、xmind、md、xlsx、xls、csv、txt、htm、html、pdf、xml 格式</div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitUpload" :loading="isUploading">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDocumentsDialog" :title="`文档管理 - ${currentKB?.name || ''}`" width="800px" top="5vh" class="custom-dialog">
      <div class="documents-header">
        <div class="documents-title-wrap">
          <el-icon :size="16" color="#C67B5C"><Document /></el-icon>
          <span class="documents-title">文档列表</span>
        </div>
        <el-button size="small" type="primary" @click="handleUploadDocuments(currentKB!)">
          <el-icon><Upload /></el-icon>
          上传文档
        </el-button>
      </div>
      <div class="documents-table">
        <el-table :data="currentDocuments" border style="width: 100%" class="kb-doc-table">
          <el-table-column prop="filename" label="文件名" min-width="200">
            <template #default="scope">
              <div class="file-name-cell">
                <el-icon :size="16" color="#C67B5C"><Document /></el-icon>
                <span>{{ scope.row.filename }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="file_size" label="大小" width="100">
            <template #default="scope">{{ formatSize(scope.row.file_size) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)" size="small">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="分块数" width="100">
            <template #default="scope">{{ scope.row.chunk_count || '-' }}</template>
          </el-table-column>
          <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip>
            <template #default="scope">
              <span v-if="scope.row.error_message" style="color: #f56c6c">{{ scope.row.error_message }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="上传时间" width="160">
            <template #default="scope">{{ formatTime(scope.row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="scope">
              <el-button
                size="small"
                type="danger"
                text
                @click="handleDeleteDocument(scope.row)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showDocumentsDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened,
  Document,
  CircleCheck,
  Clock,
  Plus,
  Upload,
  List,
  Delete,
  UploadFilled,
  Calendar,
  Grid,
} from '@element-plus/icons-vue'
import type { KnowledgeBase, KBDocument } from '@/types/ai_chat'
import { knowledgeBaseApi } from '@/api/ai_chat'

const knowledgeBases = ref<KnowledgeBase[]>([])
const searchKeyword = ref('')
const viewMode = ref<'grid' | 'list'>('grid')
const showCreateDialog = ref(false)
const showUploadDialog = ref(false)
const showDocumentsDialog = ref(false)
const currentKB = ref<KnowledgeBase | null>(null)
const currentDocuments = ref<KBDocument[]>([])
const uploadFiles = ref<any[]>([])
const createFiles = ref<any[]>([])
const isCreating = ref(false)
const isUploading = ref(false)

const createForm = ref({
  name: '',
  description: '',
})

const filteredKnowledgeBases = computed(() => {
  if (!searchKeyword.value) return knowledgeBases.value
  const keyword = searchKeyword.value.toLowerCase()
  return knowledgeBases.value.filter((kb) =>
    kb.name.toLowerCase().includes(keyword) ||
    (kb.description && kb.description.toLowerCase().includes(keyword))
  )
})

const totalDocuments = computed(() => {
  return knowledgeBases.value.reduce((sum, kb) => sum + (kb.document_count || 0), 0)
})

const activeCount = computed(() => {
  return knowledgeBases.value.filter((kb) => kb.status === 'active').length
})

const processingCount = computed(() => {
  return knowledgeBases.value.filter((kb) => kb.status === 'processing').length
})

async function loadKnowledgeBases() {
  knowledgeBases.value = await knowledgeBaseApi.list()
}

function handleCreateKB() {
  showCreateDialog.value = true
}

async function handleSubmitCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }

  isCreating.value = true

  await knowledgeBaseApi.create({
    name: createForm.value.name,
    description: createForm.value.description,
  })

  if (createFiles.value.length > 0 && knowledgeBases.value.length > 0) {
    const kb = knowledgeBases.value[knowledgeBases.value.length - 1]
    const files = createFiles.value.map((f) => f.raw)
    await knowledgeBaseApi.documents.upload(kb.id, files)
  }

  await loadKnowledgeBases()
  showCreateDialog.value = false
  createForm.value = { name: '', description: '' }
  createFiles.value = []
  isCreating.value = false
  ElMessage.success('创建成功')
}

function handleUploadDocuments(kb: KnowledgeBase) {
  currentKB.value = kb
  uploadFiles.value = []
  showUploadDialog.value = true
}

function handleFileChange(file: any) {
  uploadFiles.value.push(file)
}

function handleFileRemove(file: any) {
  const index = uploadFiles.value.findIndex((f) => f.name === file.name)
  if (index !== -1) {
    uploadFiles.value.splice(index, 1)
  }
}

async function handleSubmitUpload() {
  if (!currentKB.value) return
  if (uploadFiles.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  isUploading.value = true
  const files = uploadFiles.value.map((f) => f.raw)
  await knowledgeBaseApi.documents.upload(currentKB.value.id, files)

  await loadKnowledgeBases()
  showUploadDialog.value = false
  uploadFiles.value = []
  isUploading.value = false
  ElMessage.success('上传成功')
}

function handleViewDetails(kb: KnowledgeBase) {
  currentKB.value = kb
}

async function handleViewDocuments(kb: KnowledgeBase) {
  currentKB.value = kb
  currentDocuments.value = await knowledgeBaseApi.documents.list(kb.id)
  showDocumentsDialog.value = true
}

async function handleDeleteKB(kb: KnowledgeBase) {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库「${kb.name}」吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await knowledgeBaseApi.delete(kb.id)
    await loadKnowledgeBases()
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

async function handleDeleteDocument(doc: KBDocument) {
  if (!currentKB.value) return
  try {
    await ElMessageBox.confirm(
      `确定要删除文档「${doc.filename}」吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await knowledgeBaseApi.documents.delete(currentKB.value.id, doc.id)
    currentDocuments.value = currentDocuments.value.filter((d) => d.id !== doc.id)
    await loadKnowledgeBases()
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

function handleCreateFileChange(file: any) {
  createFiles.value.push(file)
}

function handleCreateFileRemove(file: any) {
  const index = createFiles.value.findIndex((f) => f.name === file.name)
  if (index !== -1) {
    createFiles.value.splice(index, 1)
  }
}

function getStatusType(status: string): string {
  switch (status) {
    case 'active': return 'success'
    case 'completed': return 'success'
    case 'disabled': return 'info'
    case 'pending': return 'warning'
    case 'processing': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case 'active': return '已启用'
    case 'disabled': return '已禁用'
    case 'pending': return '等待处理'
    case 'processing': return '处理中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    default: return status
  }
}

function getKBIconBg(kb: KnowledgeBase): string {
  const colors: Record<string, string> = {
    active: 'linear-gradient(135deg, rgba(198, 123, 92, 0.18) 0%, rgba(212, 165, 116, 0.12) 100%)',
    processing: 'linear-gradient(135deg, rgba(245, 158, 11, 0.18) 0%, rgba(251, 191, 36, 0.12) 100%)',
    disabled: 'linear-gradient(135deg, rgba(148, 163, 184, 0.18) 0%, rgba(203, 213, 225, 0.12) 100%)',
    failed: 'linear-gradient(135deg, rgba(239, 68, 68, 0.18) 0%, rgba(248, 113, 113, 0.12) 100%)',
  }
  return colors[kb.status] || 'linear-gradient(135deg, rgba(198, 123, 92, 0.18) 0%, rgba(212, 165, 116, 0.12) 100%)'
}

function getKBIconColor(kb: KnowledgeBase): string {
  const colors: Record<string, string> = {
    active: '#C67B5C',
    processing: '#f59e0b',
    disabled: '#94a3b8',
    failed: '#ef4444',
  }
  return colors[kb.status] || '#C67B5C'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

import { formatDate } from '@/utils'

function formatTime(time?: string): string {
  return formatDate(time)
}

onMounted(async () => {
  await loadKnowledgeBases()
})
</script>

<style scoped>
.kb-page {
  padding: 32px;
  background: var(--bg);
  min-height: calc(100vh - 64px);
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 36px;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.page-title-wrap {
  display: flex;
  align-items: center;
  gap: 14px;
}

.title-icon {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 18px rgba(198, 123, 92, 0.35);
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
  letter-spacing: -0.02em;
}

.page-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 10px;
}

.header-right {
  display: flex;
  gap: 16px;
  align-items: center;
}

.view-toggle {
  display: flex;
  background: rgba(198, 123, 92, 0.05);
  border-radius: 12px;
  padding: 5px;
}

.toggle-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.toggle-btn:hover {
  background: rgba(198, 123, 92, 0.08);
}

.search-input .el-input__wrapper {
  border-radius: 12px;
  background: rgba(198, 123, 92, 0.05);
  border-color: rgba(198, 123, 92, 0.1);
}

.search-input .el-input__wrapper.is-focus {
  box-shadow: 0 0 0 3px rgba(198, 123, 92, 0.06);
}

.create-btn {
  border-radius: 12px;
  padding: 10px 22px;
  font-size: 14px;
  font-weight: 600;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(198, 123, 92, 0.35);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(198, 123, 92, 0.45);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 36px;
}

.stat-card {
  background: var(--card-bg);
  border-radius: 20px;
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 20px;
  border: 1px solid rgba(198, 123, 92, 0.06);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent 0%, rgba(198, 123, 92, 0.1) 50%, transparent 100%);
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 40px rgba(180, 150, 120, 0.1);
  border-color: rgba(198, 123, 92, 0.1);
}

.stat-icon-wrap {
  position: relative;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
  margin-top: 8px;
}

.kb-content {
  transition: all 0.3s;
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.kb-card {
  background: var(--card-bg);
  border-radius: 22px;
  overflow: hidden;
  border: 1px solid rgba(198, 123, 92, 0.06);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.kb-card:hover {
  box-shadow: 0 20px 50px rgba(198, 123, 92, 0.14);
  transform: translateY(-8px);
  border-color: rgba(198, 123, 92, 0.12);
}

.kb-card-header {
  padding: 24px;
  display: flex;
  gap: 18px;
  border-bottom: 1px solid rgba(198, 123, 92, 0.05);
}

.kb-icon-wrapper {
  width: 68px;
  height: 68px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kb-header-info {
  flex: 1;
  overflow: hidden;
}

.kb-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 8px 0;
  letter-spacing: -0.01em;
}

.kb-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-status {
  flex-shrink: 0;
  border-radius: 10px;
}

.kb-card-body {
  padding: 20px 24px;
}

.kb-metrics {
  display: flex;
  gap: 32px;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-secondary);
}

.kb-card-footer {
  padding: 18px 24px;
  border-top: 1px solid rgba(198, 123, 92, 0.05);
  display: flex;
  gap: 12px;
}

.footer-btn {
  flex: 1;
  justify-content: center;
  color: var(--text-secondary);
  border-radius: 12px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.footer-btn:hover {
  color: var(--primary);
  background: rgba(198, 123, 92, 0.06);
}

.footer-btn.danger:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.06);
}

.kb-list-view {
  width: 100%;
}

.list-container {
  background: var(--card-bg);
  border-radius: 22px;
  border: 1px solid rgba(198, 123, 92, 0.06);
  overflow: hidden;
}

.kb-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 22px 28px;
  border-bottom: 1px solid rgba(198, 123, 92, 0.05);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.kb-list-item:last-child {
  border-bottom: none;
}

.kb-list-item:hover {
  background: rgba(198, 123, 92, 0.03);
  transform: translateX(4px);
}

.list-item-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.list-icon-wrapper {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.list-info {
  flex: 1;
  min-width: 0;
}

.list-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.list-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 13px;
  color: var(--text-muted);
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.meta-divider {
  color: rgba(180, 150, 120, 0.3);
}

.list-item-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.list-status {
  border-radius: 10px;
}

.list-actions {
  display: flex;
  gap: 8px;
}

.list-action-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  color: var(--text-muted);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.list-action-btn:hover {
  color: var(--primary);
  background: rgba(198, 123, 92, 0.06);
}

.list-action-btn.danger:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.06);
}

.empty-kb {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100px 40px;
  background: var(--card-bg);
  border-radius: 22px;
  border: 2px dashed rgba(198, 123, 92, 0.12);
}

.empty-icon-wrap {
  position: relative;
  display: inline-block;
  margin-bottom: 28px;
}

.empty-icon {
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(198, 123, 92, 0.1) 0%, rgba(212, 165, 116, 0.06) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.empty-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 132px;
  height: 132px;
  border: 2px solid rgba(198, 123, 92, 0.12);
  border-radius: 50%;
  animation: ring-pulse 3s ease-in-out infinite;
}

@keyframes ring-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.2; }
}

.empty-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 12px 0;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0 0 32px 0;
}

.create-btn-lg {
  padding: 14px 32px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #C67B5C 0%, #D49472 100%);
  border: none;
  box-shadow: 0 6px 20px rgba(198, 123, 92, 0.35);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.create-btn-lg:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 26px rgba(198, 123, 92, 0.45);
}

.custom-dialog .el-dialog__header {
  border-bottom: var(--border);
  padding: 24px;
}

.custom-dialog .el-dialog__body {
  padding: 28px 24px;
}

.custom-dialog .el-dialog__footer {
  border-top: var(--border);
  padding: 20px 24px;
}

.kb-create-form,
.kb-upload-form {
  .form-input {
    width: 100%;
  }
}

.file-upload {
  margin-top: 12px;
}

.file-upload .el-upload-dragger {
  border-radius: 16px;
  border-color: rgba(198, 123, 92, 0.15);
  transition: all 0.25s;
}

.file-upload .el-upload-dragger:hover {
  border-color: var(--primary);
  background: rgba(198, 123, 92, 0.03);
}

.el-icon--upload {
  margin-bottom: 12px;
}

.documents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.documents-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.documents-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.documents-table {
  max-height: 520px;
  overflow-y: auto;
}

.kb-doc-table {
  --el-table-border-color: rgba(198, 123, 92, 0.06);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-row-hover-bg-color: rgba(198, 123, 92, 0.03);
}

.kb-doc-table .el-table__header th {
  background: rgba(198, 123, 92, 0.03);
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .kb-grid {
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  }
}

@media (max-width: 768px) {
  .kb-page {
    padding: 20px;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .kb-grid {
    grid-template-columns: 1fr;
  }

  .kb-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .search-input {
    flex: 1;
    min-width: 200px;
  }
}
</style>
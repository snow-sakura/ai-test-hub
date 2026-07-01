<template>
  <div class="document-upload" @dragover.prevent @drop.prevent="handleDrop">
    <div class="upload-area" :class="{ 'is-dragover': isDragover }">
      <el-icon :size="40" color="#8B7355"><UploadFilled /></el-icon>
      <p class="upload-text">拖拽文档到此处，或 <em>点击选择文件</em></p>
      <p class="upload-hint">支持 PDF、DOC、DOCX、TXT、MD（最大 10MB）</p>
      <input
        ref="fileInput"
        type="file"
        accept=".pdf,.doc,.docx,.txt,.md"
        style="display: none"
        @change="handleFileChange"
      />
    </div>
    <div v-if="uploadedFile" class="file-info">
      <el-tag closable @close="clearFile" type="info">
        {{ uploadedFile.name }} ({{ (uploadedFile.size / 1024).toFixed(1) }} KB)
      </el-tag>
      <span v-if="parsedContent" class="parsed-badge">已解析</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { aitestApi } from '@/api/aitest'

const emit = defineEmits<{
  (e: 'content-parsed', content: string): void
}>()

const fileInput = ref<HTMLInputElement>()
const isDragover = ref(false)
const uploadedFile = ref<File | null>(null)
const parsedContent = ref('')
const uploading = ref(false)

async function handleDrop(e: DragEvent) {
  isDragover.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) await uploadFile(file)
}

function handleFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) uploadFile(file)
}

async function uploadFile(file: File) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 10MB')
    return
  }
  uploadedFile.value = file
  uploading.value = true
  try {
    const res = await aitestApi.uploadGenerationDoc(file)
    if (res.data?.content) {
      parsedContent.value = res.data.content
      emit('content-parsed', res.data.content)
    }
  } catch {
    ElMessage.error('文档解析失败')
  } finally {
    uploading.value = false
  }
}

function clearFile() {
  uploadedFile.value = null
  parsedContent.value = ''
}
</script>

<style scoped lang="scss">
.document-upload {
  margin-bottom: 12px;
}
.upload-area {
  border: 2px dashed #d9c8b4;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  background: #faf8f5;
  cursor: pointer;
  transition: all 0.2s;
  &:hover, &.is-dragover {
    border-color: #c4a882;
    background: #f5f0eb;
  }
}
.upload-text {
  margin: 8px 0 4px;
  font-size: 14px;
  color: #6b5a4a;
  em { color: #c4a882; font-style: normal; font-weight: 500; }
}
.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #a09182;
}
.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.parsed-badge {
  font-size: 12px;
  color: #52c41a;
}
</style>

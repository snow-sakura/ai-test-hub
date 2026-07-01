<template>
  <div class="comment-section">
    <div class="comment-input">
      <el-input
        v-model="newComment"
        type="textarea"
        :rows="3"
        placeholder="输入评论..."
        maxlength="2000"
        show-word-limit
      />
      <div class="comment-actions">
        <el-button size="small" type="primary" @click="handleCreate" :disabled="!newComment.trim()">
          发表评论
        </el-button>
      </div>
    </div>

    <div class="comment-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-meta">
          <span class="comment-author">{{ comment.author_name || '用户' }}</span>
          <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          <el-button
            v-if="comment.author_id === currentUserId"
            text
            size="small"
            type="danger"
            @click="handleDelete(comment.id)"
          >
            删除
          </el-button>
        </div>
        <p class="comment-body">{{ comment.content }}</p>
      </div>
      <el-empty v-if="comments.length === 0" description="暂无评论" :image-size="60" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { CaseComment } from '@/types/aitest'
import { aitestApi } from '@/api/aitest'

const props = defineProps<{
  caseId: number
  comments: CaseComment[]
  currentUserId: number
}>()

const emit = defineEmits<{
  (e: 'created'): void
  (e: 'deleted', id: number): void
}>()

const newComment = ref('')

function formatTime(iso?: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function handleCreate() {
  if (!newComment.value.trim()) return
  try {
    await aitestApi.createComment(props.caseId, { content: newComment.value })
    newComment.value = ''
    emit('created')
  } catch {
    ElMessage.error('发表评论失败')
  }
}

async function handleDelete(commentId: number) {
  try {
    await aitestApi.deleteComment(commentId)
    emit('deleted', commentId)
  } catch {
    ElMessage.error('删除评论失败')
  }
}
</script>

<style scoped lang="scss">
.comment-section {
  .comment-input {
    margin-bottom: 16px;
    .comment-actions {
      margin-top: 8px;
      text-align: right;
    }
  }
  .comment-item {
    padding: 12px 0;
    border-bottom: 1px solid #f0ebe4;
    &:last-child { border-bottom: none; }
    .comment-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
      .comment-author { font-weight: 600; font-size: 13px; color: #6b5a4a; }
      .comment-time { font-size: 11px; color: #a09182; }
    }
    .comment-body {
      margin: 0;
      font-size: 13px;
      line-height: 1.6;
      color: #4a3f35;
      white-space: pre-wrap;
    }
  }
}
</style>

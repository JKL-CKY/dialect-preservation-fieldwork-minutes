<template>
  <div class="discussion-panel">
    <div class="discussion-header">
      <h3>
        <el-icon><ChatDotRound /></el-icon>
        语言学团队讨论区
      </h3>
      <el-tag type="info" size="small">{{ messages.length }} 条讨论</el-tag>
    </div>

    <div class="discussion-messages" ref="messagesContainer">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-item"
        :class="{ 'is-researcher': msg.user_role === 'researcher' }"
      >
        <div class="message-avatar">
          <el-avatar :size="36">
            {{ msg.user_name.charAt(0) }}
          </el-avatar>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-author">{{ msg.user_name }}</span>
            <el-tag size="small" :type="msg.user_role === 'researcher' ? 'success' : 'primary'">
              {{ msg.user_role === 'researcher' ? '研究员' : '发音人' }}
            </el-tag>
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
          <div class="message-body">
            <p>{{ msg.content }}</p>
            <div v-if="msg.segment_ref" class="segment-ref">
              <el-button size="small" type="primary" link @click="$emit('jumpToSegment', msg.segment_ref)">
                跳转到相关转写片段
              </el-button>
            </div>
            <div v-if="msg.annotations && msg.annotations.length > 0" class="message-annotations">
              <el-tooltip
                v-for="(ann, idx) in msg.annotations"
                :key="idx"
                :content="`${ann.author}: ${ann.text}`"
                placement="top"
              >
                <el-tag size="small" :type="annotationType(ann.type)">
                  {{ annotationText(ann.type) }}
                </el-tag>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-if="messages.length === 0" description="暂无讨论内容" />
    </div>

    <div class="discussion-input">
      <el-input
        v-model="newMessage"
        type="textarea"
        :rows="2"
        placeholder="输入讨论内容..."
        @keydown.enter.ctrl="sendMessage"
      />
      <div class="input-actions">
        <span class="tip">按 Ctrl+Enter 发送</span>
        <el-button type="primary" :disabled="!newMessage.trim()" @click="sendMessage">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import type { DiscussionMessage } from '@/types'

const props = defineProps<{
  messages: DiscussionMessage[]
}>()

const emit = defineEmits<{
  (e: 'send', content: string): void
  (e: 'jumpToSegment', segmentId: string): void
}>()

const newMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const sendMessage = () => {
  if (!newMessage.value.trim()) return
  emit('send', newMessage.value)
  newMessage.value = ''
}

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const annotationType = (type: string) => {
  const types: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    comment: 'info',
    correction: 'success',
    question: 'warning',
    highlight: 'danger'
  }
  return types[type] || 'info'
}

const annotationText = (type: string) => {
  const texts: Record<string, string> = {
    comment: '评论',
    correction: '修正',
    question: '疑问',
    highlight: '重点'
  }
  return texts[type] || type
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, () => {
  scrollToBottom()
})
</script>

<style scoped>
.discussion-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.discussion-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.discussion-header h3 {
  margin: 0;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.discussion-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-item.is-researcher .message-content {
  background: #f0f9eb;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.message-author {
  font-weight: 600;
  color: #303133;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.message-body p {
  margin: 0 0 8px 0;
  line-height: 1.5;
  color: #606266;
}

.segment-ref {
  margin-top: 8px;
}

.message-annotations {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.discussion-input {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.tip {
  font-size: 12px;
  color: #909399;
}
</style>

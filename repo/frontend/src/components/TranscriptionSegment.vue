<template>
  <div
    class="transcription-segment"
    :class="{ active: isActive }"
    @click="handleClick"
  >
    <div class="segment-header">
      <div class="segment-meta">
        <span
          class="speaker-label"
          :class="segment.speaker_role === 'informant' ? 'speaker-informant' : 'speaker-researcher'"
        >
          <el-icon :size="12">
            <User v-if="segment.speaker_role === 'informant'" />
            <UserFilled v-else />
          </el-icon>
          {{ segment.speaker_name }}
        </span>
        <span class="time-range">
          {{ formatTime(segment.start_time) }} - {{ formatTime(segment.end_time) }}
        </span>
        <el-tag v-if="segment.confidence < 0.8" type="warning" size="small" effect="plain">
          置信度: {{ (segment.confidence * 100).toFixed(0) }}%
        </el-tag>
      </div>
      <div class="segment-actions">
        <el-button
          size="small"
          type="primary"
          text
          @click.stop="playSegment"
        >
          <el-icon><VideoPlay /></el-icon>
          播放
        </el-button>
        <el-button
          size="small"
          type="default"
          text
          @click.stop="isEditing = !isEditing"
        >
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
      </div>
    </div>

    <div v-if="isEditing" class="segment-edit">
      <el-input
        v-model="editText"
        type="textarea"
        :rows="2"
        placeholder="修改转写文本"
        @blur="saveEdit"
        @keyup.enter.ctrl="saveEdit"
      />
      <div class="edit-actions">
        <el-button size="small" type="primary" @click="saveEdit">保存</el-button>
        <el-button size="small" @click="cancelEdit">取消</el-button>
      </div>
    </div>

    <div v-else class="segment-content">
      <p class="text-content">{{ segment.text }}</p>
      <div v-if="segment.ipa_transcription" class="ipa-section">
        <span class="ipa-label">国际音标：</span>
        <span class="ipa-text">{{ segment.ipa_transcription }}</span>
      </div>
      <div v-if="segment.grammar_variants && segment.grammar_variants.length > 0" class="variants-section">
        <div class="variants-label">语法变异点：</div>
        <div class="variants-list">
          <el-tooltip
            v-for="variant in segment.grammar_variants"
            :key="variant.token"
            :content="`${variant.description} | 标准形式: ${variant.standard_form}`"
            placement="top"
          >
            <span class="grammar-tag grammar-variant">
              {{ variant.token }}
              <span class="variant-ipa">/{{ variant.ipa }}/</span>
            </span>
          </el-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { User, UserFilled, VideoPlay, Edit } from '@element-plus/icons-vue'
import type { TranscriptionSegment } from '@/types'

const props = defineProps<{
  segment: TranscriptionSegment
  currentTime?: number
}>()

const emit = defineEmits<{
  (e: 'play', startTime: number): void
  (e: 'update', segmentId: string, data: Partial<TranscriptionSegment>): void
  (e: 'click', segment: TranscriptionSegment): void
}>()

const isEditing = ref(false)
const editText = ref('')

const isActive = computed(() => {
  if (!props.currentTime) return false
  return props.currentTime >= props.segment.start_time && props.currentTime < props.segment.end_time
})

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const playSegment = () => {
  emit('play', props.segment.start_time)
}

const handleClick = () => {
  emit('click', props.segment)
}

const saveEdit = () => {
  emit('update', props.segment.id, { text: editText.value })
  isEditing.value = false
}

const cancelEdit = () => {
  editText.value = props.segment.text
  isEditing.value = false
}
</script>

<style scoped>
.segment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.segment-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-range {
  font-size: 12px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

.segment-actions {
  display: flex;
  gap: 8px;
}

.segment-content {
  margin-top: 8px;
}

.text-content {
  margin: 0 0 8px 0;
  line-height: 1.6;
  color: #303133;
}

.ipa-section {
  background: #f0f9eb;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.ipa-label {
  font-size: 12px;
  color: #67c23a;
  font-weight: 600;
  margin-right: 8px;
}

.variants-section {
  margin-top: 8px;
}

.variants-label {
  font-size: 12px;
  color: #e6a23c;
  font-weight: 600;
  margin-bottom: 4px;
}

.variants-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.variant-ipa {
  font-size: 10px;
  opacity: 0.8;
  margin-left: 2px;
}

.segment-edit {
  margin-top: 8px;
}

.edit-actions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>

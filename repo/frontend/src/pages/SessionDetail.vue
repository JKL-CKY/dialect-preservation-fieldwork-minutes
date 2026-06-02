<template>
  <div class="session-detail">
    <el-row :gutter="20">
      <el-col :span="16">
        <AudioPlayer
          ref="audioPlayerRef"
          :audio-url="audioUrl"
          @timeupdate="onTimeUpdate"
          @ready="onAudioReady"
        />

        <el-card class="transcriptions-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20" color="#409eff">
                <Document />
              </el-icon>
              <span>转写结果</span>
              <el-tag type="info" size="small">{{ segments.length }} 个片段</el-tag>
            </div>
          </template>

          <div class="transcriptions-list">
            <TranscriptionSegment
              v-for="segment in segments"
              :key="segment.id"
              :segment="segment"
              :current-time="currentTime"
              @play="playSegment"
              @update="updateSegment"
              @click="onSegmentClick"
            />
            <el-empty v-if="segments.length === 0" description="暂无转写结果" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="speakers-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20" color="#67c23a">
                <UserFilled />
              </el-icon>
              <span>说话人信息</span>
            </div>
          </template>

          <div class="speakers-list">
            <div
              v-for="speaker in speakers"
              :key="speaker.id"
              class="speaker-item"
            >
              <div class="speaker-avatar">
                <el-avatar :size="48" :style="{ background: speaker.role === 'informant' ? '#409eff' : '#67c23a' }">
                  {{ speaker.name.charAt(0) }}
                </el-avatar>
              </div>
              <div class="speaker-info">
                <div class="speaker-name">
                  {{ speaker.name }}
                  <el-tag size="small" :type="speaker.role === 'informant' ? 'primary' : 'success'">
                    {{ speaker.role === 'informant' ? '发音人' : '研究员' }}
                  </el-tag>
                </div>
                <div v-if="speaker.dialect" class="speaker-detail">
                  方言：{{ speaker.dialect }}
                </div>
                <div v-if="speaker.region" class="speaker-detail">
                  地区：{{ speaker.region }}
                </div>
                <div v-if="speaker.age" class="speaker-detail">
                  年龄：{{ speaker.age }}岁
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <DiscussionPanel
          :messages="discussionMessages"
          @send="sendDiscussionMessage"
          @jumpToSegment="jumpToSegment"
          class="discussion-wrapper"
        />

        <el-card class="actions-card">
          <el-button type="primary" size="large" style="width: 100%" @click="generateReport">
            <el-icon><DocumentAdd /></el-icon>
            生成方言特征报告
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, UserFilled, DocumentAdd } from '@element-plus/icons-vue'
import AudioPlayer from '@/components/AudioPlayer.vue'
import TranscriptionSegment from '@/components/TranscriptionSegment.vue'
import DiscussionPanel from '@/components/DiscussionPanel.vue'
import {
  getTranscriptions,
  getSpeakers,
  getDiscussionMessages,
  sendDiscussionMessage as sendMessage,
  updateTranscription,
  generateReport as genReport,
  getAudioUrl
} from '@/services/api'
import type { TranscriptionSegment as TranscriptionSegmentType, Speaker, DiscussionMessage } from '@/types'

const route = useRoute()
const router = useRouter()
const audioPlayerRef = ref<InstanceType<typeof AudioPlayer> | null>(null)
const sessionId = ref('')
const segments = ref<TranscriptionSegmentType[]>([])
const speakers = ref<Speaker[]>([])
const discussionMessages = ref<DiscussionMessage[]>([])
const currentTime = ref(0)
const audioDuration = ref(0)

const audioUrl = ref('')

const loadData = async () => {
  const sid = route.params.sessionId as string
  sessionId.value = sid
  audioUrl.value = getAudioUrl(sid)

  try {
    const [transRes, speakersRes, msgRes] = await Promise.all([
      getTranscriptions(sid),
      getSpeakers(sid),
      getDiscussionMessages(sid)
    ])
    segments.value = transRes.data
    speakers.value = speakersRes.data
    discussionMessages.value = msgRes.data
  } catch (error) {
    ElMessage.error('加载数据失败')
  }
}

const onTimeUpdate = (time: number) => {
  currentTime.value = time
}

const onAudioReady = (duration: number) => {
  audioDuration.value = duration
}

const playSegment = (startTime: number) => {
  audioPlayerRef.value?.seekTo(startTime)
  audioPlayerRef.value?.togglePlay()
}

const onSegmentClick = (segment: TranscriptionSegmentType) => {
  audioPlayerRef.value?.seekTo(segment.start_time)
}

const updateSegment = async (segmentId: string, data: Partial<TranscriptionSegmentType>) => {
  try {
    await updateTranscription(sessionId.value, segmentId, data)
    const index = segments.value.findIndex(s => s.id === segmentId)
    if (index !== -1) {
      segments.value[index] = { ...segments.value[index], ...data }
    }
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

const sendDiscussionMessage = async (content: string) => {
  try {
    const response = await sendMessage(sessionId.value, {
      session_id: sessionId.value,
      user_id: 'current-user',
      user_name: '研究员',
      user_role: 'researcher',
      content,
      annotations: []
    })
    discussionMessages.value.push(response.data)
  } catch (error) {
    ElMessage.error('发送失败')
  }
}

const jumpToSegment = (segmentId: string) => {
  const segment = segments.value.find(s => s.id === segmentId)
  if (segment) {
    audioPlayerRef.value?.seekTo(segment.start_time)
  }
}

const generateReport = async () => {
  try {
    const response = await genReport(sessionId.value)
    ElMessage.success('报告生成成功！')
    router.push(`/report/${response.data.id}`)
  } catch (error) {
    ElMessage.error('报告生成失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.session-detail {
  max-width: 1600px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.transcriptions-card {
  margin-top: 20px;
}

.transcriptions-list {
  max-height: 600px;
  overflow-y: auto;
}

.speakers-card,
.discussion-wrapper,
.actions-card {
  margin-bottom: 20px;
}

.speakers-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.speaker-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.speaker-info {
  flex: 1;
}

.speaker-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.speaker-detail {
  font-size: 13px;
  color: #606266;
  margin-bottom: 2px;
}

.discussion-wrapper {
  height: 500px;
}
</style>

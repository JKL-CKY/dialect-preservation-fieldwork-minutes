<template>
  <div class="home-page">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20" color="#409eff">
                <UploadFilled />
              </el-icon>
              <span>上传田野调查录音</span>
            </div>
          </template>

          <el-form :model="uploadForm" label-width="100px">
            <el-form-item label="方言名称" required>
              <el-input v-model="uploadForm.dialect" placeholder="例如：闽南语、粤语、湘语" />
            </el-form-item>
            <el-form-item label="调查地区" required>
              <el-input v-model="uploadForm.region" placeholder="例如：福建省泉州市" />
            </el-form-item>
            <el-form-item label="录音文件" required>
              <el-upload
                ref="uploadRef"
                class="audio-uploader"
                drag
                :auto-upload="false"
                :on-change="handleFileChange"
                :limit="1"
                accept="audio/*"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  将录音文件拖到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 MP3、WAV、M4A 等常见音频格式，文件大小不超过 500MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="isUploading"
                :disabled="!canUpload"
                @click="handleUpload"
              >
                <el-icon><Upload /></el-icon>
                开始上传并处理
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="24" v-if="processingStatus">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20" :color="statusColor">
                <Loading v-if="isProcessing" />
                <CircleCheck v-else-if="processingStatus.status === 'completed'" />
                <CircleClose v-else />
              </el-icon>
              <span>处理进度</span>
            </div>
          </template>

          <el-steps :active="currentStep" finish-status="success" align-center>
            <el-step title="上传录音" description="上传田野调查录音文件" />
            <el-step title="说话人分离" description="pyannote 区分发音人和研究者" />
            <el-step title="语音转写" description="Whisper 方言微调转写" />
            <el-step title="语法分析" description="spaCy 标注语法变异点" />
            <el-step title="生成报告" description="OpenAI 生成方言特征报告" />
          </el-steps>

          <div class="progress-info">
            <el-progress
              :percentage="processingStatus.progress"
              :status="processingStatus.status === 'error' ? 'exception' : undefined"
            />
            <p class="status-message">{{ processingStatus.message }}</p>
          </div>

          <div v-if="processingStatus.status === 'completed'" class="action-buttons">
            <el-button type="primary" size="large" @click="goToSession">
              <el-icon><View /></el-icon>
              查看转写结果
            </el-button>
            <el-button size="large" @click="generateReport">
              <el-icon><Document /></el-icon>
              生成方言报告
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="24">
        <el-card class="features-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20" color="#67c23a">
                <MagicStick />
              </el-icon>
              <span>系统功能</span>
            </div>
          </template>

          <el-row :gutter="20">
            <el-col :span="8">
              <div class="feature-item">
                <el-icon :size="32" color="#409eff"><Microphone /></el-icon>
                <h4>专业录音播放</h4>
                <p>支持波形显示、变速播放、段落跳转等专业功能</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <el-icon :size="32" color="#67c23a"><Collection /></el-icon>
                <h4>国际音标显示</h4>
                <p>自动生成 IPA 国际音标转写，支持方言特殊音标</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <el-icon :size="32" color="#e6a23c"><User /></el-icon>
                <h4>说话人分离</h4>
                <p>基于 pyannote 自动区分发音人和研究者身份</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <el-icon :size="32" color="#f56c6c"><Edit /></el-icon>
                <h4>语法变异标注</h4>
                <p>spaCy 自动识别并标注方言语法变异点</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <el-icon :size="32" color="#909399"><ChatDotRound /></el-icon>
                <h4>团队讨论协作</h4>
                <p>支持语言学团队在线讨论和标注修正</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <el-icon :size="32" color="#722ed1"><DataAnalysis /></el-icon>
                <h4>濒危等级评估</h4>
                <p>基于 UNESCO 标准自动评估方言濒危等级</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  UploadFilled, Upload, Loading, CircleCheck, CircleClose, View, Document,
  MagicStick, Microphone, Collection, User, Edit, ChatDotRound, DataAnalysis
} from '@element-plus/icons-vue'
import { uploadAudio, getProcessingStatus, startProcessing, generateReport as genReport } from '@/services/api'
import type { UploadResponse, ProcessingStatus } from '@/types'

const router = useRouter()
const uploadRef = ref()
const isUploading = ref(false)
const isProcessing = ref(false)
const uploadForm = ref({
  dialect: '',
  region: ''
})
const selectedFile = ref<File | null>(null)
const uploadResponse = ref<UploadResponse | null>(null)
const processingStatus = ref<ProcessingStatus | null>(null)
let statusPolling: number | null = null

const canUpload = computed(() => {
  return uploadForm.value.dialect.trim() && uploadForm.value.region.trim() && selectedFile.value
})

const currentStep = computed(() => {
  if (!processingStatus.value) return 0
  const steps: Record<string, number> = {
    uploading: 1,
    diarizing: 2,
    transcribing: 3,
    analyzing: 4,
    generating: 5,
    completed: 5,
    error: 0
  }
  return steps[processingStatus.value.status] || 0
})

const statusColor = computed(() => {
  if (!processingStatus.value) return '#909399'
  const colors: Record<string, string> = {
    uploading: '#409eff',
    diarizing: '#409eff',
    transcribing: '#409eff',
    analyzing: '#409eff',
    generating: '#409eff',
    completed: '#67c23a',
    error: '#f56c6c'
  }
  return colors[processingStatus.value.status] || '#909399'
})

const handleFileChange = (file: { raw: File }) => {
  selectedFile.value = file.raw
}

const handleUpload = async () => {
  if (!canUpload.value || !selectedFile.value) return

  isUploading.value = true
  try {
    const response = await uploadAudio(selectedFile.value, {
      dialect: uploadForm.value.dialect,
      region: uploadForm.value.region
    })
    uploadResponse.value = response.data
    ElMessage.success('文件上传成功，开始处理...')

    await startProcessing(response.data.session_id)
    startStatusPolling(response.data.session_id)
  } catch (error) {
    ElMessage.error('上传失败，请重试')
  } finally {
    isUploading.value = false
  }
}

const startStatusPolling = (sessionId: string) => {
  isProcessing.value = true
  const poll = async () => {
    try {
      const response = await getProcessingStatus(sessionId)
      processingStatus.value = response.data

      if (response.data.status === 'completed' || response.data.status === 'error') {
        isProcessing.value = false
        if (statusPolling) {
          clearInterval(statusPolling)
          statusPolling = null
        }
        if (response.data.status === 'completed') {
          ElMessage.success('处理完成！')
        } else {
          ElMessage.error('处理出错，请重试')
        }
        return
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }

  poll()
  statusPolling = window.setInterval(poll, 3000)
}

const goToSession = () => {
  if (uploadResponse.value) {
    router.push(`/session/${uploadResponse.value.session_id}`)
  }
}

const generateReport = async () => {
  if (!uploadResponse.value) return

  try {
    const response = await genReport(uploadResponse.value.session_id)
    ElMessage.success('报告生成成功！')
    router.push(`/report/${response.data.id}`)
  } catch (error) {
    ElMessage.error('报告生成失败')
  }
}

onUnmounted(() => {
  if (statusPolling) {
    clearInterval(statusPolling)
  }
})
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.upload-card,
.status-card,
.features-card {
  margin-bottom: 20px;
}

.audio-uploader {
  width: 100%;
}

.progress-info {
  margin-top: 24px;
  padding: 0 40px;
}

.status-message {
  text-align: center;
  margin-top: 12px;
  color: #606266;
}

.action-buttons {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.feature-item {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: #f5f7fa;
  transform: translateY(-4px);
}

.feature-item h4 {
  margin: 12px 0 8px 0;
  font-size: 16px;
  color: #303133;
}

.feature-item p {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}
</style>

<template>
  <div class="report-detail">
    <el-card v-loading="loading" class="report-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon :size="24" color="#722ed1">
              <DataAnalysis />
            </el-icon>
            <h2>{{ report?.title || '方言特征报告' }}</h2>
          </div>
          <div class="header-right">
            <EndangermentBadge
              v-if="report?.endangerment"
              :level="report.endangerment.level"
              :score="report.endangerment.score"
            />
            <el-tag :type="reportStatusType" size="large">
              {{ reportStatusText }}
            </el-tag>
          </div>
        </div>
      </template>

      <div v-if="report" class="report-content">
        <el-descriptions :column="2" border class="basic-info">
          <el-descriptions-item label="方言名称">
            {{ report.dialect_name }}
          </el-descriptions-item>
          <el-descriptions-item label="调查地区">
            {{ report.region }}
          </el-descriptions-item>
          <el-descriptions-item label="调查日期">
            {{ formatDate(report.fieldwork_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="报告生成时间">
            {{ formatDate(report.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="研究员">
            {{ report.researchers.join('、') }}
          </el-descriptions-item>
          <el-descriptions-item label="发音人">
            {{ report.informants.join('、') }}
          </el-descriptions-item>
          <el-descriptions-item label="转写片段数">
            {{ report.transcription_count }} 个
          </el-descriptions-item>
          <el-descriptions-item label="录音总时长">
            {{ formatDuration(report.total_duration) }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">
          <h3>
            <el-icon><Document /></el-icon>
            摘要
          </h3>
        </el-divider>
        <div class="summary-section">
          <p>{{ report.summary }}</p>
        </div>

        <el-divider content-position="left">
          <h3>
            <el-icon><MagicStick /></el-icon>
            方言主要特征
          </h3>
        </el-divider>
        <div class="features-section">
          <el-row :gutter="20">
            <el-col :span="12" v-for="feature in report.key_features" :key="feature.feature">
              <el-card class="feature-card" shadow="hover">
                <template #header>
                  <div class="feature-header">
                    <el-tag type="primary">{{ feature.category }}</el-tag>
                    <span class="feature-title">{{ feature.feature }}</span>
                  </div>
                </template>
                <div class="feature-examples">
                  <div class="examples-label">例示：</div>
                  <ul>
                    <li v-for="(example, idx) in feature.examples" :key="idx">
                      {{ example }}
                    </li>
                  </ul>
                </div>
                <p class="feature-notes" v-if="feature.notes">
                  <strong>说明：</strong>{{ feature.notes }}
                </p>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <el-divider content-position="left">
          <h3>
            <el-icon><Warning /></el-icon>
            濒危等级评估
          </h3>
        </el-divider>
        <div class="endangerment-section" v-if="report.endangerment">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="综合评分" :value="report.endangerment.score" suffix="/100" />
            </el-col>
            <el-col :span="16">
              <el-progress
                :percentage="report.endangerment.score"
                :color="progressColor"
                :stroke-width="20"
              />
            </el-col>
          </el-row>

          <h4 class="factors-title">评估因素</h4>
          <el-table :data="report.endangerment.factors" border>
            <el-table-column prop="name" label="评估因素" width="150" />
            <el-table-column prop="score" label="得分" width="100">
              <template #default="{ row }">
                <el-tag :type="row.score >= 70 ? 'success' : row.score >= 40 ? 'warning' : 'danger'">
                  {{ row.score }}/100
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>

          <h4 class="recommendations-title">保护建议</h4>
          <el-timeline>
            <el-timeline-item
              v-for="(rec, idx) in report.endangerment.recommendations"
              :key="idx"
              :timestamp="`建议 ${idx + 1}`"
              placement="top"
            >
              <el-card shadow="never">
                {{ rec }}
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>

        <el-divider />

        <div class="report-actions">
          <el-button size="large" @click="exportMarkdown">
            <el-icon><Download /></el-icon>
            导出 Markdown
          </el-button>
          <el-button size="large" type="primary" @click="showSubmitDialog = true">
            <el-icon><Promotion /></el-icon>
            提交至语委
          </el-button>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="showSubmitDialog"
      title="提交至语言文字工作委员会"
      width="600px"
    >
      <el-form :model="submitForm" label-width="100px">
        <el-form-item label="收件人">
          <el-select v-model="submitForm.to" multiple filterable placeholder="选择或输入收件人">
            <el-option label="国家语委" value="language-committee@gov.cn" />
            <el-option label="省语委" value="provincial-language@gov.cn" />
            <el-option label="市语委" value="city-language@gov.cn" />
          </el-select>
        </el-form-item>
        <el-form-item label="主题">
          <el-input v-model="submitForm.subject" />
        </el-form-item>
        <el-form-item label="邮件正文">
          <el-input v-model="submitForm.body" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSubmitDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitToCommittee">
          发送
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Document, MagicStick, Warning, Download, Promotion
} from '@element-plus/icons-vue'
import EndangermentBadge from '@/components/EndangermentBadge.vue'
import { getReport, exportMarkdown as exportMd, submitToCommittee as submitToComm } from '@/services/api'
import type { DialectReport, EmailSubmission } from '@/types'

const route = useRoute()
const loading = ref(false)
const submitting = ref(false)
const report = ref<DialectReport | null>(null)
const showSubmitDialog = ref(false)
const submitForm = ref<EmailSubmission>({
  to: ['language-committee@gov.cn'],
  subject: '',
  body: '',
  attachments: []
})

const reportStatusType = computed(() => {
  const types: Record<string, 'success' | 'warning' | 'info' | 'primary'> = {
    draft: 'info',
    completed: 'success',
    submitted: 'primary'
  }
  return types[report.value?.status || 'draft'] || 'info'
})

const reportStatusText = computed(() => {
  const texts: Record<string, string> = {
    draft: '草稿',
    completed: '已完成',
    submitted: '已提交'
  }
  return texts[report.value?.status || 'draft'] || '草稿'
})

const progressColor = computed(() => {
  const score = report.value?.endangerment?.score || 0
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  if (score >= 40) return '#f56c6c'
  return '#f5222d'
})

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  if (hours > 0) {
    return `${hours}小时${minutes}分${secs}秒`
  }
  return `${minutes}分${secs}秒`
}

const loadReport = async () => {
  const reportId = route.params.reportId as string
  loading.value = true
  try {
    const response = await getReport(reportId)
    report.value = response.data
    submitForm.value.subject = `【方言保护报告】${response.data.dialect_name} - ${response.data.region}`
    submitForm.value.body = `尊敬的语言文字工作委员会：\n\n现将《${response.data.title》提交至贵委，请审阅。\n\n报告摘要：\n${response.data.summary}\n\n此致\n敬礼\n\n方言保护研究中心\n${new Date().toLocaleDateString('zh-CN')}`
  } catch (error) {
    ElMessage.error('加载报告失败')
  } finally {
    loading.value = false
  }
}

const exportMarkdown = async () => {
  if (!report.value) return
  try {
    const response = await exportMd(report.value.id)
    const blob = new Blob([response.data], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.value.dialect_name}_方言报告_${new Date().toISOString().split('T')[0]}.md`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const submitToCommittee = async () => {
  if (!report.value) return
  submitting.value = true
  try {
    await submitToComm(report.value.id, submitForm.value)
    ElMessage.success('提交成功！')
    showSubmitDialog.value = false
    if (report.value) {
      report.value.status = 'submitted'
    }
  } catch (error) {
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.report-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.report-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.basic-info {
  margin-bottom: 20px;
}

.summary-section {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  line-height: 1.8;
  font-size: 15px;
}

.features-section {
  margin-bottom: 20px;
}

.feature-card {
  height: 100%;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-title {
  font-weight: 600;
  font-size: 14px;
}

.feature-examples {
  margin-bottom: 8px;
}

.examples-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.feature-examples ul {
  margin: 0;
  padding-left: 20px;
}

.feature-examples li {
  margin-bottom: 4px;
  color: #606266;
}

.feature-notes {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.endangerment-section {
  margin-bottom: 20px;
}

.factors-title,
.recommendations-title {
  margin: 20px 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.report-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 20px 0;
}

h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
}
</style>

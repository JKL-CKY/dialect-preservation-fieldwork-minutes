import axios from 'axios'
import type {
  UploadResponse,
  ProcessingStatus,
  TranscriptionSegment,
  DialectReport,
  DiscussionMessage,
  EmailSubmission,
  Speaker
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000
})

export const uploadAudio = (file: File, dialectInfo: { dialect: string; region: string }) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('dialect', dialectInfo.dialect)
  formData.append('region', dialectInfo.region)
  return api.post<UploadResponse>('/audio/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getProcessingStatus = (sessionId: string) => {
  return api.get<ProcessingStatus>(`/processing/status/${sessionId}`)
}

export const startProcessing = (sessionId: string) => {
  return api.post<ProcessingStatus>('/processing/start', { session_id: sessionId })
}

export const getTranscriptions = (sessionId: string) => {
  return api.get<TranscriptionSegment[]>(`/transcriptions/${sessionId}`)
}

export const updateTranscription = (sessionId: string, segmentId: string, data: Partial<TranscriptionSegment>) => {
  return api.put(`/transcriptions/${sessionId}/${segmentId}`, data)
}

export const getSpeakers = (sessionId: string) => {
  return api.get<Speaker[]>(`/speakers/${sessionId}`)
}

export const updateSpeaker = (sessionId: string, speakerId: string, data: Partial<Speaker>) => {
  return api.put(`/speakers/${sessionId}/${speakerId}`, data)
}

export const getDiscussionMessages = (sessionId: string) => {
  return api.get<DiscussionMessage[]>(`/discussion/${sessionId}`)
}

export const sendDiscussionMessage = (sessionId: string, message: Omit<DiscussionMessage, 'id' | 'timestamp'>) => {
  return api.post<DiscussionMessage>(`/discussion/${sessionId}`, message)
}

export const generateReport = (sessionId: string) => {
  return api.post<DialectReport>(`/report/generate`, { session_id: sessionId })
}

export const getReport = (reportId: string) => {
  return api.get<DialectReport>(`/report/${reportId}`)
}

export const submitToCommittee = (reportId: string, submission: EmailSubmission) => {
  return api.post(`/report/${reportId}/submit`, submission)
}

export const exportMarkdown = (reportId: string) => {
  return api.get<string>(`/report/${reportId}/markdown`)
}

export const getAudioUrl = (sessionId: string) => {
  return `/api/audio/stream/${sessionId}`
}

export default api

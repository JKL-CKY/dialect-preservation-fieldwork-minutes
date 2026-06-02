export interface Speaker {
  id: string
  name: string
  role: 'informant' | 'researcher'
  dialect?: string
  region?: string
  age?: number
  gender?: string
}

export interface TranscriptionSegment {
  id: string
  start_time: number
  end_time: number
  speaker_id: string
  speaker_name: string
  speaker_role: 'informant' | 'researcher'
  text: string
  ipa_transcription: string
  grammar_variants: GrammarVariant[]
  confidence: number
}

export interface GrammarVariant {
  token: string
  standard_form: string
  variant_type: string
  description: string
  ipa: string
  position: [number, number]
}

export interface DialectFeature {
  category: string
  feature: string
  examples: string[]
  notes: string
}

export interface EndangermentAssessment {
  level: 'safe' | 'vulnerable' | 'definitely' | 'severely' | 'critically' | 'extinct'
  score: number
  factors: {
    name: string
    score: number
    description: string
  }[]
  recommendations: string[]
}

export interface DialectReport {
  id: string
  title: string
  dialect_name: string
  region: string
  fieldwork_date: string
  researchers: string[]
  informants: string[]
  summary: string
  key_features: DialectFeature[]
  endangerment: EndangermentAssessment
  transcription_count: number
  total_duration: number
  created_at: string
  status: 'draft' | 'completed' | 'submitted'
}

export interface UploadResponse {
  session_id: string
  filename: string
  file_size: number
  upload_time: string
}

export interface ProcessingStatus {
  session_id: string
  status: 'uploading' | 'diarizing' | 'transcribing' | 'analyzing' | 'generating' | 'completed' | 'error'
  progress: number
  message: string
  current_step: string
}

export interface DiscussionMessage {
  id: string
  session_id: string
  user_id: string
  user_name: string
  user_role: string
  content: string
  timestamp: string
  segment_ref?: string
  annotations: Annotation[]
}

export interface Annotation {
  type: 'comment' | 'correction' | 'question' | 'highlight'
  text: string
  author: string
  timestamp: string
}

export interface EmailSubmission {
  to: string[]
  subject: string
  body: string
  attachments: {
    filename: string
    content: string
  }[]
}

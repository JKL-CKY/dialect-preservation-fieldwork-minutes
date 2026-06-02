from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class GrammarVariant(BaseModel):
    token: str
    standard_form: str
    variant_type: str
    description: str
    ipa: str
    position: List[float]


class SpeakerBase(BaseModel):
    name: str = "未命名说话人"
    role: str = "informant"
    dialect: Optional[str] = None
    region: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


class SpeakerCreate(SpeakerBase):
    pyannote_label: str
    session_id: str


class SpeakerUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    dialect: Optional[str] = None
    region: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None


class Speaker(SpeakerBase):
    id: str
    pyannote_label: str

    class Config:
        from_attributes = True


class TranscriptionBase(BaseModel):
    start_time: float
    end_time: float
    text: str
    ipa_transcription: Optional[str] = None
    grammar_variants: List[GrammarVariant] = Field(default_factory=list)
    confidence: float = 1.0


class TranscriptionCreate(TranscriptionBase):
    session_id: str
    speaker_id: Optional[str] = None


class TranscriptionUpdate(BaseModel):
    text: Optional[str] = None
    ipa_transcription: Optional[str] = None
    grammar_variants: Optional[List[GrammarVariant]] = None


class TranscriptionSegment(TranscriptionBase):
    id: str
    speaker_id: Optional[str] = None
    speaker_name: str = "未知说话人"
    speaker_role: str = "informant"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Annotation(BaseModel):
    type: str
    text: str
    author: str
    timestamp: datetime


class DiscussionMessageBase(BaseModel):
    user_id: str
    user_name: str
    user_role: str
    content: str
    segment_ref: Optional[str] = None
    annotations: List[Annotation] = Field(default_factory=list)


class DiscussionMessageCreate(DiscussionMessageBase):
    session_id: str


class DiscussionMessage(DiscussionMessageBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class EndangermentFactor(BaseModel):
    name: str
    score: float
    description: str


class EndangermentAssessment(BaseModel):
    level: str
    score: float
    factors: List[EndangermentFactor] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class DialectFeature(BaseModel):
    category: str
    feature: str
    examples: List[str] = Field(default_factory=list)
    notes: str = ""


class ReportBase(BaseModel):
    title: str
    dialect_name: str
    region: str
    fieldwork_date: datetime
    researchers: List[str] = Field(default_factory=list)
    informants: List[str] = Field(default_factory=list)
    summary: str = ""
    key_features: List[DialectFeature] = Field(default_factory=list)
    endangerment: Optional[EndangermentAssessment] = None
    status: str = "draft"


class ReportCreate(ReportBase):
    session_id: str


class Report(ReportBase):
    id: str
    session_id: str
    transcription_count: int = 0
    total_duration: float = 0.0
    created_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    file_size: int
    upload_time: datetime


class ProcessingStatus(BaseModel):
    session_id: str
    status: str
    progress: float
    message: str
    current_step: str


class ProcessingStartRequest(BaseModel):
    session_id: str


class ReportGenerateRequest(BaseModel):
    session_id: str


class EmailAttachment(BaseModel):
    filename: str
    content: str


class EmailSubmission(BaseModel):
    to: List[str]
    subject: str
    body: str
    attachments: List[EmailAttachment] = Field(default_factory=list)

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    filename = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Integer)
    dialect = Column(String)
    region = Column(String)
    status = Column(String, default="uploading")
    progress = Column(Float, default=0)
    current_step = Column(String, default="")
    error_message = Column(Text, nullable=True)
    total_duration = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    speakers = relationship("Speaker", back_populates="session", cascade="all, delete-orphan")
    transcriptions = relationship("Transcription", back_populates="session", cascade="all, delete-orphan")
    discussions = relationship("DiscussionMessage", back_populates="session", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Speaker(Base):
    __tablename__ = "speakers"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"))
    name = Column(String, default="未命名说话人")
    role = Column(String, default="informant")
    dialect = Column(String, nullable=True)
    region = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    pyannote_label = Column(String)

    session = relationship("Session", back_populates="speakers")
    transcriptions = relationship("Transcription", back_populates="speaker")


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"))
    speaker_id = Column(String, ForeignKey("speakers.id"), nullable=True)
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(Text)
    ipa_transcription = Column(Text, nullable=True)
    grammar_variants = Column(JSON, default=list)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    session = relationship("Session", back_populates="transcriptions")
    speaker = relationship("Speaker", back_populates="transcriptions")


class DiscussionMessage(Base):
    __tablename__ = "discussion_messages"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"))
    user_id = Column(String)
    user_name = Column(String)
    user_role = Column(String)
    content = Column(Text)
    segment_ref = Column(String, nullable=True)
    annotations = Column(JSON, default=list)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="discussions")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("sessions.id"))
    title = Column(String)
    dialect_name = Column(String)
    region = Column(String)
    fieldwork_date = Column(DateTime)
    researchers = Column(JSON, default=list)
    informants = Column(JSON, default=list)
    summary = Column(Text)
    key_features = Column(JSON, default=list)
    endangerment = Column(JSON, default=dict)
    status = Column(String, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("Session", back_populates="report")

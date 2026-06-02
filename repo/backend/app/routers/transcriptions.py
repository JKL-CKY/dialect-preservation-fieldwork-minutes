from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Transcription
from app.schemas import TranscriptionSegment, TranscriptionUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])


@router.get("/{session_id}", response_model=List[TranscriptionSegment])
async def get_transcriptions(
    session_id: str,
    db: Session = Depends(get_db)
):
    transcriptions = db.query(Transcription).filter(
        Transcription.session_id == session_id
    ).order_by(Transcription.start_time).all()

    result = []
    for t in transcriptions:
        segment = TranscriptionSegment(
            id=t.id,
            start_time=t.start_time,
            end_time=t.end_time,
            speaker_id=t.speaker_id,
            speaker_name=t.speaker.name if t.speaker else "未知说话人",
            speaker_role=t.speaker.role if t.speaker else "informant",
            text=t.text,
            ipa_transcription=t.ipa_transcription or "",
            grammar_variants=t.grammar_variants or [],
            confidence=t.confidence,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        result.append(segment)

    return result


@router.put("/{session_id}/{segment_id}")
async def update_transcription(
    session_id: str,
    segment_id: str,
    update_data: TranscriptionUpdate,
    db: Session = Depends(get_db)
):
    transcription = db.query(Transcription).filter(
        Transcription.id == segment_id,
        Transcription.session_id == session_id
    ).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="转写片段不存在")

    if update_data.text is not None:
        transcription.text = update_data.text
    if update_data.ipa_transcription is not None:
        transcription.ipa_transcription = update_data.ipa_transcription
    if update_data.grammar_variants is not None:
        transcription.grammar_variants = [v.dict() for v in update_data.grammar_variants]

    db.commit()
    db.refresh(transcription)

    logger.info(f"Transcription updated: {segment_id}")

    return {"message": "更新成功", "id": segment_id}

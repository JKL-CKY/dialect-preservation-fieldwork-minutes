from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Speaker
from app.schemas import Speaker as SpeakerSchema, SpeakerUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speakers", tags=["speakers"])


@router.get("/{session_id}", response_model=List[SpeakerSchema])
async def get_speakers(
    session_id: str,
    db: Session = Depends(get_db)
):
    speakers = db.query(Speaker).filter(
        Speaker.session_id == session_id
    ).all()

    return [
        SpeakerSchema(
            id=s.id,
            name=s.name,
            role=s.role,
            dialect=s.dialect,
            region=s.region,
            age=s.age,
            gender=s.gender,
            pyannote_label=s.pyannote_label
        )
        for s in speakers
    ]


@router.put("/{session_id}/{speaker_id}", response_model=SpeakerSchema)
async def update_speaker(
    session_id: str,
    speaker_id: str,
    update_data: SpeakerUpdate,
    db: Session = Depends(get_db)
):
    speaker = db.query(Speaker).filter(
        Speaker.id == speaker_id,
        Speaker.session_id == session_id
    ).first()

    if not speaker:
        raise HTTPException(status_code=404, detail="说话人不存在")

    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(speaker, key, value)

    db.commit()
    db.refresh(speaker)

    logger.info(f"Speaker updated: {speaker_id}")

    return SpeakerSchema(
        id=speaker.id,
        name=speaker.name,
        role=speaker.role,
        dialect=speaker.dialect,
        region=speaker.region,
        age=speaker.age,
        gender=speaker.gender,
        pyannote_label=speaker.pyannote_label
    )

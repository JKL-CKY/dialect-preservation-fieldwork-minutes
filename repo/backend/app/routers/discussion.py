from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import DiscussionMessage
from app.schemas import DiscussionMessage as DiscussionMessageSchema, DiscussionMessageCreate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discussion", tags=["discussion"])


@router.get("/{session_id}", response_model=List[DiscussionMessageSchema])
async def get_discussion_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    messages = db.query(DiscussionMessage).filter(
        DiscussionMessage.session_id == session_id
    ).order_by(DiscussionMessage.timestamp).all()

    return [
        DiscussionMessageSchema(
            id=m.id,
            session_id=m.session_id,
            user_id=m.user_id,
            user_name=m.user_name,
            user_role=m.user_role,
            content=m.content,
            segment_ref=m.segment_ref,
            annotations=m.annotations or [],
            timestamp=m.timestamp
        )
        for m in messages
    ]


@router.post("/{session_id}", response_model=DiscussionMessageSchema)
async def send_discussion_message(
    session_id: str,
    message_data: DiscussionMessageCreate,
    db: Session = Depends(get_db)
):
    message = DiscussionMessage(
        session_id=session_id,
        user_id=message_data.user_id,
        user_name=message_data.user_name,
        user_role=message_data.user_role,
        content=message_data.content,
        segment_ref=message_data.segment_ref,
        annotations=[a.dict() for a in message_data.annotations] if message_data.annotations else []
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    logger.info(f"Discussion message sent: {message.id}")

    return DiscussionMessageSchema(
        id=message.id,
        session_id=message.session_id,
        user_id=message.user_id,
        user_name=message.user_name,
        user_role=message.user_role,
        content=message.content,
        segment_ref=message.segment_ref,
        annotations=message.annotations or [],
        timestamp=message.timestamp
    )

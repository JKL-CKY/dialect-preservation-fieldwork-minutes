from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Session as DBSession
from app.schemas import ProcessingStatus, ProcessingStartRequest
from app.services.processing_service import processing_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/start", response_model=ProcessingStatus)
async def start_processing(
    request: ProcessingStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session_id = request.session_id
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()

    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if db_session.status in ["diarizing", "transcribing", "analyzing", "generating"]:
        raise HTTPException(status_code=400, detail="处理正在进行中")

    if db_session.status == "completed":
        return ProcessingStatus(
            session_id=session_id,
            status="completed",
            progress=100,
            message="处理已完成",
            current_step="处理完成！"
        )

    background_tasks.add_task(
        processing_service.process_session,
        session_id,
        db_session.file_path,
        db_session.dialect,
        db_session.region,
        db
    )

    db_session.status = "diarizing"
    db_session.progress = 10
    db_session.current_step = "正在进行说话人分离..."
    db.commit()

    logger.info(f"Processing started for session: {session_id}")

    return ProcessingStatus(
        session_id=session_id,
        status=db_session.status,
        progress=db_session.progress,
        message=db_session.current_step,
        current_step=db_session.current_step
    )


@router.get("/status/{session_id}", response_model=ProcessingStatus)
async def get_processing_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    status = processing_service.get_processing_status(session_id, db)

    if status["status"] == "not_found":
        raise HTTPException(status_code=404, detail=status["message"])

    return ProcessingStatus(**status)

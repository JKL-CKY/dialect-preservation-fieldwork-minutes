from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Session as DBSession
from app.schemas import UploadResponse
from app.services.processing_service import processing_service
import os
import aiofiles
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=UploadResponse)
async def upload_audio(
    file: UploadFile = File(...),
    dialect: str = Form(...),
    region: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

        file_extension = os.path.splitext(file.filename)[1] if file.filename else ".wav"
        filename = f"{session_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        file_size = os.path.getsize(file_path)

        db_session = DBSession(
            id=session_id,
            filename=file.filename or filename,
            file_path=file_path,
            file_size=file_size,
            dialect=dialect,
            region=region,
            status="uploading",
            progress=0
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        logger.info(f"Audio uploaded successfully: {session_id}, size: {file_size} bytes")

        return UploadResponse(
            session_id=session_id,
            filename=file.filename or filename,
            file_size=file_size,
            upload_time=datetime.now()
        )

    except Exception as e:
        logger.error(f"Audio upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/stream/{session_id}")
async def stream_audio(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if not os.path.exists(db_session.file_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    return FileResponse(
        db_session.file_path,
        media_type="audio/mpeg",
        filename=db_session.filename
    )

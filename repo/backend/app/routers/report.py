from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Report, Session as DBSession
from app.schemas import (
    Report as ReportSchema,
    ReportGenerateRequest,
    EmailSubmission,
    DialectFeature,
    EndangermentAssessment
)
from app.services.processing_service import processing_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])


@router.post("/generate", response_model=ReportSchema)
async def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db)
):
    session_id = request.session_id

    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if db_session.status != "completed":
        raise HTTPException(status_code=400, detail="会话处理尚未完成")

    existing_report = db.query(Report).filter(Report.session_id == session_id).first()
    if existing_report:
        logger.info(f"Returning existing report for session: {session_id}")
        return _report_to_schema(existing_report, db_session)

    report = await processing_service.generate_report(session_id, db)

    if not report:
        raise HTTPException(status_code=500, detail="报告生成失败")

    logger.info(f"Report generated successfully: {report.id}")
    return _report_to_schema(report, db_session)


@router.get("/{report_id}", response_model=ReportSchema)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    db_session = db.query(DBSession).filter(DBSession.id == report.session_id).first()
    return _report_to_schema(report, db_session)


@router.get("/{report_id}/markdown")
async def export_report_markdown(
    report_id: str,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    markdown = processing_service.generate_report_markdown(report)

    return markdown


@router.post("/{report_id}/submit")
async def submit_report_to_committee(
    report_id: str,
    submission: EmailSubmission,
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    success = await processing_service.submit_report_to_committee(
        report,
        to_emails=submission.to,
        subject=submission.subject,
        body=submission.body,
        db=db
    )

    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")

    logger.info(f"Report submitted to committee: {report_id}")

    return {
        "message": "提交成功",
        "report_id": report_id,
        "recipients": submission.to,
        "submitted_at": report.submitted_at.isoformat() if report.submitted_at else None
    }


def _report_to_schema(report: Report, db_session: DBSession = None) -> ReportSchema:
    transcription_count = len(db_session.transcriptions) if db_session else 0
    total_duration = db_session.total_duration if db_session else 0.0

    key_features = [
        DialectFeature(
            category=f.get("category", ""),
            feature=f.get("feature", ""),
            examples=f.get("examples", []),
            notes=f.get("notes", "")
        )
        for f in report.key_features or []
    ]

    endangerment = None
    if report.endangerment:
        endangerment = EndangermentAssessment(
            level=report.endangerment.get("level", ""),
            score=report.endangerment.get("score", 0),
            factors=report.endangerment.get("factors", []),
            recommendations=report.endangerment.get("recommendations", [])
        )

    return ReportSchema(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        dialect_name=report.dialect_name,
        region=report.region,
        fieldwork_date=report.fieldwork_date,
        researchers=report.researchers or [],
        informants=report.informants or [],
        summary=report.summary or "",
        key_features=key_features,
        endangerment=endangerment,
        status=report.status,
        transcription_count=transcription_count,
        total_duration=total_duration,
        created_at=report.created_at,
        submitted_at=report.submitted_at
    )

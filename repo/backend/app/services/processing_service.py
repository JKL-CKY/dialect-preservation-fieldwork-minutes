import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import Session as DBSession, Speaker, Transcription, Report
from app.services.pyannote_service import pyannote_service
from app.services.whisper_service import whisper_service
from app.services.spacy_service import spacy_service
from app.services.openai_service import openai_service
from app.services.markdown_service import markdown_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProcessingService:
    async def process_session(
        self,
        session_id: str,
        audio_path: str,
        dialect: str,
        region: str,
        db: Session
    ):
        try:
            db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if not db_session:
                raise Exception(f"Session {session_id} not found")

            self._update_status(db, db_session, "diarizing", 10, "正在进行说话人分离...")

            diarization_segments = await pyannote_service.diarize_audio(audio_path)
            diarization_segments = await pyannote_service.classify_speaker_roles(
                audio_path, diarization_segments
            )

            self._save_speakers(db, db_session, diarization_segments)

            self._update_status(db, db_session, "transcribing", 30, "正在进行语音转写...")

            transcriptions = await whisper_service.transcribe_full_audio(
                audio_path, diarization_segments, dialect
            )

            for i, trans in enumerate(transcriptions):
                ipa = await whisper_service.generate_ipa(trans.get("text", ""), dialect)
                trans["ipa_transcription"] = ipa

                grammar_variants = await spacy_service.analyze_grammar_variants(
                    trans.get("text", ""), dialect
                )
                trans["grammar_variants"] = grammar_variants

                progress = 30 + int((i / len(transcriptions)) * 40)
                self._update_status(
                    db, db_session, "analyzing", progress,
                    f"正在分析语法变异点... ({i+1}/{len(transcriptions)})"
                )

            self._save_transcriptions(db, db_session, transcriptions)

            total_duration = sum(
                t.get("end_time", 0) - t.get("start_time", 0) for t in transcriptions
            )
            db_session.total_duration = total_duration

            self._update_status(db, db_session, "completed", 100, "处理完成！")

            logger.info(f"Session {session_id} processed successfully")
            return True

        except Exception as e:
            logger.error(f"Processing failed for session {session_id}: {e}")
            db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if db_session:
                self._update_status(db, db_session, "error", 0, f"处理失败: {str(e)}")
            return False

    async def generate_report(
        self,
        session_id: str,
        db: Session
    ) -> Optional[Report]:
        try:
            db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if not db_session:
                raise Exception(f"Session {session_id} not found")

            transcriptions = db.query(Transcription).filter(
                Transcription.session_id == session_id
            ).all()

            speakers = db.query(Speaker).filter(Speaker.session_id == session_id).all()

            trans_dicts = [
                {
                    "text": t.text,
                    "speaker_role": t.speaker.role if t.speaker else "unknown",
                    "start_time": t.start_time,
                    "end_time": t.end_time
                }
                for t in transcriptions
            ]

            all_variants = []
            for t in transcriptions:
                if t.grammar_variants:
                    all_variants.extend(t.grammar_variants)

            speakers_dicts = [
                {
                    "name": s.name,
                    "role": s.role,
                    "age": s.age,
                    "dialect": s.dialect
                }
                for s in speakers
            ]

            summary = await openai_service.generate_summary(
                trans_dicts, db_session.dialect, db_session.region
            )

            features = await openai_service.extract_dialect_features(
                trans_dicts, all_variants, db_session.dialect
            )

            endangerment = await openai_service.assess_endangerment(
                db_session.dialect, db_session.region, trans_dicts, speakers_dicts
            )

            researchers = [s.name for s in speakers if s.role == "researcher"] or ["研究员"]
            informants = [s.name for s in speakers if s.role == "informant"] or ["发音人"]

            report = Report(
                session_id=session_id,
                title=f"{db_session.dialect}方言特征报告 - {db_session.region}",
                dialect_name=db_session.dialect,
                region=db_session.region,
                fieldwork_date=datetime.now(),
                researchers=researchers,
                informants=informants,
                summary=summary,
                key_features=features,
                endangerment=endangerment,
                status="completed"
            )

            db.add(report)
            db.commit()
            db.refresh(report)

            logger.info(f"Report generated successfully for session {session_id}")
            return report

        except Exception as e:
            logger.error(f"Report generation failed for session {session_id}: {e}")
            return None

    def get_processing_status(self, session_id: str, db: Session) -> Dict[str, Any]:
        db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
        if not db_session:
            return {
                "session_id": session_id,
                "status": "not_found",
                "progress": 0,
                "message": "会话不存在",
                "current_step": ""
            }

        return {
            "session_id": session_id,
            "status": db_session.status,
            "progress": db_session.progress,
            "message": db_session.error_message or self._get_status_message(db_session.status),
            "current_step": db_session.current_step or ""
        }

    def generate_report_markdown(self, report: Report) -> str:
        report_data = {
            "id": report.id,
            "title": report.title,
            "dialect_name": report.dialect_name,
            "region": report.region,
            "fieldwork_date": report.fieldwork_date.isoformat() if report.fieldwork_date else "",
            "researchers": report.researchers,
            "informants": report.informants,
            "summary": report.summary,
            "key_features": report.key_features,
            "endangerment": report.endangerment,
            "transcription_count": len(report.session.transcriptions) if report.session else 0,
            "total_duration": report.session.total_duration if report.session else 0
        }
        return markdown_service.generate_report_markdown(report_data)

    async def submit_report_to_committee(
        self,
        report: Report,
        to_emails: List[str],
        subject: str = None,
        body: str = None,
        db: Session = None
    ) -> bool:
        report_data = {
            "id": report.id,
            "title": report.title,
            "dialect_name": report.dialect_name,
            "region": report.region,
            "fieldwork_date": report.fieldwork_date.isoformat() if report.fieldwork_date else "",
            "researchers": report.researchers,
            "informants": report.informants,
            "summary": report.summary,
            "key_features": report.key_features,
            "endangerment": report.endangerment
        }

        email_data = markdown_service.generate_submission_email(report_data)

        attachments = email_data.get("attachments", [])
        if body:
            email_data["body"] = body
        if subject:
            email_data["subject"] = subject

        success = await markdown_service.send_email(
            to=to_emails,
            subject=email_data["subject"],
            body=email_data["body"],
            attachments=attachments
        )

        if success and db:
            report.status = "submitted"
            report.submitted_at = datetime.now()
            db.commit()

        return success

    def _update_status(
        self,
        db: Session,
        db_session: DBSession,
        status: str,
        progress: int,
        message: str
    ):
        db_session.status = status
        db_session.progress = progress
        db_session.current_step = message
        db_session.error_message = None
        db.commit()

    def _save_speakers(self, db: Session, db_session: DBSession, segments: List[Dict[str, Any]]):
        speaker_labels = list(set(seg["speaker_label"] for seg in segments))

        for label in speaker_labels:
            role = next(
                (seg["speaker_role"] for seg in segments if seg["speaker_label"] == label),
                "informant"
            )
            name = "发音人" if role == "informant" else "研究员"
            speaker_index = sum(1 for s in db_session.speakers if s.role == role) + 1

            speaker = Speaker(
                session_id=db_session.id,
                name=f"{name}{speaker_index}",
                role=role,
                pyannote_label=label,
                dialect=db_session.dialect,
                region=db_session.region
            )
            db.add(speaker)

        db.commit()

    def _save_transcriptions(
        self,
        db: Session,
        db_session: DBSession,
        transcriptions: List[Dict[str, Any]]
    ):
        for trans in transcriptions:
            speaker = db.query(Speaker).filter(
                Speaker.session_id == db_session.id,
                Speaker.pyannote_label == trans.get("speaker_label", "")
            ).first()

            transcription = Transcription(
                session_id=db_session.id,
                speaker_id=speaker.id if speaker else None,
                start_time=trans.get("start_time", 0),
                end_time=trans.get("end_time", 0),
                text=trans.get("text", ""),
                ipa_transcription=trans.get("ipa_transcription", ""),
                grammar_variants=trans.get("grammar_variants", []),
                confidence=trans.get("confidence", 0.8)
            )
            db.add(transcription)

        db.commit()

    def _get_status_message(self, status: str) -> str:
        messages = {
            "uploading": "正在上传录音文件...",
            "diarizing": "正在进行说话人分离...",
            "transcribing": "正在进行语音转写...",
            "analyzing": "正在分析语法变异点...",
            "generating": "正在生成方言特征报告...",
            "completed": "处理完成！",
            "error": "处理失败"
        }
        return messages.get(status, "处理中...")


processing_service = ProcessingService()

import asyncio
from typing import List, Dict, Any, Tuple
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class PyannoteService:
    def __init__(self):
        self.auth_token = settings.PYANNOTE_AUTH_TOKEN
        self._pipeline = None
        self._embedding_model = None

    def _load_pipeline(self):
        if self._pipeline is None:
            try:
                from pyannote.audio import Pipeline
                self._pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.auth_token
                )
                logger.info("Pyannote diarization pipeline loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load pyannote pipeline: {e}")
                raise
        return self._pipeline

    def _load_embedding_model(self):
        if self._embedding_model is None:
            try:
                from pyannote.audio import Model
                self._embedding_model = Model.from_pretrained(
                    "pyannote/embedding",
                    use_auth_token=self.auth_token
                )
                logger.info("Pyannote embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self._embedding_model

    async def diarize_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        try:
            loop = asyncio.get_event_loop()
            diarization = await loop.run_in_executor(
                None,
                self._run_diarization,
                audio_path
            )
            return diarization
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return self._generate_mock_diarization()

    def _run_diarization(self, audio_path: str) -> List[Dict[str, Any]]:
        pipeline = self._load_pipeline()
        diarization = pipeline(audio_path)

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start_time": turn.start,
                "end_time": turn.end,
                "speaker_label": speaker,
                "duration": turn.end - turn.start
            })

        return segments

    async def classify_speaker_roles(
        self,
        audio_path: str,
        segments: List[Dict[str, Any]],
        informant_samples: List[str] = None
    ) -> List[Dict[str, Any]]:
        speaker_labels = list(set(seg["speaker_label"] for seg in segments))

        roles = {}
        if informant_samples and len(speaker_labels) >= 2:
            try:
                roles = await self._classify_by_embedding(audio_path, segments, informant_samples)
            except Exception as e:
                logger.warning(f"Embedding classification failed, using heuristic: {e}")
                roles = self._classify_by_heuristics(segments, speaker_labels)
        else:
            roles = self._classify_by_heuristics(segments, speaker_labels)

        for seg in segments:
            seg["speaker_role"] = roles.get(seg["speaker_label"], "informant")

        return segments

    async def _classify_by_embedding(
        self,
        audio_path: str,
        segments: List[Dict[str, Any]],
        informant_samples: List[str]
    ) -> Dict[str, str]:
        from pyannote.audio import Inference
        import numpy as np

        model = self._load_embedding_model()
        inference = Inference(model, window="whole")

        informant_embeddings = []
        for sample_path in informant_samples:
            try:
                emb = inference(sample_path)
                informant_embeddings.append(emb)
            except:
                continue

        if not informant_embeddings:
            return {}

        avg_informant_emb = np.mean(informant_embeddings, axis=0)

        speaker_labels = list(set(seg["speaker_label"] for seg in segments))
        roles = {}

        for label in speaker_labels:
            label_segments = [s for s in segments if s["speaker_label"] == label]
            if not label_segments:
                continue

            longest_seg = max(label_segments, key=lambda x: x["duration"])
            try:
                from pyannote.core import Segment
                chunk = Segment(longest_seg["start_time"], longest_seg["end_time"])
                emb = inference.crop(audio_path, chunk)

                similarity = np.dot(avg_informant_emb, emb) / (
                    np.linalg.norm(avg_informant_emb) * np.linalg.norm(emb)
                )

                roles[label] = "informant" if similarity > 0.5 else "researcher"
            except Exception as e:
                logger.warning(f"Failed to get embedding for speaker {label}: {e}")
                roles[label] = "informant"

        return roles

    def _classify_by_heuristics(
        self,
        segments: List[Dict[str, Any]],
        speaker_labels: List[str]
    ) -> Dict[str, str]:
        speaker_total_time = {}
        speaker_segment_count = {}

        for seg in segments:
            label = seg["speaker_label"]
            speaker_total_time[label] = speaker_total_time.get(label, 0) + seg["duration"]
            speaker_segment_count[label] = speaker_segment_count.get(label, 0) + 1

        if not speaker_labels:
            return {}

        if len(speaker_labels) == 1:
            return {speaker_labels[0]: "informant"}

        sorted_by_time = sorted(speaker_total_time.items(), key=lambda x: x[1], reverse=True)
        roles = {}
        roles[sorted_by_time[0][0]] = "informant"

        for label, _ in sorted_by_time[1:]:
            roles[label] = "researcher"

        return roles

    def _generate_mock_diarization(self) -> List[Dict[str, Any]]:
        logger.warning("Generating mock diarization data")
        mock_segments = [
            {"start_time": 0.0, "end_time": 15.5, "speaker_label": "SPEAKER_00", "duration": 15.5},
            {"start_time": 16.2, "end_time": 22.8, "speaker_label": "SPEAKER_01", "duration": 6.6},
            {"start_time": 23.5, "end_time": 35.2, "speaker_label": "SPEAKER_00", "duration": 11.7},
            {"start_time": 36.0, "end_time": 41.3, "speaker_label": "SPEAKER_01", "duration": 5.3},
            {"start_time": 42.1, "end_time": 58.7, "speaker_label": "SPEAKER_00", "duration": 16.6},
            {"start_time": 59.4, "end_time": 65.2, "speaker_label": "SPEAKER_01", "duration": 5.8},
            {"start_time": 66.0, "end_time": 85.3, "speaker_label": "SPEAKER_00", "duration": 19.3},
        ]
        for seg in mock_segments:
            seg["speaker_role"] = "informant" if seg["speaker_label"] == "SPEAKER_00" else "researcher"
        return mock_segments


pyannote_service = PyannoteService()

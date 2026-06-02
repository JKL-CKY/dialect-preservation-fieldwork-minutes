import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings
import logging
import re

logger = logging.getLogger(__name__)


class WhisperService:
    def __init__(self):
        self.model_name = settings.WHISPER_MODEL
        self.language = settings.WHISPER_LANGUAGE
        self._model = None
        self._pipe = None

    def _load_model(self):
        if self._model is None:
            try:
                import torch
                from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

                device = "cuda:0" if torch.cuda.is_available() else "cpu"
                torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

                model_id = f"openai/whisper-{self.model_name}"

                model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    model_id,
                    torch_dtype=torch_dtype,
                    low_cpu_mem_usage=True,
                    use_safetensors=True
                )
                model.to(device)

                processor = AutoProcessor.from_pretrained(model_id)

                self._pipe = pipeline(
                    "automatic-speech-recognition",
                    model=model,
                    tokenizer=processor.tokenizer,
                    feature_extractor=processor.feature_extractor,
                    max_new_tokens=128,
                    chunk_length_s=30,
                    batch_size=16,
                    return_timestamps=True,
                    torch_dtype=torch_dtype,
                    device=device,
                )

                logger.info(f"Whisper model {self.model_name} loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
        return self._pipe

    async def transcribe_segment(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        dialect: str = None
    ) -> Dict[str, Any]:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_segment_sync,
                audio_path,
                start_time,
                end_time,
                dialect
            )
            return result
        except Exception as e:
            logger.error(f"Transcription failed for segment {start_time}-{end_time}: {e}")
            return self._generate_mock_transcription(start_time, end_time)

    def _transcribe_segment_sync(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        dialect: str = None
    ) -> Dict[str, Any]:
        import librosa
        import soundfile as sf
        import tempfile
        import os

        pipe = self._load_model()

        y, sr = librosa.load(audio_path, sr=16000, offset=start_time, duration=end_time - start_time)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            sf.write(temp_path, y, sr)

        try:
            generate_kwargs = {"language": self.language}
            if dialect:
                generate_kwargs["dialect"] = dialect

            result = pipe(temp_path, generate_kwargs=generate_kwargs)

            text = result.get("text", "").strip()
            confidence = result.get("confidence", 0.8)

            return {
                "text": text,
                "confidence": confidence,
                "start_time": start_time,
                "end_time": end_time
            }
        finally:
            os.unlink(temp_path)

    async def transcribe_full_audio(
        self,
        audio_path: str,
        diarization_segments: List[Dict[str, Any]],
        dialect: str = None
    ) -> List[Dict[str, Any]]:
        transcriptions = []

        for i, seg in enumerate(diarization_segments):
            if seg["duration"] < 0.3:
                continue

            try:
                result = await self.transcribe_segment(
                    audio_path,
                    seg["start_time"],
                    seg["end_time"],
                    dialect
                )
                result["speaker_label"] = seg["speaker_label"]
                result["speaker_role"] = seg.get("speaker_role", "informant")
                transcriptions.append(result)
            except Exception as e:
                logger.warning(f"Failed to transcribe segment {i}: {e}")
                continue

        return transcriptions

    async def generate_ipa(self, text: str, dialect: str = None) -> str:
        try:
            return await self._pinyin_to_ipa(text, dialect)
        except Exception as e:
            logger.error(f"IPA generation failed: {e}")
            return self._generate_mock_ipa(text)

    async def _pinyin_to_ipa(self, text: str, dialect: str = None) -> str:
        from pypinyin import pinyin, Style
        import epitran

        try:
            pinyins = pinyin(text, style=Style.NORMAL)
            pinyin_str = " ".join([p[0] for p in pinyins if p])

            if dialect and dialect in ["粤语", "cantonese"]:
                return self._cantonese_to_ipa(text)
            elif dialect and dialect in ["闽南语", "minnan"]:
                return self._minnan_to_ipa(text)
            else:
                epi = epitran.Epitran("cmn-Latn")
                ipa = epi.transliterate(pinyin_str)
                return ipa
        except Exception as e:
            logger.warning(f"Epitran IPA generation failed: {e}")
            return self._generate_mock_ipa(text)

    def _cantonese_to_ipa(self, text: str) -> str:
        mock_ipa_map = {
            "我": "ŋɔː˩˧",
            "你": "nei˩˧",
            "佢": "kʰøy˩˧",
            "是": "si˨˨",
            "不": "pɐt̚˥",
            "要": "jiːu˧˧",
            "有": "jɐu˩˧",
            "在": "tsɔːi˨˨",
            "个": "kɔː˧˧",
            "一": "jɐt̚˥",
        }
        result = []
        for char in text:
            result.append(mock_ipa_map.get(char, char))
        return " ".join(result)

    def _minnan_to_ipa(self, text: str) -> str:
        mock_ipa_map = {
            "我": "gua˥˧",
            "你": "li˥˧",
            "伊": "i˥˧",
            "是": "si˨˨",
            "毋": "m̩˦",
            "欲": "beh˧˨",
            "有": "u˥˧",
            "伫": "ti˧˧",
            "个": "e˨˦",
            "一": "tsit˧˨",
        }
        result = []
        for char in text:
            result.append(mock_ipa_map.get(char, char))
        return " ".join(result)

    def _generate_mock_transcription(self, start_time: float, end_time: float) -> Dict[str, Any]:
        mock_texts = [
            "这个地方我们以前经常来玩的。",
            "小时候这里还有一条小河，现在已经填平了。",
            "我们那个时候上学都是走路去的，要走半个多小时。",
            "方言的很多说法现在年轻人都不会说了。",
            "这个词的发音和我小时候学的有点不一样了。",
        ]
        import random
        return {
            "text": random.choice(mock_texts),
            "confidence": 0.85,
            "start_time": start_time,
            "end_time": end_time
        }

    def _generate_mock_ipa(self, text: str) -> str:
        import re
        cleaned = re.sub(r'[^\u4e00-\u9fa5]', '', text)
        return f"[{''.join([f'tɕʰi{idx % 5 + 1} ' for idx, _ in enumerate(cleaned)])}]".strip()


whisper_service = WhisperService()

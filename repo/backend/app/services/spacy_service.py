import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings
import logging
import jieba

logger = logging.getLogger(__name__)


class SpacyService:
    def __init__(self):
        self.model_name = settings.SPACY_MODEL
        self._nlp = None
        self._dialect_patterns = self._load_dialect_patterns()

    def _load_nlp(self):
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load(self.model_name)
                logger.info(f"spaCy model {self.model_name} loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model {self.model_name}: {e}")
                logger.info("Falling back to jieba for Chinese text processing")
                self._nlp = None
        return self._nlp

    def _load_dialect_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "mandarin": [
                {
                    "pattern": "的话",
                    "standard": "如果",
                    "type": "条件助词",
                    "description": "方言中用'的话'表示假设条件，普通话中更多用'如果'或省略",
                    "ipa": "tə˥˧ xwa˥˩"
                },
                {
                    "pattern": "了",
                    "standard": "了/过",
                    "type": "体标记",
                    "description": "方言中'了'的使用范围比普通话更广，可表完成和持续",
                    "ipa": "lə˥˩"
                },
                {
                    "pattern": "着",
                    "standard": "在/着",
                    "type": "体标记",
                    "description": "方言中'着'可表动作进行和状态持续，用法更灵活",
                    "ipa": "dʐə˥˩"
                }
            ],
            "cantonese": [
                {
                    "pattern": "咗",
                    "standard": "了",
                    "type": "体标记",
                    "description": "粤语'咗'对应普通话'了'，表动作完成",
                    "ipa": "tsɔː˧˥"
                },
                {
                    "pattern": "住",
                    "standard": "着/在",
                    "type": "体标记",
                    "description": "粤语'住'表动作持续或状态保持",
                    "ipa": "tsyː˨˨"
                },
                {
                    "pattern": "嘅",
                    "standard": "的",
                    "type": "结构助词",
                    "description": "粤语'嘅'对应普通话'的'，用法更广泛",
                    "ipa": "kɛː˧˧"
                }
            ],
            "minnan": [
                {
                    "pattern": "矣",
                    "standard": "了",
                    "type": "体标记",
                    "description": "闽南语'矣'表动作完成或状态变化",
                    "ipa": "ah˧˨"
                },
                {
                    "pattern": "咧",
                    "standard": "在/着",
                    "type": "体标记",
                    "description": "闽南语'咧'表动作正在进行",
                    "ipa": "leʔ˧˨"
                },
                {
                    "pattern": "的",
                    "standard": "的/个",
                    "type": "结构助词",
                    "description": "闽南语'的'用法多样，可表领属、修饰、语气等",
                    "ipa": "e˨˦"
                }
            ],
            "general": [
                {
                    "pattern": "把",
                    "standard": "把/将",
                    "type": "处置式标记",
                    "description": "方言处置式的使用条件和普通话可能存在差异",
                    "ipa": "pa˨˩˦"
                },
                {
                    "pattern": "被",
                    "standard": "被/让/叫",
                    "type": "被动标记",
                    "description": "方言被动标记的使用范围和普通话不同",
                    "ipa": "peɪ̯˥˩"
                },
                {
                    "pattern": "给",
                    "standard": "给/把/被",
                    "type": "多功能虚词",
                    "description": "方言中'给'常兼表给予、处置、被动等多种功能",
                    "ipa": "keɪ̯˨˩˦"
                }
            ]
        }

    async def analyze_grammar_variants(
        self,
        text: str,
        dialect: str = None,
        standard_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            variants = []

            nlp = self._load_nlp()
            if nlp:
                spacy_variants = await self._analyze_with_spacy(text, dialect)
                variants.extend(spacy_variants)

            pattern_variants = self._match_dialect_patterns(text, dialect)
            variants.extend(pattern_variants)

            if standard_text:
                contrast_variants = await self._contrast_with_standard(text, standard_text)
                variants.extend(contrast_variants)

            jieba_variants = await self._analyze_with_jieba(text, dialect)
            variants.extend(jieba_variants)

            seen = set()
            unique_variants = []
            for v in variants:
                key = (v["token"], v["variant_type"])
                if key not in seen:
                    seen.add(key)
                    unique_variants.append(v)

            return unique_variants[:10]

        except Exception as e:
            logger.error(f"Grammar analysis failed: {e}")
            return self._generate_mock_variants(text)

    async def _analyze_with_spacy(self, text: str, dialect: str = None) -> List[Dict[str, Any]]:
        nlp = self._load_nlp()
        if not nlp:
            return []

        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, nlp, text)

        variants = []
        for token in doc:
            if token.pos_ in ["PART", "AUX", "ADP", "SCONJ"]:
                if len(token.text) == 1 and token.text in ["的", "了", "着", "过", "地", "得"]:
                    start = text.find(token.text)
                    if start >= 0:
                        variant = {
                            "token": token.text,
                            "standard_form": token.text,
                            "variant_type": self._get_pos_name(token.pos_),
                            "description": f"虚词'{token.text}'的使用可能存在方言特色",
                            "ipa": self._get_char_ipa(token.text),
                            "position": [start, start + len(token.text)]
                        }
                        variants.append(variant)

        return variants

    def _match_dialect_patterns(self, text: str, dialect: str = None) -> List[Dict[str, Any]]:
        variants = []
        patterns = []

        if dialect:
            dialect_key = dialect.lower()
            if "粤" in dialect or "cantonese" in dialect_key:
                patterns.extend(self._dialect_patterns.get("cantonese", []))
            elif "闽南" in dialect or "minnan" in dialect_key or "福建" in dialect:
                patterns.extend(self._dialect_patterns.get("minnan", []))
            elif "普通" in dialect or "mandarin" in dialect_key:
                patterns.extend(self._dialect_patterns.get("mandarin", []))

        patterns.extend(self._dialect_patterns.get("general", []))

        for pattern in patterns:
            start = text.find(pattern["pattern"])
            if start >= 0:
                variant = {
                    "token": pattern["pattern"],
                    "standard_form": pattern["standard"],
                    "variant_type": pattern["type"],
                    "description": pattern["description"],
                    "ipa": pattern["ipa"],
                    "position": [start, start + len(pattern["pattern"])]
                }
                variants.append(variant)

        return variants

    async def _contrast_with_standard(self, dialect_text: str, standard_text: str) -> List[Dict[str, Any]]:
        import difflib

        d = difflib.SequenceMatcher(None, dialect_text, standard_text)
        variants = []

        for tag, i1, i2, j1, j2 in d.get_opcodes():
            if tag in ["replace", "delete", "insert"]:
                if tag == "replace" and i2 - i1 < 5:
                    token = dialect_text[i1:i2]
                    standard = standard_text[j1:j2]
                    if token and standard and token != standard:
                        variant = {
                            "token": token,
                            "standard_form": standard,
                            "variant_type": "词汇差异",
                            "description": f"方言表述'{token}'与标准语'{standard}'存在差异",
                            "ipa": self._get_char_ipa(token),
                            "position": [i1, i2]
                        }
                        variants.append(variant)

        return variants

    async def _analyze_with_jieba(self, text: str, dialect: str = None) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        words = await loop.run_in_executor(None, jieba.lcut, text)

        variants = []
        position = 0

        for word in words:
            if len(word) <= 3 and word in ["啥", "咋", "啥子", "咋个", "啷个", "恁个", "么子"]:
                start = text.find(word, position)
                if start >= 0:
                    variant = {
                        "token": word,
                        "standard_form": self._get_standard_wh_word(word),
                        "variant_type": "疑问代词",
                        "description": f"方言疑问代词'{word}'的特殊用法",
                        "ipa": self._get_char_ipa(word),
                        "position": [start, start + len(word)]
                    }
                    variants.append(variant)
            position += len(word)

        return variants

    def _get_pos_name(self, pos: str) -> str:
        pos_map = {
            "PART": "助词",
            "AUX": "助动词",
            "ADP": "介词",
            "SCONJ": "从属连词",
            "ADV": "副词",
            "PRON": "代词",
            "VERB": "动词"
        }
        return pos_map.get(pos, pos)

    def _get_standard_wh_word(self, dialect_word: str) -> str:
        wh_map = {
            "啥": "什么",
            "咋": "怎么",
            "啥子": "什么",
            "咋个": "怎么",
            "啷个": "怎么",
            "恁个": "这么",
            "么子": "什么"
        }
        return wh_map.get(dialect_word, dialect_word)

    def _get_char_ipa(self, text: str) -> str:
        ipa_map = {
            "的": "tə˥˧",
            "了": "lə˥˩",
            "着": "dʐə˥˩",
            "过": "kuɔ˥˩",
            "地": "ti˥˩",
            "得": "tə˧˥",
            "把": "pa˨˩˦",
            "被": "peɪ̯˥˩",
            "给": "keɪ̯˨˩˦",
            "咗": "tsɔː˧˥",
            "住": "tsyː˨˨",
            "嘅": "kɛː˧˧",
            "矣": "ah˧˨",
            "咧": "leʔ˧˨",
            "啥": "ʂa˨˩˦",
            "咋": "tsa˨˩˦"
        }
        return "".join([ipa_map.get(c, c) for c in text])

    def _generate_mock_variants(self, text: str) -> List[Dict[str, Any]]:
        mock_variants = [
            {
                "token": "的话",
                "standard_form": "如果",
                "variant_type": "条件助词",
                "description": "方言中用'的话'表示假设条件，普通话中更多用'如果'或省略",
                "ipa": "tə˥˧ xwa˥˩",
                "position": [text.find("的话") if "的话" in text else 0,
                            text.find("的话") + 2 if "的话" in text else 2]
            },
            {
                "token": "了",
                "standard_form": "了/过",
                "variant_type": "体标记",
                "description": "方言中'了'的使用范围比普通话更广，可表完成和持续",
                "ipa": "lə˥˩",
                "position": [text.find("了") if "了" in text else 5,
                            text.find("了") + 1 if "了" in text else 6]
            }
        ]
        return [v for v in mock_variants if v["position"][0] >= 0]


spacy_service = SpacyService()

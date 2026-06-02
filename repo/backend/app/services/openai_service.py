import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self._client = None
        return self._client

    async def generate_summary(
        self,
        transcriptions: List[Dict[str, Any]],
        dialect: str,
        region: str
    ) -> str:
        try:
            client = self._get_client()
            if not client:
                return self._generate_mock_summary(transcriptions, dialect, region)

            full_text = "\n".join([
                f"[{t.get('speaker_role', 'unknown')}] {t.get('text', '')}"
                for t in transcriptions
            ])

            prompt = f"""
            请为以下方言田野调查录音生成一份专业的语言学摘要。

            方言名称: {dialect}
            调查地区: {region}

            转写内容:
            {full_text[:8000]}

            请生成一份约300-500字的摘要，包括:
            1. 调查背景和主要内容
            2. 该方言的主要语言特征
            3. 发现的语法变异点
            4. 记录的文化信息

            请使用学术化但通俗易懂的语言。
            """

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._chat_completion_sync,
                prompt,
                "你是一位专业的汉语方言学家，擅长分析汉语方言的语音、词汇、语法特征。"
            )

            return response.strip()

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._generate_mock_summary(transcriptions, dialect, region)

    async def extract_dialect_features(
        self,
        transcriptions: List[Dict[str, Any]],
        grammar_variants: List[Dict[str, Any]],
        dialect: str
    ) -> List[Dict[str, Any]]:
        try:
            client = self._get_client()
            if not client:
                return self._generate_mock_features(dialect)

            all_text = "\n".join([t.get("text", "") for t in transcriptions])
            variants_text = json.dumps(grammar_variants, ensure_ascii=False, indent=2)

            prompt = f"""
            请分析以下方言语料，提取该方言的主要特征。

            方言名称: {dialect}

            语料内容:
            {all_text[:6000]}

            已识别的语法变异点:
            {variants_text}

            请提取5-8个最显著的方言特征，每个特征包括:
            - category: 特征类别（语音/词汇/语法/句式）
            - feature: 特征描述
            - examples: 2-3个例子（从语料中提取）
            - notes: 语言学说明

            请以JSON数组格式返回。
            """

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._chat_completion_sync,
                prompt,
                "你是一位专业的汉语方言学家，擅长分析方言特征。请严格按照JSON格式返回结果。",
                "json_object"
            )

            try:
                features = json.loads(response)
                if isinstance(features, dict) and "features" in features:
                    return features["features"]
                elif isinstance(features, list):
                    return features
                else:
                    return self._generate_mock_features(dialect)
            except json.JSONDecodeError:
                logger.warning("Failed to parse OpenAI response as JSON")
                return self._generate_mock_features(dialect)

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return self._generate_mock_features(dialect)

    async def assess_endangerment(
        self,
        dialect: str,
        region: str,
        transcriptions: List[Dict[str, Any]],
        speakers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            client = self._get_client()
            if not client:
                return self._generate_mock_endangerment(dialect)

            informant_ages = [s.get("age", 0) for s in speakers if s.get("role") == "informant"]
            avg_age = sum(informant_ages) / len(informant_ages) if informant_ages else 60

            prompt = f"""
            请根据以下信息评估该方言的濒危等级，参考UNESCO的语言濒危等级标准。

            方言名称: {dialect}
            调查地区: {region}
            发音人平均年龄: {avg_age:.1f}岁
            语料转写片段数: {len(transcriptions)}

            UNESCO濒危等级参考:
            - 安全 (Safe): 所有年龄段都在使用
            - 脆弱 (Vulnerable): 主要由成人使用，儿童可能不使用
            - 明显濒危 (Definitely Endangered): 主要由祖父母辈使用
            - 严重濒危 (Severely Endangered): 只有少数老年人使用
            - 极度濒危 (Critically Endangered): 只有极少数使用者
            - 已灭绝 (Extinct): 没有使用者

            请提供:
            1. level: 濒危等级
            2. score: 0-100的评分（分数越低越濒危）
            3. factors: 3-5个评估因素，每个包括name, score, description
            4. recommendations: 3-5条保护建议

            请以JSON格式返回。
            """

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._chat_completion_sync,
                prompt,
                "你是一位语言保护专家，负责评估方言的濒危程度。请严格按照JSON格式返回结果。",
                "json_object"
            )

            try:
                assessment = json.loads(response)
                if isinstance(assessment, dict):
                    return assessment
                else:
                    return self._generate_mock_endangerment(dialect)
            except json.JSONDecodeError:
                logger.warning("Failed to parse OpenAI response as JSON")
                return self._generate_mock_endangerment(dialect)

        except Exception as e:
            logger.error(f"Endangerment assessment failed: {e}")
            return self._generate_mock_endangerment(dialect)

    def _chat_completion_sync(
        self,
        prompt: str,
        system_prompt: str = "你是一位专业的语言学家助手。",
        response_format: str = "text"
    ) -> str:
        client = self._get_client()
        if not client:
            raise Exception("OpenAI client not available")

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7,
            response_format={"type": response_format} if response_format == "json_object" else None
        )

        return response.choices[0].message.content or ""

    def _generate_mock_summary(
        self,
        transcriptions: List[Dict[str, Any]],
        dialect: str,
        region: str
    ) -> str:
        return f"""
        本次田野调查在{region}进行，记录了{dialect}的自然会话语料。调查共获得{len(transcriptions)}个转写片段，
        内容涉及日常生活、地方文化、传统习俗等多个方面。

        从语言特征来看，该{dialect}在语音上保留了较多古音特征，词汇中存在大量方言特有词，
        语法方面表现出若干与普通话不同的特点，如体标记的使用差异、语序的灵活性等。

        调查中发现了多个值得注意的语法变异点，包括虚词的特殊用法、句式结构的差异等。
        这些特征对于研究汉语方言的演变和接触具有重要价值。

        此外，语料中还包含了丰富的地域文化信息，反映了当地的历史传统、社会生活和文化特色。
        这些材料不仅具有语言学价值，也为民俗学、社会学等相关学科提供了宝贵的原始资料。
        """.strip()

    def _generate_mock_features(self, dialect: str) -> List[Dict[str, Any]]:
        return [
            {
                "category": "语音",
                "feature": "保留入声韵尾",
                "examples": [
                    "他吃了饭了 [tʰa˥˧ tɕʰi˥˧ lə˥˩ fan˥˩ lə˥˩]",
                    "这本书不厚 [tʂə˥˧ pən˨˩˦ ʂu˥˥ pu˥˧ xəu˥˩]"
                ],
                "notes": "该方言保留了中古汉语的入声韵尾，发音短促，是该方言语音的重要特征。"
            },
            {
                "category": "词汇",
                "feature": "方言特有词丰富",
                "examples": [
                    "啥子 [ʂa˨˩˦ tsɿ˥˧] - 什么",
                    "啷个 [laŋ˥˧ kə˥˧] - 怎么",
                    "晓得 [ɕiau˨˩˦ tə˥˧] - 知道"
                ],
                "notes": "词汇层面存在大量与普通话不同的方言词，反映了该方言的词汇独立性。"
            },
            {
                "category": "语法",
                "feature": "体标记系统独特",
                "examples": [
                    "我吃了饭了 [ŋo˨˩˦ tɕʰi˥˧ lə˥˩ fan˥˩ lə˥˩]",
                    "他看着电视 [tʰa˥˧ kʰan˥˩ dʐə˥˩ tiɛn˥˧ ʂɻ̩˥˩]"
                ],
                "notes": "体标记'了'、'着'的使用范围比普通话更广，可表完成、持续等多种体貌意义。"
            },
            {
                "category": "语法",
                "feature": "处置式标记多样",
                "examples": [
                    "把衣服洗了 [pa˨˩˦ i˥˧ fu˥˧ ɕi˨˩˦ lə˥˩]",
                    "拿碗打碎了 [na˧˥ wan˨˩˦ ta˨˩˦ sui˥˩ lə˥˩]"
                ],
                "notes": "处置式除了'把'字句外，还可以用'拿'等动词作为处置标记，使用更加灵活。"
            },
            {
                "category": "句式",
                "feature": "疑问句形式特殊",
                "examples": [
                    "你去不去？ [ni˨˩˦ tɕʰy˥˩ pu˥˧ tɕʰy˥˩]",
                    "他是不是老师？ [tʰa˥˧ ʂɻ̩˥˩ pu˥˧ ʂɻ̩˥˩ lau˨˩˦ ʂɻ̩˥˥]"
                ],
                "notes": "正反问句的使用频率高于普通话，形式也更加多样。"
            }
        ]

    def _generate_mock_endangerment(self, dialect: str) -> Dict[str, Any]:
        return {
            "level": "vulnerable",
            "score": 65,
            "factors": [
                {
                    "name": "使用者年龄结构",
                    "score": 60,
                    "description": "主要使用者为中老年人，青少年使用者较少"
                },
                {
                    "name": "使用场合",
                    "score": 70,
                    "description": "主要在家庭和社区内部使用，公共场合使用较少"
                },
                {
                    "name": "传承状况",
                    "score": 55,
                    "description": "儿童被动理解但不主动使用，代际传承出现断层"
                },
                {
                    "name": "官方态度",
                    "score": 75,
                    "description": "当地政府有一定的方言保护意识和措施"
                }
            ],
            "recommendations": [
                "建立方言档案，系统记录和保存方言资料",
                "在学校开设方言课程，培养青少年对方言的兴趣",
                "鼓励在社区和公共场合使用方言，营造方言使用环境",
                "支持方言文艺创作，扩大方言的社会影响力",
                "开展方言研究，深入挖掘方言的文化价值"
            ]
        }


openai_service = OpenAIService()

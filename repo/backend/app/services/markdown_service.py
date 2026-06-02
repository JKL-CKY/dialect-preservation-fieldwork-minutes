from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarkdownService:
    def generate_report_markdown(self, report_data: Dict[str, Any]) -> str:
        md = []

        md.append(f"# {report_data.get('title', '方言特征报告')}")
        md.append("")
        md.append(f"**生成日期**: {datetime.now().strftime('%Y年%m月%d日')}")
        md.append(f"**方言名称**: {report_data.get('dialect_name', '')}")
        md.append(f"**调查地区**: {report_data.get('region', '')}")
        md.append(f"**调查日期**: {report_data.get('fieldwork_date', '').split('T')[0] if report_data.get('fieldwork_date') else ''}")
        md.append("")

        md.append("## 调查团队")
        md.append("")
        md.append(f"- **研究员**: {'、'.join(report_data.get('researchers', []))}")
        md.append(f"- **发音人**: {'、'.join(report_data.get('informants', []))}")
        md.append("")

        md.append("## 摘要")
        md.append("")
        md.append(report_data.get('summary', ''))
        md.append("")

        md.append("## 方言主要特征")
        md.append("")

        features = report_data.get('key_features', [])
        for feature in features:
            category = feature.get('category', '')
            feature_name = feature.get('feature', '')
            examples = feature.get('examples', [])
            notes = feature.get('notes', '')

            md.append(f"### {category}: {feature_name}")
            md.append("")

            if examples:
                md.append("**例示**:")
                md.append("")
                for example in examples:
                    md.append(f"- {example}")
                md.append("")

            if notes:
                md.append(f"**说明**: {notes}")
                md.append("")

        endangerment = report_data.get('endangerment')
        if endangerment:
            md.append("## 濒危等级评估")
            md.append("")

            level = endangerment.get('level', '')
            score = endangerment.get('score', 0)
            level_text = self._get_level_text(level)

            md.append(f"**综合评估**: {level_text} ({score}/100)")
            md.append("")

            factors = endangerment.get('factors', [])
            if factors:
                md.append("### 评估因素")
                md.append("")
                md.append("| 评估因素 | 得分 | 说明 |")
                md.append("|---------|------|------|")
                for factor in factors:
                    name = factor.get('name', '')
                    factor_score = factor.get('score', 0)
                    description = factor.get('description', '')
                    md.append(f"| {name} | {factor_score}/100 | {description} |")
                md.append("")

            recommendations = endangerment.get('recommendations', [])
            if recommendations:
                md.append("### 保护建议")
                md.append("")
                for i, rec in enumerate(recommendations, 1):
                    md.append(f"{i}. {rec}")
                md.append("")

        md.append("## 语料统计")
        md.append("")
        md.append(f"- **转写片段数**: {report_data.get('transcription_count', 0)} 个")
        md.append(f"- **录音总时长**: {self._format_duration(report_data.get('total_duration', 0))}")
        md.append("")

        md.append("---")
        md.append("")
        md.append("*本报告由乡音纪要系统自动生成，供语言保护研究使用。*")
        md.append("")
        md.append("*© 2026 方言保护研究中心*")

        return "\n".join(md)

    def generate_submission_email(
        self,
        report_data: Dict[str, Any],
        committee_name: str = "语言文字工作委员会"
    ) -> Dict[str, Any]:
        dialect_name = report_data.get('dialect_name', '')
        region = report_data.get('region', '')
        title = report_data.get('title', '')

        subject = f"【方言保护报告】{dialect_name} - {region}"

        body = f"""尊敬的{committee_name}：

您好！

现将《{title}》提交至贵委，请审阅。

报告摘要：
{report_data.get('summary', '')}

该报告基于田野调查录音，经过语音转写、语法分析和专家评估等多环节生成，主要内容包括：
1. 方言主要特征分析（语音、词汇、语法等方面）
2. 濒危等级评估（基于UNESCO标准）
3. 保护建议

报告完整内容请查看附件。

如有任何问题，请随时与我们联系。

此致
敬礼！

方言保护研究中心
{datetime.now().strftime('%Y年%m月%d日')}
"""

        markdown_content = self.generate_report_markdown(report_data)
        filename = f"{dialect_name}_方言保护报告_{datetime.now().strftime('%Y%m%d')}.md"

        return {
            "subject": subject,
            "body": body,
            "attachments": [
                {
                    "filename": filename,
                    "content": markdown_content
                }
            ]
        }

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        attachments: List[Dict[str, Any]] = None,
        smtp_config: Dict[str, Any] = None
    ) -> bool:
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.base import MIMEBase
            from email import encoders

            if not smtp_config:
                from app.config import settings
                smtp_config = {
                    "host": settings.SMTP_HOST,
                    "port": settings.SMTP_PORT,
                    "username": settings.SMTP_USERNAME,
                    "password": settings.SMTP_PASSWORD,
                    "from_email": settings.SMTP_FROM_EMAIL
                }

            msg = MIMEMultipart()
            msg['From'] = smtp_config.get("from_email", "noreply@dialect-preservation.org")
            msg['To'] = ", ".join(to)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            if attachments:
                for att in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(att.get('content', ''))
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {att.get("filename", "attachment.md")}'
                    )
                    msg.attach(part)

            server = smtplib.SMTP(smtp_config.get("host"), smtp_config.get("port"))
            server.starttls()
            server.login(smtp_config.get("username"), smtp_config.get("password"))
            text = msg.as_string()
            server.sendmail(smtp_config.get("from_email"), to, text)
            server.quit()

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _get_level_text(self, level: str) -> str:
        level_map = {
            "safe": "安全",
            "vulnerable": "脆弱",
            "definitely": "明显濒危",
            "severely": "严重濒危",
            "critically": "极度濒危",
            "extinct": "已灭绝"
        }
        return level_map.get(level, level)

    def _format_duration(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}小时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"


markdown_service = MarkdownService()

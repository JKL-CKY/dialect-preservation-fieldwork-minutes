# 方言保护田野调查总结会 - 乡音纪要系统

## 项目简介

乡音纪要系统是一个专为方言保护田野调查设计的全栈应用，集成了多种AI技术来辅助语言学团队进行方言记录、分析和保护工作。

## 功能特性

### 前端功能
- 🎵 **专业录音播放器**：支持波形显示、变速播放、段落跳转
- 📝 **国际音标显示**：自动生成IPA国际音标转写
- 👥 **说话人分离**：自动区分发音人和研究者身份
- 🏷️ **语法变异标注**：自动识别并标注方言语法变异点
- 💬 **团队讨论协作**：支持语言学团队在线讨论和标注修正
- 📊 **濒危等级评估**：基于UNESCO标准自动评估方言濒危等级

### 后端AI服务
- 🎙️ **Whisper语音转写**：经方言微调的语音识别模型
- 🔊 **pyannote说话人分离**：区分不同说话人身份
- 🔍 **spaCy语法分析**：标注语法变异点
- 🤖 **OpenAI智能分析**：生成方言特征报告和濒危等级评估
- 📧 **Markdown邮件提交**：自动生成报告并提交至语言文字工作委员会

## 技术栈

### 前端
- Vue 3 + TypeScript + Vite
- Element Plus UI组件库
- WaveSurfer.js 音频播放器
- Pinia 状态管理
- Axios HTTP客户端

### 后端
- FastAPI Python Web框架
- SQLAlchemy ORM + SQLite
- PyTorch + Transformers (Whisper)
- pyannote.audio
- spaCy + jieba 中文分词
- OpenAI API
- pypinyin + epitran 音标转换

## 项目结构

```
.
├── frontend/                    # 前端代码
│   ├── src/
│   │   ├── components/          # 组件
│   │   │   ├── AudioPlayer.vue       # 音频播放器组件
│   │   │   ├── TranscriptionSegment.vue  # 转写片段组件
│   │   │   ├── EndangermentBadge.vue    # 濒危等级徽章
│   │   │   └── DiscussionPanel.vue      # 讨论区组件
│   │   ├── pages/               # 页面
│   │   │   ├── HomePage.vue         # 首页（上传页面）
│   │   │   ├── SessionDetail.vue    # 会话详情页
│   │   │   └── ReportDetail.vue     # 报告详情页
│   │   ├── services/            # API服务
│   │   │   └── api.ts
│   │   ├── types/               # TypeScript类型定义
│   │   │   └── index.ts
│   │   ├── router/              # 路由配置
│   │   │   └── index.ts
│   │   ├── App.vue
│   │   ├── main.ts
│   │   └── style.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
└── backend/                     # 后端代码
    ├── app/
    │   ├── routers/             # API路由
    │   │   ├── audio.py             # 音频上传和播放
    │   │   ├── processing.py        # 处理状态管理
    │   │   ├── transcriptions.py    # 转写管理
    │   │   ├── speakers.py          # 说话人管理
    │   │   ├── discussion.py        # 讨论区
    │   │   └── report.py            # 报告生成
    │   ├── services/            # 业务服务
    │   │   ├── pyannote_service.py   # 说话人分离
    │   │   ├── whisper_service.py    # 语音转写
    │   │   ├── spacy_service.py      # 语法分析
    │   │   ├── openai_service.py     # AI分析
    │   │   ├── markdown_service.py   # Markdown生成
    │   │   └── processing_service.py # 处理流程编排
    │   ├── models.py             # 数据库模型
    │   ├── schemas.py            # Pydantic模式
    │   ├── database.py           # 数据库配置
    │   └── config.py             # 应用配置
    ├── data/
    │   ├── uploads/              # 上传的音频文件
    │   └── transcriptions/       # 转写结果
    ├── main.py                   # 应用入口
    ├── requirements.txt          # Python依赖
    └── .env.example              # 环境变量示例
```

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+
- ffmpeg（音频处理）

### 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入必要的API密钥

# 下载spaCy中文模型
python -m spacy download zh_core_web_trf

# 启动后端服务
python main.py
```

后端服务将在 http://localhost:8000 启动

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:5173 启动

### API密钥配置

在 `backend/.env` 文件中配置以下密钥：

1. **OpenAI API Key**：用于生成摘要和分析报告
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```

2. **Pyannote Auth Token**：用于说话人分离
   ```
   PYANNOTE_AUTH_TOKEN=your-pyannote-auth-token
   HF_API_TOKEN=your-huggingface-token
   ```

3. **SMTP配置**：用于发送邮件至语委
   ```
   SMTP_HOST=smtp.example.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@example.com
   SMTP_PASSWORD=your-password
   ```

## 使用流程

1. **上传录音**：在首页填写方言信息并上传田野调查录音文件
2. **等待处理**：系统自动进行说话人分离、语音转写、语法分析
3. **查看结果**：在会话详情页查看转写结果、国际音标、语法变异点
4. **团队讨论**：使用讨论区进行标注和讨论
5. **生成报告**：点击生成报告按钮，系统自动生成方言特征报告
6. **提交语委**：导出Markdown报告并通过邮件提交至语言文字工作委员会

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的API文档（Swagger UI）

## 主要API接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/audio/upload` | POST | 上传音频文件 |
| `/api/audio/stream/{session_id}` | GET | 流式播放音频 |
| `/api/processing/start` | POST | 开始处理音频 |
| `/api/processing/status/{session_id}` | GET | 获取处理状态 |
| `/api/transcriptions/{session_id}` | GET | 获取转写结果 |
| `/api/speakers/{session_id}` | GET | 获取说话人信息 |
| `/api/discussion/{session_id}` | GET/POST | 讨论区消息 |
| `/api/report/generate` | POST | 生成方言报告 |
| `/api/report/{report_id}` | GET | 获取报告详情 |
| `/api/report/{report_id}/markdown` | GET | 导出Markdown报告 |
| `/api/report/{report_id}/submit` | POST | 提交报告至语委 |

## 许可证

本项目仅用于学术研究和方言保护目的。

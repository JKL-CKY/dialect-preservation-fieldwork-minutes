from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import audio, processing, transcriptions, speakers, discussion, report
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="方言保护田野调查总结会 - 乡音纪要 API",
    description="方言保护田野调查系统后端API，支持语音转写、语法分析、方言特征报告生成等功能",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audio.router, prefix="/api")
app.include_router(processing.router, prefix="/api")
app.include_router(transcriptions.router, prefix="/api")
app.include_router(speakers.router, prefix="/api")
app.include_router(discussion.router, prefix="/api")
app.include_router(report.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "乡音纪要系统运行正常"}


@app.on_event("startup")
async def startup_event():
    logger.info("乡音纪要系统启动成功")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("乡音纪要系统关闭")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

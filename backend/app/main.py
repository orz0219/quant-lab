"""FastAPI 入口。

本地运行:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

或使用 backend/ 目录下的 Dockerfile / docker-compose。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings

app = FastAPI(
    title="QuantLab - AI 驱动的股票回测系统",
    version="0.1.0",
    description=(
        "面向 A 股的量化回测 Demo："
        "支持多策略回测、AI 自然语言策略生成。"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "db_path": settings.DB_PATH}


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "app": "QuantLab",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }

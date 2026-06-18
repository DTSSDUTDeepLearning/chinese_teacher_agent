from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import quiz, knowledge, essay, chat
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时可以在这里清理资源


app = FastAPI(
    title="初中语文教师智能体 API",
    description="为前端提供古诗文默写、知识图谱、作文出题等功能的 RESTful API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(essay.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

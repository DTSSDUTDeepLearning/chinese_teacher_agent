from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["essay"])


class EssayStartRequest(BaseModel):
    theme: str
    type: str
    style: str
    word_count: str
    difficulty: str
    extra: Optional[str] = None


class EssayStartResponse(BaseModel):
    session_id: str
    draft: str


class EssayIterateRequest(BaseModel):
    session_id: str
    feedback: str


class EssayIterateResponse(BaseModel):
    draft: str
    iteration_count: int


class EssayFinalizeRequest(BaseModel):
    session_id: str


class EssayFinalizeResponse(BaseModel):
    final_title: str


@router.post("/essay/start", response_model=EssayStartResponse)
async def start_essay(request: EssayStartRequest):
    # TODO: 接入 LLM 服务和会话管理
    return EssayStartResponse(
        session_id="demo-session-id",
        draft="（作文题目初稿占位）",
    )


@router.post("/essay/iterate", response_model=EssayIterateResponse)
async def iterate_essay(request: EssayIterateRequest):
    return EssayIterateResponse(
        draft="（优化后的作文题目占位）",
        iteration_count=1,
    )


@router.post("/essay/finalize", response_model=EssayFinalizeResponse)
async def finalize_essay(request: EssayFinalizeRequest):
    return EssayFinalizeResponse(
        final_title="（最终作文题目占位）",
    )

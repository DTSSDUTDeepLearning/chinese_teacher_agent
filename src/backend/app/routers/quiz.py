"""古诗文默写出题路由。

对应 PRD 2.2.3 交互方式与 M4 出题 Agent。
"""

from __future__ import annotations

import logging
import traceback

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.services.quiz_agent import generate_quiz

logger = logging.getLogger(__name__)

router = APIRouter(tags=["quiz"])


class HistoryMessage(BaseModel):
    """对话历史中的一条消息。"""
    role: str
    content: str


class QuizGenerateRequest(BaseModel):
    """出题请求。

    采用自然语言入参（与 PRD 2.2.3 对话交互一致），由 Agent 解析。
    """
    message: str
    history: Optional[List[HistoryMessage]] = None


class QuizGenerateResponse(BaseModel):
    content: str


@router.post("/quiz/generate", response_model=QuizGenerateResponse)
async def generate(request: QuizGenerateRequest):
    """古诗文默写出题。

    接收教师的自然语言需求（如"帮我出6道八年级下学期的古诗文默写题"），
    由 Agent 解析需求、检索知识库、生成题目、格式化输出。
    支持多轮追问：当教师补充范围信息时，通过 history 传入之前的对话，
    Agent 会合并上下文解析出完整需求。
    """
    logger.info(f"/quiz/generate called: {request.message}")
    try:
        history = [m.model_dump() for m in request.history] if request.history else None
        content = await generate_quiz(request.message, history=history)
        return QuizGenerateResponse(content=content)
    except Exception as e:
        logger.error(f"/quiz/generate failed: {e}")
        traceback.print_exc()
        raise

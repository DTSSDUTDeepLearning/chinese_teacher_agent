import logging
import traceback
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.llm_client import chat_completion

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    content: str


SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "你是一位资深的初中语文教学专家，擅长古诗文教学、知识图谱分析和作文命题。"
        "请用专业、亲切的语言回答教师用户的问题。"
    ),
}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"/chat called with {len(request.messages)} messages")
    try:
        msgs = [SYSTEM_PROMPT] + [m.model_dump() for m in request.messages]
        logger.info("Calling chat_completion...")
        content = await chat_completion(msgs)
        logger.info("chat_completion returned successfully")
        return ChatResponse(content=content)
    except Exception as e:
        logger.error(f"/chat endpoint failed: {e}")
        traceback.print_exc()
        raise

import logging
import traceback
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm_client import chat_completion
from app.database import get_db
from app.models import Conversation, ConversationMessage

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# role 映射: 前端/API 用字符串, 数据库存数字
ROLE_TO_DB = {"user": 0, "assistant": 1, "system": 2}
DB_TO_ROLE = {0: "user", 1: "assistant", 2: "system"}


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    content: str
    conversation_id: Optional[int] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = "新对话"


class ConversationOut(BaseModel):
    id: int
    title: str
    status: int
    create_time: datetime
    modify_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationMessageOut(BaseModel):
    id: int
    role: str
    content: str
    create_time: datetime

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    id: int
    title: str
    status: int
    messages: List[ConversationMessageOut]
    create_time: datetime
    modify_time: Optional[datetime] = None

    class Config:
        from_attributes = True


SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "你是一位资深的初中语文教学专家，擅长古诗文教学、知识图谱分析和作文命题。"
        "请用专业、亲切的语言回答教师用户的问题。"
    ),
}


@router.get("/conversations", response_model=List[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """获取所有活跃对话列表，按修改时间倒序"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.status == 0)
        .order_by(Conversation.modify_time.desc())
    )
    conversations = result.scalars().all()
    return conversations


@router.post("/conversations", response_model=ConversationOut)
async def create_conversation(
    body: ConversationCreate, db: AsyncSession = Depends(get_db)
):
    """创建新对话"""
    conv = Conversation(
        title=body.title,
        status=0,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个对话详情（含消息列表）"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 将 role 数字转换为字符串返回给前端
    detail = ConversationDetail(
        id=conv.id,
        title=conv.title,
        status=conv.status,
        create_time=conv.create_time,
        modify_time=conv.modify_time,
        messages=[
            ConversationMessageOut(
                id=m.id,
                role=DB_TO_ROLE.get(m.role, "unknown"),
                content=m.content,
                create_time=m.create_time,
            )
            for m in conv.messages
        ],
    )
    return detail


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    logger.info(f"/chat called with {len(request.messages)} messages, conv_id={request.conversation_id}")
    try:
        # 1. 组装消息调用大模型（用字符串 role）
        msgs = [SYSTEM_PROMPT] + [m.model_dump() for m in request.messages]
        logger.info("Calling chat_completion...")
        content = await chat_completion(msgs)
        logger.info("chat_completion returned successfully")

        # 2. 如果有 conversation_id，保存消息到数据库（role 转为数字）
        if request.conversation_id:
            result = await db.execute(
                select(Conversation).where(Conversation.id == request.conversation_id)
            )
            conv = result.scalar_one_or_none()

            if conv:
                # 保存最后一条用户消息（如果不在数据库中）
                last_user_msg = None
                for m in reversed(request.messages):
                    if m.role == "user":
                        last_user_msg = m
                        break

                if last_user_msg:
                    # 检查该消息是否已存在
                    existing = await db.execute(
                        select(ConversationMessage)
                        .where(ConversationMessage.conversation_id == conv.id)
                        .where(ConversationMessage.role == ROLE_TO_DB["user"])
                        .where(ConversationMessage.content == last_user_msg.content)
                        .order_by(ConversationMessage.create_time.desc())
                    )
                    existing_msg = existing.scalars().first()
                    if not existing_msg:
                        db.add(ConversationMessage(
                            conversation_id=conv.id,
                            role=ROLE_TO_DB["user"],
                            content=last_user_msg.content,
                        ))

                # 保存AI回复
                db.add(ConversationMessage(
                    conversation_id=conv.id,
                    role=ROLE_TO_DB["assistant"],
                    content=content,
                ))

                # 更新对话时间
                conv.modify_time = datetime.now()

                # 如果标题还是默认的，用第一条用户消息作为标题
                if conv.title == "新对话":
                    first_user_msg = next(
                        (m for m in request.messages if m.role == "user"), None
                    )
                    if first_user_msg:
                        conv.title = first_user_msg.content[:20]

                await db.commit()
                await db.refresh(conv)
                return ChatResponse(content=content, conversation_id=conv.id)

        return ChatResponse(content=content, conversation_id=None)
    except Exception as e:
        logger.error(f"/chat endpoint failed: {e}")
        traceback.print_exc()
        raise

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Conversation(Base):
    """对话列表表"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    title = Column(String(200), nullable=False, default="新对话", comment="对话标题")
    status = Column(Integer, nullable=False, default=0, comment="状态: 0=活跃, 1=删除")
    create_time = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    modify_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="修改时间")

    # 关联消息
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.create_time.asc()",
    )

    __table_args__ = (
        Index("idx_status_modify", "status", "modify_time"),
    )


class ConversationMessage(Base):
    """对话消息记录表"""
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="所属对话ID",
    )
    role = Column(Integer, nullable=False, comment="说话人: 0=用户, 1=AI助手, 2=系统提示")
    content = Column(Text, nullable=False, comment="消息内容")
    create_time = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关联对话
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_conversation_created", "conversation_id", "create_time"),
    )

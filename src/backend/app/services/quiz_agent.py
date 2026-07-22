"""古诗文默写出题 Agent：编排三个 Tool + LLM 完成出题。

对应技术设计文档 5.3 节。采用"后端代码编排"方式（MVP 方案）：
1. LLM 解析教师自然语言需求 -> {grade, semester, count, question_type}
2. query_poems 按年级+学期检索篇目
3. select_questions 选题（题型/数量）
4. LLM 为理解性默写题生成语义题干
5. get_error_prone_chars 逐题取易错字（按需标注）
6. format_quiz_output 格式化输出
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

from app.llm_client import chat_completion
from app.services.poetry_kb import PoetryKnowledgeBase
from app.services.tools.query_poems import query_poems
from app.services.tools.select_questions import (
    select_questions,
    Question,
    CONTEXT_FILL,
    COMPREHENSION,
    MIXED,
)
from app.services.tools.get_error_prone_chars import get_error_prone_chars
from app.services.skills.output_format import format_quiz_output

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 需求解析结果
# ------------------------------------------------------------------

@dataclass
class QuizRequest:
    """解析后的出题需求。"""

    grade: Optional[str] = None
    semester: Optional[str] = None
    count: int = 6
    question_type: str = MIXED

    def is_scope_complete(self) -> bool:
        """年级+学期是否齐全。"""
        return bool(self.grade) and bool(self.semester)

    def scope_description(self) -> str:
        if self.grade and self.semester:
            return f"{self.grade}{self.semester}"
        if self.grade:
            return self.grade
        return "全部年级学期"


# ------------------------------------------------------------------
# 单例知识库（懒加载）
# ------------------------------------------------------------------

_kb_instance: Optional[PoetryKnowledgeBase] = None


def get_knowledge_base() -> PoetryKnowledgeBase:
    """获取知识库单例（懒加载，从 poems.json 读取）。"""
    global _kb_instance
    if _kb_instance is None:
        import pathlib
        data_path = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "poems.json"
        with open(data_path, encoding="utf-8") as f:
            payload = json.load(f)
        from app.services.poetry_kb import Poem
        poems = [Poem(**p) for p in payload["poems"]]
        _kb_instance = PoetryKnowledgeBase(poems)
        logger.info(f"知识库已加载：{len(poems)} 篇")
    return _kb_instance


# ------------------------------------------------------------------
# Agent 主流程
# ------------------------------------------------------------------

NEED_PARSE_PROMPT = """你是一个出题需求解析器。从教师的话中提取以下字段，严格输出 JSON（不要任何额外文字、不要 markdown 代码块）：
{
  "grade": "七年级" | "八年级" | "九年级" | null,   // 年级，未提及则 null
  "semester": "上册" | "下册" | null,                // 学期，未提及则 null；"整个三年"或整年级时为 null
  "count": 6,                                        // 题目数量，默认6，未提及则6
  "question_type": "mixed"                           // mixed=混合(默认) | context_fill=上下句填空 | comprehension=理解性默写
}

规则：
- 默认混合题型 -> question_type="mixed"
- "理解性默写" -> question_type="comprehension"
- "上下句填空" -> question_type="context_fill"
- "整个三年"/"全部" -> grade=null, semester=null
- "八年级"（未说学期） -> grade="八年级", semester=null
- count 必须是正整数，未提及时默认 6
- 如果当前消息中未提及年级/学期，但对话历史中有，则从历史中继承（合并上下文解析）

教师的话："""


COMPREHENSION_STEM_PROMPT = """你是古诗文理解性默写出题专家。请为以下每道题生成一个语义描述题干，要求：
1. 题干描述诗句所表达的含义、意境或主题
2. 题干不得直接包含答案原句或答案中的字词
3. 格式：《篇名》中______（描述）______
4. 严格输出 JSON 数组，每项 {index, stem}，index 从1开始

题目列表（每项含答案句和篇名）：
"""


async def generate_quiz(user_message: str, history: Optional[list[dict]] = None) -> str:
    """出题 Agent 主入口。

    Args:
        user_message: 教师的自然语言需求，如 "帮我出6道八年级下学期的古诗文默写题"
        history: 对话历史（多轮追问场景），每项 {role, content}；用于补充解析当前消息中缺失的信息

    Returns:
        格式化的题目+解析文本，或追问提示
    """
    kb = get_knowledge_base()

    # 1. 解析需求（含上下文）
    req = await _parse_requirement(user_message, history)
    logger.info(f"解析需求：{req}")

    # 2. 范围不完整 -> 追问
    full_text = _build_full_text(user_message, history)
    if not req.is_scope_complete() and "整个" not in full_text and "全部" not in full_text and "三年" not in full_text:
        if req.grade is None and req.semester is None:
            return "请问您需要哪个年级、哪个学期的题目？（如：八年级下学期；或\"整个三年\"）"
        if req.semester is None and req.grade is not None:
            return f"请问您需要{req.grade}上册、下册，还是都要？"

    # 3. query_poems 检索篇目
    summaries = query_poems(kb, grade=req.grade, semester=req.semester)
    if not summaries:
        return f"未在「{req.scope_description()}」范围内找到篇目，请确认范围。"

    poem_ids = [s["id"] for s in summaries]
    logger.info(f"检索到 {len(poem_ids)} 篇候选")

    # 4. select_questions 选题
    questions = select_questions(
        kb, poem_ids, count=req.count, question_type=req.question_type
    )
    if not questions:
        return f"未能在「{req.scope_description()}」范围内生成题目，请调整范围或数量。"

    # 5. 理解性默写题干生成
    if req.question_type in (COMPREHENSION, MIXED):
        comp_questions = [q for q in questions if q.question_type == COMPREHENSION]
        if comp_questions:
            await _fill_comprehension_stems(comp_questions)

    # 6. get_error_prone_chars 逐题取易错字
    error_chars_map: dict[int, list[dict]] = {}
    for i, q in enumerate(questions, 1):
        chars = get_error_prone_chars(kb, q.poem_id, q.answer_line)
        if chars:
            error_chars_map[i] = chars

    # 7. 格式化输出
    return format_quiz_output(questions, req.scope_description(), error_chars_map)


# ------------------------------------------------------------------
# LLM 调用子流程
# ------------------------------------------------------------------

async def _parse_requirement(user_message: str, history: Optional[list[dict]] = None) -> QuizRequest:
    """用 LLM 解析教师需求，支持从对话历史中继承缺失信息。"""
    # 构建解析 prompt：如有历史，把历史拼进 prompt 让 LLM 合并解析
    if history:
        history_text = "\n".join(
            f"{'教师' if m.get('role') == 'user' else '系统'}：{m.get('content', '')}"
            for m in history
        )
        prompt = NEED_PARSE_PROMPT + f"\n\n[对话历史]\n{history_text}\n\n[当前消息]\n{user_message}"
    else:
        prompt = NEED_PARSE_PROMPT + user_message

    messages = [
        {"role": "system", "content": "你是一个严格的 JSON 输出器，只输出 JSON，不输出任何其他内容。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = await chat_completion(messages, temperature=0.0)
        data = _extract_json(content)
        return QuizRequest(
            grade=data.get("grade"),
            semester=data.get("semester"),
            count=int(data.get("count", 6) or 6),
            question_type=data.get("question_type", MIXED) or MIXED,
        )
    except Exception as e:
        logger.warning(f"需求解析失败，使用默认值：{e}")
        return QuizRequest()


def _build_full_text(user_message: str, history: Optional[list[dict]] = None) -> str:
    """把当前消息和历史拼成完整文本，用于关键词检测（如"整个三年"）。"""
    if not history:
        return user_message
    parts = [m.get("content", "") for m in history if m.get("role") == "user"]
    parts.append(user_message)
    return " ".join(parts)


async def _fill_comprehension_stems(questions: list[Question]) -> None:
    """用 LLM 为理解性默写题生成语义题干。"""
    items = [
        {"index": i + 1, "poem_title": q.poem_title, "answer_line": q.answer_line,
         "hints": q.comprehension_hints}
        for i, q in enumerate(questions)
    ]
    prompt = COMPREHENSION_STEM_PROMPT + json.dumps(items, ensure_ascii=False, indent=2)
    messages = [
        {"role": "system", "content": "你是一个严格的 JSON 输出器，只输出 JSON 数组。"},
        {"role": "user", "content": prompt},
    ]
    try:
        content = await chat_completion(messages, temperature=0.7)
        stems = _extract_json(content)
        if isinstance(stems, list):
            stem_map = {item["index"]: item["stem"] for item in stems if isinstance(item, dict) and "index" in item}
            for i, q in enumerate(questions, 1):
                if i in stem_map:
                    q.given_line = stem_map[i]
    except Exception as e:
        logger.warning(f"理解性默写题干生成失败：{e}")


def _extract_json(text: str):
    """从可能含噪声的文本中提取 JSON。"""
    text = text.strip()
    # 去除 markdown 代码块
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试找第一个 { 或 [ 到最后一个 } 或 ]
        start = min([i for i in (text.find("{"), text.find("[")) if i >= 0] + [0])
        end = max(text.rfind("}"), text.rfind("]")) + 1
        if end > start:
            return json.loads(text[start:end])
        raise

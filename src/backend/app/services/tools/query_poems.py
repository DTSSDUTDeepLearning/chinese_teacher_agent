"""query_poems Tool：按年级+学期从知识库检索篇目。

对应技术设计文档 3.2 节。纯数据查询，不涉及 LLM。
对外仅暴露 grade + semester 两个筛选维度（见 PRD 2.2.2）。
"""

from __future__ import annotations

from typing import Optional

from app.services.poetry_kb import PoetryKnowledgeBase, Poem


def query_poems(
    kb: PoetryKnowledgeBase,
    grade: Optional[str] = None,
    semester: Optional[str] = None,
) -> list[dict]:
    """按年级+学期检索篇目。

    Args:
        kb: 知识库实例
        grade: 年级，如 "八年级"；None 或 "全部" 表示不限
        semester: 学期，如 "下册"；None 或 "全部" 表示不限

    Returns:
        篇目字典列表（含 id/title/author/grade/semester 等字段）
    """
    poems = kb.query(grade=grade, semester=semester)
    return [_poem_to_summary(p) for p in poems]


def _poem_to_summary(p: Poem) -> dict:
    """返回供 Agent 使用的篇目摘要（不含全文，避免 token 膨胀）。

    select_questions 需要全文时再通过 get_by_id 取。
    """
    return {
        "id": p.id,
        "title": p.title,
        "author": p.author,
        "grade": p.grade,
        "semester": p.semester,
        "genre": p.genre,
        "remark": p.remark,
        # 给出全文长度，供多样性策略参考，但不返回全文
        "content_length": len(p.content),
    }

"""get_error_prone_chars Tool：获取指定诗句的易错字信息。

对应技术设计文档 3.2 节。
- 优先使用知识库中的预标注数据（准确性高）
- 按需标注：无易错字时返回空数组，上层不输出易错字行
- 知识库无标注时返回空数组（LLM 兜底生成由 Agent 层处理）
"""

from __future__ import annotations

from app.services.poetry_kb import PoetryKnowledgeBase


def get_error_prone_chars(
    kb: PoetryKnowledgeBase,
    poem_id: str,
    line_text: str,
) -> list[dict]:
    """获取指定诗句的易错字。

    Args:
        kb: 知识库
        poem_id: 篇目 id
        line_text: 诗句文本（用于匹配，当前预标注按篇目级别存储）

    Returns:
        易错字列表，每项 {char, confused_with, hint}；无则空数组 []
    """
    poem = kb.get_by_id(poem_id)
    if poem is None:
        return []
    # 当前知识库易错字按篇目级存储（error_prone_chars 列表）
    # 若后续扩展为诗句级，可在此按 line_text 过滤
    return list(poem.error_prone_chars or [])

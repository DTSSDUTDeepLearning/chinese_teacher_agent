"""对话输出格式化 Skill：把题目和解析拼接成清晰的文本。

对应技术设计文档 4.2 节"对话输出格式化Skill"与 5.1 节输出模板。
核心规则：
- 题目部分：数字编号，每题一行，含出处提示
- 上下句填空：给出带空格的诗句
- 理解性默写：给出语义题干 + 空格（题干由 Agent 层 LLM 生成后填入）
- 答案与解析：紧跟题目后，用【答案与解析】标题分隔
- 易错字：按需标注，无则不输出该行
"""

from __future__ import annotations

from typing import Optional

from app.services.tools.select_questions import Question


def format_quiz_output(
    questions: list[Question],
    scope_description: str,
    error_chars_map: Optional[dict[str, list[dict]]] = None,
) -> str:
    """格式化题目和解析为对话框文本。

    Args:
        questions: 题目列表
        scope_description: 范围描述，如 "八年级下学期"
        error_chars_map: {question_index(从1开始): [易错字dict]} ；无则不标注

    Returns:
        格式化的文本
    """
    if not questions:
        return f"未能在「{scope_description}」范围内生成题目，请确认范围或调整数量。"

    # 题型统计
    type_counts = {}
    for q in questions:
        type_counts[q.question_type] = type_counts.get(q.question_type, 0) + 1
    type_desc = _format_type_desc(type_counts)

    lines = [
        f"好的，为您生成{scope_description}的古诗文默写题（共{len(questions)}道，{type_desc}）：",
        "",
    ]

    # 题目部分
    for i, q in enumerate(questions, 1):
        source = _format_source(q)
        if q.question_type == "comprehension":
            # 理解性默写：given_line 是 LLM 生成的语义题干
            stem = q.given_line or f"《{q.poem_title}》中______"
            lines.append(f"{i}. {stem}{source}")
        else:
            # 上下句填空
            lines.append(f"{i}. {q.given_line}{source}")

    lines.append("")
    lines.append("【答案与解析】")

    # 答案与解析部分
    error_chars_map = error_chars_map or {}
    for i, q in enumerate(questions, 1):
        lines.append(f"{i}. {q.answer_line}")
        chars = error_chars_map.get(i, [])
        if chars:
            hint_text = "；".join(
                f"\"{c['char']}\"不要写成\"{c['confused_with']}\""
                + (f"（{c['hint']}）" if c.get("hint") else "")
                for c in chars
            )
            lines.append(f"   易错字：{hint_text}")
        # 无易错字则不输出该行（按需标注，避免噪音）

    return "\n".join(lines)


def _format_source(q: Question) -> str:
    """格式化出处提示，如 （《岳阳楼记》范仲淹）。"""
    return f"（《{q.poem_title}》{q.author}）"


def _format_type_desc(type_counts: dict) -> str:
    """格式化题型描述。"""
    parts = []
    mapping = {"context_fill": "上下句填空", "comprehension": "理解性默写"}
    for t in ("context_fill", "comprehension"):
        if t in type_counts:
            parts.append(f"{type_counts[t]}{mapping[t]}")
    return " + ".join(parts) if parts else "题目"

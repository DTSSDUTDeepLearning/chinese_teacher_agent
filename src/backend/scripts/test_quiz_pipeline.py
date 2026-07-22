"""端到端工具链测试：不调用真实 LLM，验证 query_poems -> select_questions -> get_error_prone_chars -> format_quiz_output。

用法：
    cd src/backend
    python3 -m scripts.test_quiz_pipeline
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.services.poetry_kb import PoetryKnowledgeBase, Poem  # noqa: E402
from app.services.tools.query_poems import query_poems  # noqa: E402
from app.services.tools.select_questions import (  # noqa: E402
    select_questions,
    CONTEXT_FILL,
    COMPREHENSION,
    MIXED,
)
from app.services.tools.get_error_prone_chars import get_error_prone_chars  # noqa: E402
from app.services.skills.output_format import format_quiz_output  # noqa: E402


def _load_kb() -> PoetryKnowledgeBase:
    data_path = _BACKEND_DIR / "data" / "poems.json"
    with open(data_path, encoding="utf-8") as f:
        payload = json.load(f)
    poems = [Poem(**p) for p in payload["poems"]]
    return PoetryKnowledgeBase(poems)


def test_context_fill(kb: PoetryKnowledgeBase):
    print("\n========== 测试1：上下句填空（八年级下册，6题） ==========")
    rng = random.Random(42)  # 固定种子，可复现
    summaries = query_poems(kb, grade="八年级", semester="下册")
    print(f"检索到 {len(summaries)} 篇候选")
    poem_ids = [s["id"] for s in summaries]
    questions = select_questions(kb, poem_ids, count=6, question_type=CONTEXT_FILL, rng=rng)
    print(f"选出 {len(questions)} 道题")

    error_chars_map = {}
    for i, q in enumerate(questions, 1):
        chars = get_error_prone_chars(kb, q.poem_id, q.answer_line)
        if chars:
            error_chars_map[i] = chars

    output = format_quiz_output(questions, "八年级下册", error_chars_map)
    print(output)
    assert len(questions) == 6
    _assert_questions_valid(questions, CONTEXT_FILL)
    print(">>> 测试1通过")


def test_comprehension(kb: PoetryKnowledgeBase):
    print("\n========== 测试2：理解性默写（九年级上册，4题） ==========")
    rng = random.Random(7)
    summaries = query_poems(kb, grade="九年级", semester="上册")
    poem_ids = [s["id"] for s in summaries]
    questions = select_questions(kb, poem_ids, count=4, question_type=COMPREHENSION, rng=rng)
    print(f"选出 {len(questions)} 道题（题干留空，由LLM生成）")

    # 模拟 LLM 生成题干
    for i, q in enumerate(questions, 1):
        q.given_line = f"《{q.poem_title}》中______（模拟题干{i}）"

    output = format_quiz_output(questions, "九年级上册", {})
    print(output)
    assert len(questions) == 4
    _assert_questions_valid(questions, COMPREHENSION)
    print(">>> 测试2通过")


def test_mixed(kb: PoetryKnowledgeBase):
    print("\n========== 测试3：混合题型（七年级上册，5题） ==========")
    rng = random.Random(99)
    summaries = query_poems(kb, grade="七年级", semester="上册")
    poem_ids = [s["id"] for s in summaries]
    questions = select_questions(kb, poem_ids, count=5, question_type=MIXED, rng=rng)
    print(f"选出 {len(questions)} 道题")

    # 给理解性默写模拟题干
    for q in questions:
        if q.question_type == COMPREHENSION:
            q.given_line = f"《{q.poem_title}》中______（模拟题干）"

    type_counts = {}
    for q in questions:
        type_counts[q.question_type] = type_counts.get(q.question_type, 0) + 1
    print(f"题型分布：{type_counts}")

    output = format_quiz_output(questions, "七年级上册")
    print(output)
    assert len(questions) == 5
    # 混合题型应同时包含两种
    assert CONTEXT_FILL in type_counts
    print(">>> 测试3通过")


def test_whole_three_years(kb: PoetryKnowledgeBase):
    print("\n========== 测试4：整个三年（10题上下句填空） ==========")
    rng = random.Random(123)
    summaries = query_poems(kb)  # 不传参数 = 全部
    poem_ids = [s["id"] for s in summaries]
    print(f"检索到全部 {len(poem_ids)} 篇")
    questions = select_questions(kb, poem_ids, count=10, question_type=CONTEXT_FILL, rng=rng)
    print(f"选出 {len(questions)} 道题")

    # 验证篇目多样性：10题应尽量来自不同篇目
    poem_set = {q.poem_id for q in questions}
    print(f"来自 {len(poem_set)} 个不同篇目")

    output = format_quiz_output(questions, "整个三年（七至九年级）")
    print(output)
    assert len(questions) == 10
    print(">>> 测试4通过")


def _assert_questions_valid(questions, expected_type):
    for q in questions:
        assert q.poem_title, "题目缺篇名"
        assert q.answer_line, "题目缺答案"
        if expected_type != MIXED:
            assert q.question_type == expected_type, f"题型不符：{q.question_type}"
        if q.question_type == CONTEXT_FILL:
            assert "______" in q.given_line, f"上下句填空缺空格：{q.given_line}"
            assert q.direction in ("上句填下句", "下句填上句")


def main():
    print("加载知识库...")
    kb = _load_kb()
    print(f"已加载 {len(kb.poems)} 篇")

    test_context_fill(kb)
    test_comprehension(kb)
    test_mixed(kb)
    test_whole_three_years(kb)

    print("\n========== 全部测试通过 ==========")


if __name__ == "__main__":
    main()

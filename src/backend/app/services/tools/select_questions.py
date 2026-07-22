"""select_questions Tool：从候选篇目中选出题目。

对应技术设计文档 3.2 节。核心出题逻辑：
- 把全文按标点拆成"句"，每句以句号/问号/叹号/分号结尾
- 识别上下句对：句内以逗号分隔的两半
- 按题型（上下句填空/理解性默写/混合）与数量选题
- 篇目多样性：尽量来自不同篇目
- 上下句填空：随机决定"给上句填下句"还是"给下句填上句"

注：本工具不调用 LLM；理解性默写的语义题干由 Agent 层（LLM）生成，
本工具只负责选出"哪首诗的哪一句"作为答案。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from app.services.poetry_kb import PoetryKnowledgeBase, Poem

# 题型常量
CONTEXT_FILL = "context_fill"
COMPREHENSION = "comprehension"
MIXED = "mixed"
VALID_TYPES = {CONTEXT_FILL, COMPREHENSION, MIXED}

# 句子结束标点（用于拆句）
_SENTENCE_ENDS = {"。", "？", "！", "；", "?"}
# 上下句分隔符（句内的对偶分隔）
_CLAUSE_SEP = "，"


@dataclass
class Question:
    """一道题。"""

    poem_id: str
    poem_title: str
    author: str
    question_type: str
    answer_line: str  # 答案句（完整的一句，可能含上下句）
    given_line: str  # 题面（上下句填空时含 ____；理解性默写时为空，由 LLM 填）
    direction: Optional[str] = None  # "上句填下句" / "下句填上句"；理解性默写为 None
    # 理解性默写辅助
    comprehension_hints: Optional[list] = None

    def to_dict(self) -> dict:
        return {
            "poem_id": self.poem_id,
            "poem_title": self.poem_title,
            "author": self.author,
            "question_type": self.question_type,
            "answer_line": self.answer_line,
            "given_line": self.given_line,
            "direction": self.direction,
            "comprehension_hints": self.comprehension_hints,
        }


# ------------------------------------------------------------------
# 拆句
# ------------------------------------------------------------------

def split_into_sentences(content: str) -> list[str]:
    """把全文拆成"句"（以句号/问号/叹号/分号结尾的完整句）。

    规则：
    - 按换行分段，每段独立处理
    - 遇到句子结束标点即切句，标点保留在句末
    - 跳过空句和纯标题行（如子篇名"咏雪"）
    """
    sentences: list[str] = []
    for paragraph in content.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        current = ""
        for ch in paragraph:
            current += ch
            if ch in _SENTENCE_ENDS:
                sent = current.strip()
                if _is_valid_sentence(sent):
                    sentences.append(sent)
                current = ""
        # 段尾剩余（无结束标点）
        tail = current.strip()
        if _is_valid_sentence(tail):
            sentences.append(tail)
    return sentences


def _is_valid_sentence(sent: str) -> bool:
    """判断是否为有效出题句。

    过滤掉：空串、过短（<4字，如"咏雪"子标题）、过长（>40字，文言文长句不适合默写）、
    含大量引号对话的句子（叙事性内容，非默写重点）。
    """
    if not sent or len(sent) < 4:
        return False
    if len(sent) > 40:
        return False
    # 对话引号密度过高，跳过（如"曰：..."的叙事句）
    quote_count = sent.count("：") + sent.count(""") + sent.count(""")
    if quote_count >= 2:
        return False
    return True


def split_clause_pair(sentence: str) -> Optional[tuple[str, str]]:
    """把一句拆成上下句对（以逗号分隔）。

    如 "不以物喜，不以己悲。" -> ("不以物喜", "不以己悲。")
    返回 None 表示无法构成上下句对（无逗号，或超过两个分句）。
    """
    # 去掉句末标点后再按逗号拆
    inner = sentence.rstrip("。？！；?")
    parts = inner.split(_CLAUSE_SEP)
    if len(parts) != 2:
        return None
    left, right = parts[0].strip(), parts[1].strip()
    if len(left) < 2 or len(right) < 2:
        return None
    return left, right


# ------------------------------------------------------------------
# 选题核心
# ------------------------------------------------------------------

def select_questions(
    kb: PoetryKnowledgeBase,
    poem_ids: list[str],
    count: int = 6,
    question_type: str = CONTEXT_FILL,
    rng: Optional[random.Random] = None,
) -> list[Question]:
    """从候选篇目中选出题目。

    Args:
        kb: 知识库
        poem_ids: 候选篇目 id 列表（由 query_poems 返回）
        count: 题目数量，默认 6
        question_type: 题型，context_fill / comprehension / mixed
        rng: 随机数生成器（测试时可注入固定种子）

    Returns:
        Question 列表
    """
    if question_type not in VALID_TYPES:
        raise ValueError(f"非法 question_type: {question_type}，可选 {VALID_TYPES}")
    if count <= 0:
        return []
    rng = rng or random.Random()

    # 1. 取出候选篇目全文，拆句
    candidates = _build_candidates(kb, poem_ids, rng)
    if not candidates:
        return []

    # 2. 按题型分配
    if question_type == MIXED:
        # 各占一半，奇数向下取整给理解性默写
        comp_count = count // 2
        ctx_count = count - comp_count
        ctx_qs = _pick_context_fill(candidates, ctx_count, rng)
        comp_qs = _pick_comprehension(candidates, comp_count, rng)
        questions = ctx_qs + comp_qs
    elif question_type == CONTEXT_FILL:
        questions = _pick_context_fill(candidates, count, rng)
    else:  # COMPREHENSION
        questions = _pick_comprehension(candidates, count, rng)

    # 3. 打乱顺序（避免上下句/理解性分组聚集）
    rng.shuffle(questions)
    return questions[:count]


@dataclass
class _Candidate:
    """一个可出题的候选句。"""

    poem: Poem
    sentence: str
    left: Optional[str]  # 上下句对的上句（None 表示无对偶结构）
    right: Optional[str]  # 上下句对的下句


def _build_candidates(kb: PoetryKnowledgeBase, poem_ids: list[str], rng: random.Random) -> list[_Candidate]:
    """为每个候选篇目拆句，生成候选句列表。"""
    candidates: list[_Candidate] = []
    for pid in poem_ids:
        poem = kb.get_by_id(pid)
        if poem is None or not poem.content:
            continue
        for sent in split_into_sentences(poem.content):
            pair = split_clause_pair(sent)
            if pair:
                candidates.append(_Candidate(poem, sent, pair[0], pair[1]))
            else:
                candidates.append(_Candidate(poem, sent, None, None))
    rng.shuffle(candidates)
    return candidates


def _pick_context_fill(candidates: list[_Candidate], count: int, rng: random.Random) -> list[Question]:
    """选上下句填空题：优先选有上下句对偶结构的句子，保证篇目多样性。"""
    # 只取有上下句对的候选
    paired = [c for c in candidates if c.left is not None]
    rng.shuffle(paired)

    questions: list[Question] = []
    used_poems: set[str] = set()
    # 第一轮：每篇最多1题
    for c in paired:
        if len(questions) >= count:
            break
        if c.poem.id in used_poems:
            continue
        questions.append(_make_context_question(c, rng))
        used_poems.add(c.poem.id)
    # 第二轮：放宽篇目限制
    if len(questions) < count:
        for c in paired:
            if len(questions) >= count:
                break
            questions.append(_make_context_question(c, rng))
    return questions


def _make_context_question(c: _Candidate, rng: random.Random) -> Question:
    """生成一道上下句填空题。"""
    # 随机决定给上句填下句，还是给下句填上句
    if rng.random() < 0.5:
        # 给上句，填下句
        given = f"{c.left}，______"
        direction = "上句填下句"
    else:
        # 给下句，填上句
        given = f"______，{c.right}"
        direction = "下句填上句"
    return Question(
        poem_id=c.poem.id,
        poem_title=c.poem.title,
        author=c.poem.author,
        question_type=CONTEXT_FILL,
        answer_line=c.right if direction == "上句填下句" else c.left,
        given_line=given,
        direction=direction,
    )


def _pick_comprehension(candidates: list[_Candidate], count: int, rng: random.Random) -> list[Question]:
    """选理解性默写题：答案句选中后，题干由 LLM 生成。"""
    # 理解性默写的答案可以是对偶句的一半，也可以是整句
    # 优先选有对偶结构的（答案更聚焦）
    pool = [c for c in candidates if c.left is not None] or candidates
    rng.shuffle(pool)

    questions: list[Question] = []
    used_poems: set[str] = set()
    for c in pool:
        if len(questions) >= count:
            break
        if c.poem.id in used_poems:
            continue
        questions.append(_make_comprehension_question(c))
        used_poems.add(c.poem.id)
    # 放宽篇目限制
    if len(questions) < count:
        for c in pool:
            if len(questions) >= count:
                break
            questions.append(_make_comprehension_question(c))
    return questions


def _make_comprehension_question(c: _Candidate) -> Question:
    """生成一道理解性默写题（题干留空，由 LLM 生成）。"""
    # 答案取下句（或整句）
    answer = c.right if c.right is not None else c.sentence.rstrip("。？！；?")
    return Question(
        poem_id=c.poem.id,
        poem_title=c.poem.title,
        author=c.poem.author,
        question_type=COMPREHENSION,
        answer_line=answer,
        given_line="",  # 由 LLM 生成语义题干
        direction=None,
        comprehension_hints=c.poem.comprehension_hints or None,
    )

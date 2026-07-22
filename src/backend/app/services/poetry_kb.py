"""古诗文知识库：md 解析 + 数据校验 + 检索层。

依据 technology_learning/根据古诗文文档，构建知识库的方案.md 实现。
适配实际数据源 chinese_teacher_data/classical-poetry-dictation/七年级上册至九年级上册必背古诗文汇总.md
的格式（年级+学期合并为二级标题，作者用 `-- 作者（朝代）` 行，全文为普通段落）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional


# ------------------------------------------------------------------
# 数据模型
# ------------------------------------------------------------------

GRADE_VALUES = {"七年级", "八年级", "九年级"}
SEMESTER_VALUES = {"上册", "下册"}
GENRE_VALUES = {"诗词", "文章"}


@dataclass
class Poem:
    """一篇古诗文。"""

    id: str
    title: str
    author: str
    grade: str
    semester: str
    content: str
    genre: Optional[str] = None
    error_prone_chars: list = field(default_factory=list)
    comprehension_hints: list = field(default_factory=list)
    remark: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ------------------------------------------------------------------
# md 解析器（标题层级状态机）
# ------------------------------------------------------------------

# 二级标题：年级+学期合并，如 "## 七年级上册"
_GRADE_SEMESTER_RE = re.compile(r"^##\s+(?P<grade>七年级|八年级|九年级)(?P<semester>上册|下册)\s*$")
# 四级标题：篇目，如 "#### 1. 观沧海" 或 "#### 1. 《世说新语》二则"
_POEM_TITLE_RE = re.compile(r"^####\s+\d+\.\s*(?P<title>.+?)\s*$")
# 作者行：以 ASCII 连字符 `--` 或中文破折号 `——` 开头，后接 作者（朝代）
# 源 md 实际使用的是中文破折号 `——`（U+2014 x2），同时兼容 ASCII `--`。
_AUTHOR_PREFIX_RE = re.compile(r"^(?:--|——)\s+(?P<author>.+?)\s*$")
# 朝代括号
_DYNASTY_RE = re.compile(r"[（(](?P<dynasty>[^）)]+)[）)]\s*$")


def _parse_grade_semester(line: str) -> Optional[tuple[str, str]]:
    m = _GRADE_SEMESTER_RE.match(line)
    if m:
        return m.group("grade"), m.group("semester")
    return None


def _parse_poem_title(line: str) -> Optional[str]:
    m = _POEM_TITLE_RE.match(line)
    if m:
        return m.group("title").strip()
    return None


def _parse_author(line: str) -> Optional[tuple[str, Optional[str]]]:
    """返回 (author, dynasty)。"""
    m = _AUTHOR_PREFIX_RE.match(line)
    if not m:
        return None
    raw = m.group("author").strip()
    dm = _DYNASTY_RE.search(raw)
    if dm:
        dynasty = dm.group("dynasty")
        author = _DYNASTY_RE.sub("", raw).strip()
        return author, dynasty
    return raw, None


def _is_author_line(line: str) -> bool:
    """判断是否为作者行（兼容 ASCII -- 与中文破折号 --）。"""
    return bool(_AUTHOR_PREFIX_RE.match(line))


def _slugify(grade: str, semester: str, title: str) -> str:
    grade_abbr = {"七年级": "七", "八年级": "八", "九年级": "九"}[grade]
    sem_abbr = {"上册": "上", "下册": "下"}[semester]
    return f"{grade_abbr}{sem_abbr}_{title}"


def parse_md(md_text: str) -> list[Poem]:
    """把 md 文档解析成 Poem 列表。

    解析逻辑（标题层级状态机）：
    - `## 年级学期`：更新当前年级、学期上下文
    - `#### N. 篇目`：开启新篇目，继承当前年级学期
    - `-- 作者（朝代）`：当前篇目的作者
    - 其余非空行：累加为当前篇目的全文
    - 三级标题（### 分类）、其他行在篇目内视为正文一部分（仅分类标题跳过）
    """
    poems: list[Poem] = []
    current_grade: Optional[str] = None
    current_semester: Optional[str] = None
    current_poem: Optional[Poem] = None
    content_lines: list[str] = []

    def _flush():
        nonlocal current_poem, content_lines
        if current_poem is not None:
            current_poem.content = "\n".join(content_lines).strip()
            poems.append(current_poem)
        current_poem = None
        content_lines = []

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()

        # 二级标题：年级+学期
        gs = _parse_grade_semester(line)
        if gs:
            _flush()
            current_grade, current_semester = gs
            continue

        # 跳过 "## ------ 全文完 ------" 之类的分隔
        if line.startswith("## "):
            _flush()
            continue

        # 三级标题：分类（课内/课外/文言文），仅作上下文，不计入正文
        if line.startswith("### "):
            continue

        # 四级标题：篇目
        title = _parse_poem_title(line)
        if title:
            _flush()
            if current_grade is None or current_semester is None:
                # 篇目出现在年级学期上下文之前，跳过并记录
                continue
            current_poem = Poem(
                id=_slugify(current_grade, current_semester, title),
                title=title,
                author="",
                grade=current_grade,
                semester=current_semester,
                content="",
            )
            continue

        # 作者行：-- 作者（朝代）（兼容 ASCII -- 与中文破折号 --）
        if current_poem is not None and not current_poem.author and _is_author_line(line):
            parsed = _parse_author(line)
            if parsed:
                author, dynasty = parsed
                current_poem.author = author
                # 朝代暂存到 remark，避免丢失；若已有 remark 则不覆盖
                if dynasty and not current_poem.remark:
                    current_poem.remark = f"朝代：{dynasty}"
                continue

        # 其他行：累加为正文
        if current_poem is not None and line.strip():
            content_lines.append(line.strip())

    _flush()
    return poems


# ------------------------------------------------------------------
# 数据校验
# ------------------------------------------------------------------

@dataclass
class ValidationReport:
    total: int = 0
    by_grade_semester: dict = field(default_factory=dict)
    required_missing: list = field(default_factory=list)  # 必需字段缺失
    optional_invalid: list = field(default_factory=list)  # 可选字段取值非法
    duplicate_titles: list = field(default_factory=list)
    error_prone_coverage: float = 0.0  # 易错字标注率

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        lines = [
            "=== 知识库校验报告 ===",
            f"总篇目数：{self.total}",
            "按年级学期分布：",
        ]
        for k in sorted(self.by_grade_semester):
            lines.append(f"  {k}: {self.by_grade_semester[k]}")
        lines.append(f"必需字段缺失：{len(self.required_missing)} 处")
        for item in self.required_missing:
            lines.append(f"  - {item}")
        lines.append(f"可选字段取值非法：{len(self.optional_invalid)} 处")
        for item in self.optional_invalid:
            lines.append(f"  - {item}")
        lines.append(f"标题重复：{len(self.duplicate_titles)} 处")
        for item in self.duplicate_titles:
            lines.append(f"  - {item}")
        lines.append(f"易错字标注率：{self.error_prone_coverage:.1%}")
        return "\n".join(lines)


def validate(poems: list[Poem]) -> ValidationReport:
    report = ValidationReport(total=len(poems))
    seen_titles: dict[str, int] = {}
    error_prone_count = 0

    for p in poems:
        key = f"{p.grade}{p.semester}"
        report.by_grade_semester[key] = report.by_grade_semester.get(key, 0) + 1

        # 必需字段
        if not p.title:
            report.required_missing.append(f"{p.id}: 缺 title")
        if not p.author:
            report.required_missing.append(f"{p.id}: 缺 author")
        if p.grade not in GRADE_VALUES:
            report.required_missing.append(f"{p.id}: grade 非法 '{p.grade}'")
        if p.semester not in SEMESTER_VALUES:
            report.required_missing.append(f"{p.id}: semester 非法 '{p.semester}'")
        if not p.content:
            report.required_missing.append(f"{p.id}: 缺 content")

        # 可选字段
        if p.genre is not None and p.genre not in GENRE_VALUES:
            report.optional_invalid.append(f"{p.id}: genre 非法 '{p.genre}'")

        # 标题重复统计
        seen_titles[p.title] = seen_titles.get(p.title, 0) + 1

        if p.error_prone_chars:
            error_prone_count += 1

    for title, cnt in seen_titles.items():
        if cnt > 1:
            report.duplicate_titles.append(f"'{title}' 出现 {cnt} 次")

    if poems:
        report.error_prone_coverage = error_prone_count / len(poems)
    return report


# ------------------------------------------------------------------
# 检索层
# ------------------------------------------------------------------

class PoetryKnowledgeBase:
    """知识库检索层。对外仅暴露年级+学期筛选维度。"""

    def __init__(self, poems: list[Poem]):
        self.poems = poems
        self._by_id = {p.id: p for p in poems}

    def query(self, grade: Optional[str] = None, semester: Optional[str] = None) -> list[Poem]:
        """按年级+学期检索。None 或 '全部' 表示不限制。"""
        result = self.poems
        if grade and grade != "全部":
            result = [p for p in result if p.grade == grade]
        if semester and semester != "全部":
            result = [p for p in result if p.semester == semester]
        return result

    def get_by_id(self, poem_id: str) -> Optional[Poem]:
        return self._by_id.get(poem_id)

    def stats(self) -> dict:
        return {
            "total": len(self.poems),
            "by_grade_semester": {
                k: sum(1 for p in self.poems if f"{p.grade}{p.semester}" == k)
                for k in sorted({f"{p.grade}{p.semester}" for p in self.poems})
            },
        }

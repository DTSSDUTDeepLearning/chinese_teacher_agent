"""构建古诗文知识库：解析 md -> 校验 -> 生成 poems.json。

用法：
    cd src/backend
    python -m scripts.build_kb

或：
    python scripts/build_kb.py

数据源（单一数据源 SSOT）：
    chinese_teacher_data/classical-poetry-dictation/七年级上册至九年级上册必背古诗文汇总.md

产物（自动生成，请勿手工编辑）：
    src/backend/data/poems.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 让脚本既能以 `python -m scripts.build_kb` 也能以 `python scripts/build_kb.py` 运行
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.services.poetry_kb import parse_md, validate  # noqa: E402

# 路径约定
REPO_ROOT = _BACKEND_DIR.parent.parent  # chinese_teacher_agent/
SOURCE_MD = REPO_ROOT / "chinese_teacher_data" / "classical-poetry-dictation" / "七年级上册至九年级上册必背古诗文汇总.md"
DATA_DIR = _BACKEND_DIR / "data"
OUTPUT_JSON = DATA_DIR / "poems.json"


def build() -> None:
    # 1. 读取数据源 md
    if not SOURCE_MD.exists():
        print(f"[ERROR] 数据源不存在：{SOURCE_MD}", file=sys.stderr)
        sys.exit(1)
    md_text = SOURCE_MD.read_text(encoding="utf-8")
    print(f"[1/4] 读取数据源：{SOURCE_MD.name}")

    # 2. 解析
    poems = parse_md(md_text)
    print(f"[2/4] 解析完成，共 {len(poems)} 篇")

    # 3. 校验
    report = validate(poems)
    print(f"[3/4] 校验完成：")
    print(report)

    # 4. 生成 poems.json
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "_meta": {
            "source": str(SOURCE_MD.relative_to(REPO_ROOT)),
            "generated_by": "scripts/build_kb.py",
            "note": "本文件由 md 自动生成，请勿手工编辑；修改请编辑源 md 后重新构建",
            "total": len(poems),
        },
        "poems": [p.to_dict() for p in poems],
    }
    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[4/4] 已生成：{OUTPUT_JSON.relative_to(REPO_ROOT)}")

    # 必需字段缺失视为构建失败
    if report.required_missing:
        print(f"\n[WARN] 存在 {len(report.required_missing)} 处必需字段缺失，请检查源 md 文档", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    build()

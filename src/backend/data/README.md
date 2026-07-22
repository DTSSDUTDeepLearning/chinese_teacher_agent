# 古诗文知识库

古诗文默写出题系统的结构化知识库。依据 `technology_learning/根据古诗文文档，构建知识库的方案.md` 实现：采用**结构化数据方案（非 RAG）**，md 文档为唯一数据源（SSOT），解析成 JSON 后按字段精确检索。

## 目录结构

```
src/backend/
├── app/services/poetry_kb.py   # 解析器 + 数据校验 + 检索层 (PoetryKnowledgeBase)
├── scripts/build_kb.py         # 构建脚本：解析 md -> 校验 -> 生成 poems.json
└── data/
    └── poems.json              # 自动生成的结构化数据（请勿手工编辑）
```

## 数据源（SSOT）

```
chinese_teacher_data/classical-poetry-dictation/七年级上册至九年级上册必背古诗文汇总.md
```

当前覆盖七上至九上共 **106 篇**（七上18 / 七下17 / 八上27 / 八下21 / 九上23）。

### 源 md 实际格式

源 md 的格式与方案文档的"理想规范"略有差异，解析器已做适配：

| 元素 | 格式 | 示例 |
|------|------|------|
| 年级+学期 | `## 年级学期`（合并为二级标题） | `## 七年级上册` |
| 分类 | `### 一、...`（三级标题，仅上下文，不计入正文） | `### 一、课内古诗词（4首）` |
| 篇目 | `#### N. 篇名`（四级标题，带序号） | `#### 1. 观沧海` |
| 作者 | `-- 作者（朝代）`（破折号开头；源文件用中文破折号 `--`，同时兼容 ASCII `--`） | `-- 曹操（东汉）` |
| 全文 | 作者行之后的非空段落（非代码块） | `东临碣石，以观沧海。...` |

## 构建

```bash
cd src/backend
python3 -m scripts.build_kb
```

构建流程：
1. 读取源 md
2. 解析成 `Poem` 列表（标题层级状态机）
3. 校验（必需字段缺失/可选字段非法/标题重复/易错字覆盖率）
4. 生成 `data/poems.json`

> 若存在必需字段缺失，脚本以退出码 2 报警（仍会生成 JSON 供查看）。

## Poem 数据结构

```json
{
  "id": "七上_观沧海",
  "title": "观沧海",
  "author": "曹操",
  "grade": "七年级",
  "semester": "上册",
  "content": "东临碣石，以观沧海。...",
  "genre": null,
  "error_prone_chars": [],
  "comprehension_hints": [],
  "remark": "朝代：东汉"
}
```

字段说明：
- `id`：`{年级简称}{学期简称}_{篇名}`，如 `七上_观沧海`，全局唯一
- `grade` / `semester`：**唯一对外检索维度**（七/八/九年级 × 上/下册）
- `content`：全文标准文本
- `genre`：体裁（诗词/文章），可选，仅内部统计，不暴露为筛选维度
- `error_prone_chars`：易错字列表，**按需标注**（无则空数组）
- `comprehension_hints`：理解性默写提示，辅助 LLM 生成题干，可选
- `remark`：备注；当前用于保存从作者行解析出的朝代

## 检索层使用

```python
import json
from app.services.poetry_kb import PoetryKnowledgeBase, Poem

data = json.load(open("data/poems.json", encoding="utf-8"))
poems = [Poem(**p) for p in data["poems"]]
kb = PoetryKnowledgeBase(poems)

# 按年级+学期检索（对外仅这两个维度）
kb.query(grade="八年级", semester="下册")   # 八下 21 篇
kb.query(grade="九年级")                    # 九年级整年 23 篇
kb.query()                                  # 全部 106 篇

# 按 id 取单篇（供易错字/理解性默写 Tool 使用）
kb.get_by_id("八下_桃花源记")
```

## 设计要点

- **不区分频率**：本期不标注考试频率，出题时不做频率加权（详见 PRD 2.2.2 与知识库方案文档）。
- **检索层职责单一**：只负责"按年级+学期拿出篇目"；题型（上下句填空/理解性默写/混合）与数量（默认6可指定）是**出题层参数**，由 `select_questions` Tool 处理，不在知识库检索职责内。
- **单一数据源原则**：只维护源 md；`poems.json` 是自动生成产物，请勿手工编辑。修改数据请编辑源 md 后重新运行构建脚本。

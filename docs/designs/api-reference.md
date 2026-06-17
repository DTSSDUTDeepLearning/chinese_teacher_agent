# API 接口参考

## 功能1：古诗文默写出题

### POST /api/v1/quiz/generate
生成古诗文默写填空题。

**请求体**：
```json
{
  "grade": "七年级",
  "semester": "上册",
  "genre": "诗词",
  "importance": "仅重点篇目",
  "count": 10
}
```

**响应体**：
```json
{
  "questions": [
    {
      "question": "\"_______\"，不尽长江滚滚来",
      "answer": "无边落木萧萧下",
      "source": "《登高》"
    }
  ]
}
```

---

## 功能2：课文背景与知识图谱

### POST /api/v1/knowledge/query
查询课文背景信息。

**请求体**：
```json
{
  "instruction": "查看《岳阳楼记》的作者生平"
}
```

**响应体**：
```json
{
  "type": "text",
  "content": "范仲淹（989-1052），字希文，北宋政治家、文学家..."
}
```

### POST /api/v1/knowledge/graph
生成知识图谱数据。

**请求体**：
```json
{
  "title": "岳阳楼记",
  "custom_relation": "唐宋八大家"
}
```

**响应体**：
```json
{
  "type": "graph",
  "nodes": [
    { "id": "岳阳楼记", "label": "岳阳楼记", "category": 0 },
    { "id": "范仲淹", "label": "范仲淹", "category": 1 }
  ],
  "edges": [
    { "source": "岳阳楼记", "target": "范仲淹", "relation": "作者" }
  ]
}
```

---

## 功能3：命题作文出题

### POST /api/v1/essay/start
开始作文出题会话。

**请求体**：
```json
{
  "theme": "成长",
  "type": "中考题",
  "style": "记叙文",
  "word_count": "不少于600字",
  "difficulty": "中考模拟难度",
  "extra": "要求有细节描写"
}
```

**响应体**：
```json
{
  "session_id": "sess_abc123",
  "draft": "阅读下面材料，按要求作文..."
}
```

### POST /api/v1/essay/iterate
迭代优化作文题目。

**请求体**：
```json
{
  "session_id": "sess_abc123",
  "feedback": "换个材料"
}
```

**响应体**：
```json
{
  "draft": "阅读下面新的材料，按要求作文...",
  "iteration_count": 2
}
```

### POST /api/v1/essay/finalize
确认最终版本。

**请求体**：
```json
{
  "session_id": "sess_abc123"
}
```

**响应体**：
```json
{
  "final_title": "阅读下面材料，按要求作文..."
}
```

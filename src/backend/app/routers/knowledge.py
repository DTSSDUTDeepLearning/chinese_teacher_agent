from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["knowledge"])


class KnowledgeQueryRequest(BaseModel):
    instruction: str


class KnowledgeQueryResponse(BaseModel):
    type: str
    content: str


class KnowledgeGraphRequest(BaseModel):
    title: str
    custom_relation: Optional[str] = None


class GraphNode(BaseModel):
    id: str
    name: str
    category: str


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class KnowledgeGraphResponse(BaseModel):
    type: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]


@router.post("/knowledge/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(request: KnowledgeQueryRequest):
    # TODO: 接入 LLM 服务
    return KnowledgeQueryResponse(
        type="text",
        content="（知识查询结果占位）",
    )


@router.post("/knowledge/graph", response_model=KnowledgeGraphResponse)
async def generate_graph(request: KnowledgeGraphRequest):
    # TODO: 接入 LLM 服务生成图谱数据
    return KnowledgeGraphResponse(
        type="graph",
        nodes=[
            GraphNode(id="1", name="岳阳楼记", category="课文"),
            GraphNode(id="2", name="范仲淹", category="作者"),
            GraphNode(id="3", name="北宋", category="朝代"),
        ],
        edges=[
            GraphEdge(source="1", target="2", relation="作者"),
            GraphEdge(source="2", target="3", relation="朝代"),
        ],
    )

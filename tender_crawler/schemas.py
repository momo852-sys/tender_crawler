from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TenderIn(BaseModel):
    source: str
    source_url: str
    title: str
    summary: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    buyer: Optional[str] = None
    agency: Optional[str] = None
    budget: Optional[str] = None
    publish_date: Optional[str] = None
    deadline: Optional[str] = None
    category: Optional[str] = None
    business_profile: Optional[str] = None
    matched_keywords: Optional[str] = None
    relevance_score: int = 0
    raw_text: Optional[str] = None


class TenderOut(TenderIn):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CrawlRequest(BaseModel):
    config_path: str = "configs/sources.guangheng.yaml"
    export_csv: bool = True
    upload_to_dify: bool = False


class CrawlResult(BaseModel):
    source: str
    found: int
    inserted: int
    updated: int
    raw_found: int = 0
    errors: List[str] = Field(default_factory=list)


class WorkflowRequest(CrawlRequest):
    user_url: Optional[str] = None
    keyword: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    min_relevance_score: Optional[int] = Field(default=2, ge=0)


class WorkflowResponse(BaseModel):
    crawl_results: List[CrawlResult]
    exported_csv: Optional[str] = None
    dify_uploaded: bool = False
    dify_message: Optional[str] = None
    total_candidates: int = 0


class ExternalKnowledgeMetadataCondition(BaseModel):
    name: str
    comparison_operator: str
    value: Optional[Union[str, int, float, List[str]]] = None


class ExternalKnowledgeMetadataFiltering(BaseModel):
    logical_operator: Optional[str] = "and"
    conditions: List[ExternalKnowledgeMetadataCondition] = Field(default_factory=list)


class ExternalKnowledgeRetrievalSetting(BaseModel):
    top_k: int = Field(..., ge=1)
    score_threshold: float = Field(..., ge=0, le=1)


class ExternalKnowledgeRetrievalRequest(BaseModel):
    knowledge_id: str
    query: str
    retrieval_setting: ExternalKnowledgeRetrievalSetting
    metadata_condition: Optional[ExternalKnowledgeMetadataFiltering] = None


class ExternalKnowledgeRecord(BaseModel):
    content: str
    score: float
    title: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExternalKnowledgeRetrievalResponse(BaseModel):
    records: List[ExternalKnowledgeRecord]

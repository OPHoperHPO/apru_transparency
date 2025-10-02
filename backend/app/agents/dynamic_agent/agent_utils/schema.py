from __future__ import annotations
from dataclasses import dataclass
from typing import List
from pydantic import BaseModel, Field
from typing import List, Optional
class BlogProfileOut(BaseModel):
    topic_primary: str = Field(..., description="Короткая формулировка основной темы блога (1–4 слова).")
    topic_secondary: List[str] = Field(default_factory=list, description="2–6 подтем, релевантных блогу.")
    language: str = Field(..., description="Код языка: 'ru' или 'en'.")
    geo: str = Field(..., description="Гео для SEO: 'RU', 'US' и т.п.")
    tone_style: List[str] = Field(default_factory=list, description="Слова-маркеры стиля: разговорный, экспертный и т.д.")
    audience: List[str] = Field(default_factory=list, description="Целевая аудитория: маркетологи, продакты, разработчики и т.п.")
    negative_topics: List[str] = Field(default_factory=list, description="Темы, которых блог избегает.")
    evidence_samples: List[str] = Field(default_factory=list, description="2–5 цитат/заголовков из контекста, на основании которых сделан вывод.")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность 0..1")
from pydantic import BaseModel, Field
class KeywordSet(BaseModel):
    primary: List[str] = Field(default_factory=list, description="Основные ключи (в точных формулировках)")
    secondary: List[str] = Field(default_factory=list, description="Второстепенные ключи/вариации")
    lsi: List[str] = Field(default_factory=list, description="Семантически близкие фразы")
    negatives: List[str] = Field(default_factory=list, description="Минус-слова (не покрывать)")
class Brief(BaseModel):
    topic: str
    outline: List[str]
    target_keywords: KeywordSet
class ImageIdea(BaseModel):
    section: str
    prompt: str
    alt: str
class SEOData(BaseModel):
    title: str
    description: str
    schema_jsonld: str
    internal_links: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
class BriefOut(BaseModel):
    brief: Brief
class KeywordSetOut(BaseModel):
    keywordset: KeywordSet
class SEOOut(BaseModel):
    seo: SEOData
@dataclass
class Item:
    url: str
    title: str
    text: str
    source: str
    ts: float
@dataclass
class FeedInfo:
    url: str
    title: str
    description: str
class QuerySeeds(BaseModel):
    seed_terms: List[str] = Field(
        default_factory=list,
        description="30–60 seed-запросов вокруг темы блога и клиентских вопросов (точные формулировки).",
    )
    notes: str = Field(default="", description="Короткая стратегия выбора семян и источники (1–3 предложения).")
class QuerySeedsOut(BaseModel):
    query_seeds: QuerySeeds

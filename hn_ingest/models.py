"""HTTP-boundary Pydantic models for ingest and item APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class HNItemIn(BaseModel):
    """HN-shaped item. `id` is required; remaining HN fields are optional."""

    model_config = ConfigDict(extra="allow")

    id: int
    type: str | None = None
    by: str | None = None
    time: int | None = None
    title: str | None = None
    url: str | None = None
    text: str | None = None
    score: int | None = None
    parent: int | None = None
    descendants: int | None = None
    kids: list[int] | None = None
    dead: bool | None = None
    deleted: bool | None = None

    @field_validator("id")
    @classmethod
    def id_must_be_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("id must be a positive HN identifier")
        return value


class ItemsWrapper(BaseModel):
    items: list[HNItemIn]


class IngestRequest(BaseModel):
    """One HN object or {"items": [...]}."""

    model_config = ConfigDict(extra="forbid")

    items: list[HNItemIn] = Field(min_length=0)

    @model_validator(mode="before")
    @classmethod
    def accept_single_or_wrapper(cls, data: Any) -> Any:
        if isinstance(data, list):
            raise ValueError("body must be one HN object or an object with an items array")
        if not isinstance(data, dict):
            raise ValueError("body must be a JSON object")
        if "items" in data:
            return data
        return {"items": [data]}


class IngestResponse(BaseModel):
    count: int
    ids: list[int]


class HealthResponse(BaseModel):
    status: str


class DomainCount(BaseModel):
    domain: str
    count: int


class SummaryResponse(BaseModel):
    total: int
    by_type: dict[str, int]
    top_domains: list[DomainCount]
    score_buckets: dict[str, int]

"""
Reltio-compatible entity models.

Mirrors the shape of Reltio's REST API so swapping mock -> real Reltio
requires only base URL + auth changes.

Reltio attribute shape: { "AttrName": [ { "value": "..." } ] }
"""
from typing import Any
from pydantic import BaseModel, Field


class AttributeValue(BaseModel):
    value: Any
    ov: bool = True  # operational value flag


class Entity(BaseModel):
    uri: str  # e.g. "entities/abc123"
    type: str  # e.g. "configuration/entityTypes/HCP"
    attributes: dict[str, list[AttributeValue]] = Field(default_factory=dict)
    crosswalks: list[dict[str, Any]] = Field(default_factory=list)
    createdTime: int = 0
    updatedTime: int = 0


class SearchRequest(BaseModel):
    filter: str | None = None  # e.g. "equals(type,'HCP') and equals(attributes.LastName,'Chen')"
    select: str | None = None
    max: int = 25
    offset: int = 0


class CreateEntityRequest(BaseModel):
    type: str
    attributes: dict[str, list[AttributeValue]]


class MergeRequest(BaseModel):
    winnerUri: str
    loserUri: str


class PotentialMatch(BaseModel):
    uri: str
    matchScore: float
    matchRules: list[str]
    entity: Entity

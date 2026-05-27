from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

FilterOp = Literal["=", "!=", ">", ">=", "<", "<=", "in", "contains", "startswith"]
AggregateFunc = Literal["count", "sum", "avg", "min", "max"]
SortDirection = Literal["asc", "desc"]


class Filter(BaseModel):
    field: str
    op: FilterOp
    value: Any

    @model_validator(mode="after")
    def validate_value_shape(self) -> "Filter":
        if self.op == "in" and not isinstance(self.value, list):
            raise ValueError("operator 'in' requires a list value")
        if self.op != "in" and isinstance(self.value, (list, dict)):
            raise ValueError(f"operator {self.op!r} requires a scalar value")
        return self


class Aggregate(BaseModel):
    func: AggregateFunc
    field: str | None = None
    alias: str = Field(alias="as")

    @model_validator(mode="after")
    def validate_count_field(self) -> "Aggregate":
        if self.func != "count" and not self.field:
            raise ValueError(f"aggregate {self.func!r} requires a field")
        return self


class OrderBy(BaseModel):
    field: str
    direction: SortDirection = "asc"


class QueryRequest(BaseModel):
    dataset: str
    select: list[str] = Field(default_factory=list)
    filters: list[Filter] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    aggregates: list[Aggregate] = Field(default_factory=list)
    order_by: list[OrderBy] = Field(default_factory=list)
    limit: int | None = Field(default=None, ge=1)

    @field_validator("select", "group_by")
    @classmethod
    def reject_duplicate_fields(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("field lists cannot contain duplicates")
        return value


class QueryResponse(BaseModel):
    rows: list[dict[str, Any]]
    row_count: int
    columns: list[str]
    query_ms: int
    dataset: str

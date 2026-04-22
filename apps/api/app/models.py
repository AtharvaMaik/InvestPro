from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class FactorSelection(BaseModel):
    id: str
    weight: float


class BacktestRequest(BaseModel):
    dataSource: Literal["demo", "live"] = "demo"
    universeId: str
    customSymbols: list[str] = Field(default_factory=list)
    startDate: date
    endDate: date
    rebalanceFrequency: Literal["monthly", "quarterly"] = "monthly"
    weightingMethod: Literal["equal", "score", "volatility"] = "equal"
    topN: int = Field(ge=1, le=50)
    transactionCostBps: float = Field(ge=0, le=200)
    factors: list[FactorSelection]
    benchmarks: list[str] = Field(default_factory=list)
    mutualFunds: list[str] = Field(default_factory=list)

    @field_validator("factors")
    @classmethod
    def require_factors(cls, value: list[FactorSelection]) -> list[FactorSelection]:
        if not value:
            raise ValueError("At least one factor is required.")
        if sum(abs(factor.weight) for factor in value) == 0:
            raise ValueError("At least one factor weight must be non-zero.")
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "BacktestRequest":
        if self.startDate >= self.endDate:
            raise ValueError("startDate must be before endDate.")
        return self


class WarningMessage(BaseModel):
    code: str
    message: str


class ComparisonResult(BaseModel):
    id: str
    name: str
    type: Literal["benchmark", "mutual_fund"]
    metrics: dict[str, float | None]
    monthlyWinRate: float | None


class BacktestResponse(BaseModel):
    id: str
    status: Literal["completed"]
    config: dict
    summary: dict[str, int | str]
    metrics: dict[str, dict[str, float | None]]
    series: dict
    holdings: list[dict]
    comparisons: list[ComparisonResult]
    factorDiagnostics: list[dict] = Field(default_factory=list)
    robustness: list[dict] = Field(default_factory=list)
    warnings: list[WarningMessage]

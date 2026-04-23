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
    trendFilter: bool = False
    sectorNeutral: bool = False
    maxSectorWeight: float = Field(default=0.3, ge=0.05, le=1.0)
    maxPositionWeight: float = Field(default=0.1, ge=0.01, le=1.0)
    minLiquidityCrore: float = Field(default=0, ge=0)
    maxAnnualTurnover: float = Field(default=3.0, ge=0.1, le=20)
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
    category: str | None = None
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
    sectorExposure: list[dict] = Field(default_factory=list)
    fundCategoryComparison: list[dict] = Field(default_factory=list)
    rollingAnalysis: dict = Field(default_factory=dict)
    walkForward: dict = Field(default_factory=dict)
    dataConfidence: dict = Field(default_factory=dict)
    investability: dict = Field(default_factory=dict)
    riskBudget: dict = Field(default_factory=dict)
    researchVerdict: dict = Field(default_factory=dict)
    rebalanceJournal: list[dict] = Field(default_factory=list)
    actionList: list[dict] = Field(default_factory=list)
    warnings: list[WarningMessage]

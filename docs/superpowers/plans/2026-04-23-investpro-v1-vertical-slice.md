# InvestPro V1 Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working InvestPro vertical slice: deterministic quant backend, FastAPI endpoints, Next.js research workspace, and demo factor backtest with mutual fund comparison.

**Architecture:** Use a repo-level app split with `apps/api` for FastAPI/Python quant code and `apps/web` for Next.js/TypeScript UI. Start with seeded demo data so the full flow works offline, then keep provider interfaces ready for live data later.

**Tech Stack:** Python, FastAPI, Pandas, NumPy, Pytest, Next.js, TypeScript, Tailwind CSS, Recharts, Framer Motion.

---

## File Structure

- Create `apps/api/pyproject.toml`: Python project metadata and dependencies.
- Create `apps/api/app/main.py`: FastAPI app and route registration.
- Create `apps/api/app/models.py`: Pydantic request and response contracts.
- Create `apps/api/app/data/demo.py`: deterministic seeded price, benchmark, and mutual fund data.
- Create `apps/api/app/quant/factors.py`: factor math.
- Create `apps/api/app/quant/metrics.py`: performance metrics.
- Create `apps/api/app/quant/backtest.py`: portfolio simulation and comparison orchestration.
- Create `apps/api/tests/test_metrics.py`: deterministic metric tests.
- Create `apps/api/tests/test_factors.py`: factor and ranking tests.
- Create `apps/api/tests/test_api.py`: endpoint tests.
- Create `apps/web/package.json`: frontend scripts and dependencies.
- Create `apps/web/src/app/page.tsx`: main research workspace.
- Create `apps/web/src/app/layout.tsx`: app shell metadata.
- Create `apps/web/src/app/globals.css`: responsive layout, design tokens, and motion polish.
- Create `apps/web/src/lib/api.ts`: backend API client and types.
- Create `apps/web/src/components/strategy-builder.tsx`: strategy controls.
- Create `apps/web/src/components/results-dashboard.tsx`: charts, metrics, comparisons, holdings.
- Create `README.md`: setup, run, and project overview.

## Task 1: Backend Project Scaffold

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/main.py`
- Test: none

- [ ] **Step 1: Create Python project metadata**

```toml
[project]
name = "investpro-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pandas>=2.2.0",
  "numpy>=2.0.0",
  "pydantic>=2.8.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "httpx>=0.27.0"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create FastAPI health route**

```python
from fastapi import FastAPI

app = FastAPI(title="InvestPro API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "investpro-api", "version": "0.1.0"}
```

- [ ] **Step 3: Run API smoke check**

Run: `cd apps/api; python -m uvicorn app.main:app --port 8000`

Expected: Uvicorn starts and `/health` returns the JSON from Step 2.

- [ ] **Step 4: Commit**

Run: `git add apps/api && git commit -m "feat: scaffold InvestPro API"`

## Task 2: Quant Metrics

**Files:**
- Create: `apps/api/app/quant/__init__.py`
- Create: `apps/api/app/quant/metrics.py`
- Create: `apps/api/tests/test_metrics.py`

- [ ] **Step 1: Write failing metric tests**

```python
import math
import pandas as pd

from app.quant.metrics import calculate_metrics, drawdown_series


def test_drawdown_series_tracks_peak_to_trough():
    wealth = pd.Series([1.0, 1.2, 0.9, 1.5])
    result = drawdown_series(wealth)
    assert result.round(4).tolist() == [0.0, 0.0, -0.25, 0.0]


def test_calculate_metrics_for_simple_daily_returns():
    returns = pd.Series([0.01, -0.02, 0.03, 0.01])
    metrics = calculate_metrics(returns, periods_per_year=252)
    assert metrics.total_return > 0
    assert metrics.volatility > 0
    assert metrics.max_drawdown < 0
    assert math.isfinite(metrics.sharpe)
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd apps/api; pytest tests/test_metrics.py -v`

Expected: FAIL because `app.quant.metrics` does not exist.

- [ ] **Step 3: Implement metrics**

```python
from dataclasses import dataclass
import math
import pandas as pd


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    cagr: float | None
    volatility: float | None
    sharpe: float | None
    sortino: float | None
    max_drawdown: float | None
    calmar: float | None


def wealth_index(returns: pd.Series) -> pd.Series:
    return (1 + returns.fillna(0)).cumprod()


def drawdown_series(wealth: pd.Series) -> pd.Series:
    peaks = wealth.cummax()
    return (wealth / peaks) - 1


def calculate_metrics(
    returns: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> PerformanceMetrics:
    clean = returns.dropna()
    if clean.empty:
        return PerformanceMetrics(0.0, None, None, None, None, None, None)

    wealth = wealth_index(clean)
    total_return = float(wealth.iloc[-1] - 1)
    years = len(clean) / periods_per_year
    cagr = float((wealth.iloc[-1] ** (1 / years)) - 1) if years > 0 else None
    volatility = float(clean.std(ddof=1) * math.sqrt(periods_per_year)) if len(clean) > 1 else None
    downside = clean.clip(upper=0)
    downside_vol = float(downside.std(ddof=1) * math.sqrt(periods_per_year)) if len(clean) > 1 else None
    sharpe = (cagr - risk_free_rate) / volatility if cagr is not None and volatility and volatility != 0 else None
    sortino = (cagr - risk_free_rate) / downside_vol if cagr is not None and downside_vol and downside_vol != 0 else None
    max_drawdown = float(drawdown_series(wealth).min())
    calmar = cagr / abs(max_drawdown) if cagr is not None and max_drawdown != 0 else None
    return PerformanceMetrics(total_return, cagr, volatility, sharpe, sortino, max_drawdown, calmar)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cd apps/api; pytest tests/test_metrics.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add apps/api/app/quant apps/api/tests/test_metrics.py && git commit -m "feat: add quant performance metrics"`

## Task 3: Factor Ranking

**Files:**
- Create: `apps/api/app/quant/factors.py`
- Create: `apps/api/tests/test_factors.py`

- [ ] **Step 1: Write factor tests**

```python
import pandas as pd

from app.quant.factors import zscore_factor, composite_scores


def test_zscore_factor_inverts_lower_is_better():
    values = pd.Series({"A": 0.10, "B": 0.20, "C": 0.30})
    scores = zscore_factor(values, higher_is_better=False)
    assert scores["A"] > scores["C"]


def test_composite_scores_use_weights():
    factors = {
        "momentum": pd.Series({"A": 1.0, "B": 0.0}),
        "risk": pd.Series({"A": 0.0, "B": 1.0}),
    }
    scores = composite_scores(factors, {"momentum": 0.75, "risk": 0.25})
    assert scores["A"] > scores["B"]
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd apps/api; pytest tests/test_factors.py -v`

Expected: FAIL because factor functions do not exist.

- [ ] **Step 3: Implement factor scoring**

```python
import pandas as pd


def winsorize(values: pd.Series, lower: float = 0.05, upper: float = 0.95) -> pd.Series:
    clean = values.dropna()
    if clean.empty:
        return values
    low = clean.quantile(lower)
    high = clean.quantile(upper)
    return values.clip(lower=low, upper=high)


def zscore_factor(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    clipped = winsorize(values.astype(float))
    std = clipped.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=values.index)
    z = (clipped - clipped.mean()) / std
    return z if higher_is_better else -z


def composite_scores(factor_scores: dict[str, pd.Series], weights: dict[str, float]) -> pd.Series:
    total_weight = sum(abs(weight) for weight in weights.values())
    if total_weight == 0:
        raise ValueError("At least one factor weight must be non-zero.")
    normalized = {key: value / total_weight for key, value in weights.items()}
    result = None
    for factor_id, scores in factor_scores.items():
        weighted = scores.fillna(0) * normalized.get(factor_id, 0)
        result = weighted if result is None else result.add(weighted, fill_value=0)
    return result.sort_values(ascending=False)
```

- [ ] **Step 4: Run tests**

Run: `cd apps/api; pytest tests/test_factors.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add apps/api/app/quant/factors.py apps/api/tests/test_factors.py && git commit -m "feat: add factor scoring"`

## Task 4: Demo Data And Backtest API

**Files:**
- Create: `apps/api/app/models.py`
- Create: `apps/api/app/data/__init__.py`
- Create: `apps/api/app/data/demo.py`
- Create: `apps/api/app/quant/backtest.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_api.py`

- [ ] **Step 1: Define tests for metadata and default backtest**

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_backtest_default_config_returns_series_and_comparisons():
    payload = {
        "universeId": "nifty50-demo",
        "customSymbols": [],
        "startDate": "2020-01-01",
        "endDate": "2024-12-31",
        "rebalanceFrequency": "monthly",
        "topN": 5,
        "transactionCostBps": 25,
        "factors": [{"id": "momentum_6m", "weight": 1.0}],
        "benchmarks": ["nifty50-demo"],
        "mutualFunds": ["ppfas-flexi-demo"]
    }
    response = client.post("/backtests", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["series"]["equityCurve"]
    assert body["comparisons"]
    assert body["holdings"]
```

- [ ] **Step 2: Run tests to confirm failure**

Run: `cd apps/api; pytest tests/test_api.py -v`

Expected: FAIL because routes and models are incomplete.

- [ ] **Step 3: Implement Pydantic models**

Use models that match `project_details.md`: factor selections, backtest request, metrics, chart points, holdings, comparisons, and warnings.

- [ ] **Step 4: Implement deterministic demo provider**

Use seeded generated daily business-day data for 12 Indian stock symbols, one benchmark, and one mutual fund. Keep generation deterministic with a fixed random seed so tests are stable.

- [ ] **Step 5: Implement backtest orchestration**

Calculate monthly rebalances, momentum ranking, equal-weight holdings, daily returns, transaction cost, metrics, benchmark comparison, mutual fund comparison, holdings, and warnings.

- [ ] **Step 6: Wire API routes**

Expose `/universes`, `/factors`, `/benchmarks`, `/mutual-funds/search`, `/backtests`, and `/backtests/{id}`.

- [ ] **Step 7: Run API tests**

Run: `cd apps/api; pytest -v`

Expected: PASS.

- [ ] **Step 8: Commit**

Run: `git add apps/api && git commit -m "feat: add demo backtest API"`

## Task 5: Frontend Scaffold

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/globals.css`

- [ ] **Step 1: Create Next.js app metadata**

Use Next.js with TypeScript, React, Tailwind CSS, Recharts, and Framer Motion.

- [ ] **Step 2: Create app shell**

Render the research workspace immediately on `/` with no marketing landing page.

- [ ] **Step 3: Add global styles**

Define spacing tokens, responsive grids, tabular numbers, accessible focus states, smooth transitions, and reduced-motion handling.

- [ ] **Step 4: Run frontend build**

Run: `cd apps/web; npm install; npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add apps/web && git commit -m "feat: scaffold InvestPro web app"`

## Task 6: Frontend API Client And Strategy Builder

**Files:**
- Create: `apps/web/src/lib/api.ts`
- Create: `apps/web/src/components/strategy-builder.tsx`
- Modify: `apps/web/src/app/page.tsx`

- [ ] **Step 1: Add typed API client**

Define TypeScript types matching backend responses and functions for metadata endpoints and `runBacktest`.

- [ ] **Step 2: Add strategy builder**

Build controls for universe, date range, factor weights, top-N, transaction cost, benchmark, and mutual fund selection.

- [ ] **Step 3: Add validation**

Block submission if date range is invalid, no factor has positive weight, or transaction cost is outside 0-200 bps.

- [ ] **Step 4: Run lint/build**

Run: `cd apps/web; npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

Run: `git add apps/web && git commit -m "feat: add strategy builder"`

## Task 7: Results Dashboard

**Files:**
- Create: `apps/web/src/components/results-dashboard.tsx`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/globals.css`

- [ ] **Step 1: Render metrics**

Show CAGR, total return, volatility, Sharpe, Sortino, max drawdown, Calmar, annual turnover, and transaction cost drag using tabular numbers.

- [ ] **Step 2: Render charts**

Use Recharts for equity curve, drawdown, rolling returns, and monthly returns.

- [ ] **Step 3: Render comparisons and holdings**

Show benchmark/mutual fund comparison table and holdings by rebalance date.

- [ ] **Step 4: Add smooth motion**

Use Framer Motion for subtle result entrance and respect `prefers-reduced-motion`.

- [ ] **Step 5: Verify responsiveness**

Check desktop, tablet, and mobile widths. No overlapping text, chart collapse, or shifting button dimensions.

- [ ] **Step 6: Commit**

Run: `git add apps/web && git commit -m "feat: add results dashboard"`

## Task 8: Documentation And Verification

**Files:**
- Create or modify: `README.md`
- Modify: `project_details.md` only if implementation reveals a contract mismatch.

- [ ] **Step 1: Document setup**

Include commands for installing backend dependencies, running API, installing frontend dependencies, and running the web app.

- [ ] **Step 2: Run backend tests**

Run: `cd apps/api; pytest -v`

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run: `cd apps/web; npm run build`

Expected: PASS.

- [ ] **Step 4: Run full local smoke test**

Start API on port 8000 and web on port 3000, open the app, run default strategy, and verify the dashboard renders metrics, charts, comparison, and holdings.

- [ ] **Step 5: Commit**

Run: `git add README.md project_details.md apps && git commit -m "docs: add InvestPro setup and verification notes"`

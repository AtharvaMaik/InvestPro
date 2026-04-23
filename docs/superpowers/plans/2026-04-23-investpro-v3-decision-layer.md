# InvestPro V3 Decision Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add V3 decision support fields and dashboard panels that make InvestPro research results auditable and investable.

**Architecture:** Keep the current FastAPI/Pandas backtest engine as the source of performance truth. Add a decision layer at the end of `run_backtest` that consumes holdings, warnings, metrics, factor coverage, liquidity, sector exposure, and walk-forward results. The Next.js dashboard renders the new sections without adding a separate route.

**Tech Stack:** FastAPI, Pydantic, Pandas, Next.js App Router, TypeScript, Recharts.

---

## Tasks

- [ ] Add API tests asserting V3 response sections exist and contain verdict/check fields.
- [ ] Extend `BacktestRequest` and `BacktestResponse` in `apps/api/app/models.py`.
- [ ] Track factor coverage, latest liquidity, rebalance adds/removes/retained, and data provider warnings in `apps/api/app/quant/backtest.py`.
- [ ] Implement `dataConfidence`, `investability`, `riskBudget`, `researchVerdict`, and `rebalanceJournal` helper functions.
- [ ] Update frontend API types in `apps/web/src/lib/api.ts`.
- [ ] Add strategy builder controls for max position weight, minimum liquidity, and turnover budget.
- [ ] Add result panels for research verdict, data confidence, investability, risk budget, and rebalance journal.
- [ ] Update guide and project details docs.
- [ ] Run `python -m pytest -v`, `npm run build`, smoke check local routes, commit, push, and restart services.

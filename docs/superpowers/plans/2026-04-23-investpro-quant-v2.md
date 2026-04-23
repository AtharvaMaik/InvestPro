# InvestPro Quant V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add live-aware fundamental factors, sector-aware construction, trend and drawdown controls, benchmark-relative momentum, mutual fund category comparison, rolling analysis, and walk-forward validation.

**Architecture:** Extend the existing FastAPI/Pandas quant pipeline instead of adding a separate service. Demo providers supply deterministic sector/fundamental data; live providers enrich from Yahoo Finance when available and fail softly with warnings. The Next.js dashboard consumes the expanded response without changing the single-page workspace model.

**Tech Stack:** FastAPI, Pydantic, Pandas, yfinance, MFAPI, Next.js App Router, TypeScript, Recharts, Framer Motion.

---

## File Map

- Modify `apps/api/app/models.py`: request toggles and response fields.
- Modify `apps/api/app/data/demo.py`: sector map, richer factor metadata, seeded fundamentals, fund categories.
- Modify `apps/api/app/data/live.py`: live fundamentals adapter and curated fund categories.
- Modify `apps/api/app/quant/factors.py`: trend, drawdown, relative momentum helpers.
- Modify `apps/api/app/quant/backtest.py`: filters, sector caps, category comparisons, rolling returns, walk-forward.
- Modify `apps/api/tests/test_api.py` and `apps/api/tests/test_factors.py`: regression coverage.
- Modify `apps/web/src/lib/api.ts`: expanded types.
- Modify `apps/web/src/app/page.tsx`: Quant v2 defaults.
- Modify `apps/web/src/components/strategy-builder.tsx`: trend and sector controls.
- Modify `apps/web/src/components/results-dashboard.tsx`: new analytics panels.
- Modify `apps/web/src/lib/glossary.ts` and `apps/web/src/app/globals.css`: explanations and layout polish.
- Modify `project_details.md`: exact Quant v2 math and flow.

## Tasks

- [ ] Add failing tests for new factor helpers: 200-day trend, trailing drawdown, and benchmark-relative momentum.
- [ ] Implement the factor helpers in `apps/api/app/quant/factors.py`.
- [ ] Add API tests for trend filtering, sector caps, rolling analysis, walk-forward, and category comparison response fields.
- [ ] Extend request and response models with `trendFilter`, `sectorNeutral`, `maxSectorWeight`, `sectorExposure`, `fundCategoryComparison`, `rollingAnalysis`, and `walkForward`.
- [ ] Add seeded sector/fundamental data and expanded factor metadata.
- [ ] Add live fundamentals fetch with Yahoo Finance metadata, per-symbol failure tolerance, and warnings.
- [ ] Apply trend filtering before ranking and sector caps during final stock selection.
- [ ] Add mutual fund category aggregation, rolling returns, and walk-forward validation to the backtest response.
- [ ] Update TypeScript types and default strategy weights.
- [ ] Add frontend controls for trend filter and sector cap.
- [ ] Add frontend panels for sector exposure, fund categories, rolling analysis, and walk-forward validation.
- [ ] Update `project_details.md` with formulas and API behavior.
- [ ] Run `python -m pytest -v`, `npm run build`, a live smoke backtest, restart services, commit, and push.

# InvestPro Live Presets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert app usage to live-only mode, add strategy presets, produce latest stock research actions, and fix responsive dashboard scaling.

**Architecture:** Keep demo helpers for tests but remove demo from the user-facing app path. Add action-list calculation at the end of the existing backtest engine. Add frontend-only preset definitions that map to the existing `BacktestRequest` shape.

**Tech Stack:** FastAPI, Pydantic, Pandas, Next.js App Router, TypeScript, CSS Grid.

---

## Tasks

- [ ] Update API tests to assert live-facing metadata and action-list output.
- [ ] Change app metadata endpoints to return live-labeled universe and benchmark information.
- [ ] Remove silent demo fallback for live price, benchmark, mutual fund, and fundamentals providers.
- [ ] Add `actionList` to the backtest response.
- [ ] Add frontend strategy preset definitions and preset cards.
- [ ] Make frontend default data source live and remove the data source selector.
- [ ] Move guide link into top navigation and improve CSS grid responsiveness.
- [ ] Run backend tests, web build, live smoke check, commit, push, and restart services.

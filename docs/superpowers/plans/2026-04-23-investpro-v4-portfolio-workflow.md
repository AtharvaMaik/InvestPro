# InvestPro V4 Portfolio Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add portfolio capital, current holdings, target allocations, rebalance trades, and execution safety checks.

**Architecture:** Extend the existing FastAPI backtest response with portfolio workflow calculations after latest holdings are known. Keep the frontend single-page workflow and add a compact Portfolio Setup section plus results panels.

**Tech Stack:** FastAPI, Pydantic, Pandas, Next.js, TypeScript, CSS Grid.

---

## Tasks

- [ ] Add backend tests for `allocationPlan`, `rebalanceTrades`, and `executionChecklist`.
- [ ] Extend `BacktestRequest` with `portfolioCapital` and `currentHoldings`.
- [ ] Compute latest price map from the existing price frame.
- [ ] Build allocation plan from latest target weights.
- [ ] Classify rebalance trades against current holdings.
- [ ] Add execution checklist helper.
- [ ] Extend TypeScript request and response types.
- [ ] Add Portfolio Setup controls to the builder.
- [ ] Add Allocation Plan, Rebalance Trades, and Execution Checklist panels.
- [ ] Improve Balanced Compounder preset defaults and documentation.
- [ ] Run tests/build, smoke check, restart services, commit, push.

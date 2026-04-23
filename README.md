# InvestPro

InvestPro is an Indian equity research tool for people who want to pick stocks more carefully.

It helps you build a rules-based stock selection strategy, test how it would have behaved in the past, compare it with Nifty and mutual funds, and turn the result into a practical portfolio action list.

This is not investment advice. It is a research and learning tool.

## Who This Is For

InvestPro is useful if you are:

- New to investing and want to understand what makes a stock attractive.
- Learning quant finance, factor investing, or portfolio construction.
- Comparing active stock picking against mutual funds.
- Building a finance or data science portfolio project.
- Trying to avoid buying stocks only because they are popular on social media.

## What The App Does

In simple terms, InvestPro asks:

1. Which stocks are we allowed to choose from?
2. Which factors should matter?
3. How much should each factor matter?
4. Which stocks score best today?
5. How would this strategy have performed historically?
6. Did it beat a benchmark or mutual funds?
7. If I already own some stocks, what would the model suggest I buy, add, trim, hold, or exit?

The app then shows:

- Strategy performance.
- Risk and drawdown.
- Mutual fund comparisons.
- Factor diagnostics.
- Buy, sell, and hold actions.
- Portfolio allocation in rupees.
- A timeline of when stocks entered or exited the strategy.

## Beginner Investing Glossary

### Stock

A stock is a small ownership share in a company. If you buy shares of Reliance, TCS, or HDFC Bank, you own a tiny part of that business.

### Portfolio

A portfolio is the collection of investments you own. For example:

- Reliance: Rs 50,000
- TCS: Rs 40,000
- HDFC Bank: Rs 35,000

Together, these make up your portfolio.

### Capital

Capital is the total amount of money you want to invest or analyze. In InvestPro, portfolio capital is used to convert percentage weights into rupee allocations.

Example:

```text
Capital = Rs 500,000
Target weight for TCS = 10%
Target value for TCS = Rs 50,000
```

### Share Quantity

Share quantity means how many shares you own.

If TCS trades at Rs 4,000 and you own 5 shares:

```text
Current value = 5 * 4,000 = Rs 20,000
```

### Benchmark

A benchmark is the thing you compare your strategy against.

For Indian large-cap stocks, a common benchmark is Nifty 50. If your strategy takes more effort and risk than simply buying the index, it should ideally show a good reason for that extra effort.

### Mutual Fund

A mutual fund pools money from many investors and invests it according to a fund manager's strategy.

InvestPro compares the stock strategy with mutual fund categories such as:

- Large-cap funds
- Flexi-cap funds
- Mid-cap funds
- ELSS funds
- Index funds

This helps answer: "Was this stock-picking strategy actually better than a professionally managed fund?"

### Factor

A factor is a measurable trait used to rank stocks.

Instead of saying "I like this company", a factor says "I like stocks with this measurable property."

InvestPro uses factors such as:

- Momentum
- Relative momentum
- Trend
- Drawdown
- Liquidity
- ROE
- ROCE
- Debt to equity
- Earnings growth
- P/E
- P/B

### Momentum

Momentum measures whether a stock has been going up over a recent period.

Example:

```text
6-month momentum = Stock price today / Stock price 6 months ago - 1
```

High momentum means the stock has been strong recently.

### Relative Momentum

Relative momentum compares a stock against the benchmark.

A stock going up 8% may look good, but if Nifty went up 12%, the stock actually underperformed the market.

InvestPro prefers stocks that are not just rising, but rising more strongly than Nifty.

### Trend Filter

The trend filter checks whether a stock is above its 200-day moving average.

Beginner version:

- Above 200-day average: trend is healthier.
- Below 200-day average: trend may be weak or risky.

### Drawdown

Drawdown means how much an investment has fallen from its previous high.

Example:

```text
Stock high = Rs 1,000
Current price = Rs 750
Drawdown = -25%
```

Large drawdowns can signal risk, stress, or broken momentum.

### Liquidity

Liquidity means how easy it is to buy or sell a stock without affecting its price too much.

Highly traded stocks are usually more liquid. Illiquid stocks can be harder to exit, especially during market stress.

### ROE

ROE means return on equity.

It measures how efficiently a company generates profit from shareholder money. Higher ROE is generally better, but it should not be viewed alone.

### ROCE

ROCE means return on capital employed.

It measures how efficiently a company uses all capital in the business, including debt. It is useful for comparing business quality.

### Debt To Equity

Debt to equity measures how much debt a company has compared with shareholder equity.

Lower debt is usually safer, especially in weak markets or high-interest-rate periods.

### Earnings Growth

Earnings growth measures whether the company's profits are growing.

A business with rising profits is often healthier than one with flat or falling profits.

### P/E Ratio

P/E means price-to-earnings ratio.

It roughly answers: "How much are investors paying for each rupee of company profit?"

A lower P/E can mean cheaper valuation, but sometimes a stock is cheap for a reason.

### P/B Ratio

P/B means price-to-book ratio.

It compares the market price of a company with its accounting book value. It is often used for banks, financial companies, and asset-heavy businesses.

### CAGR

CAGR means compound annual growth rate.

It answers: "What yearly return would produce the same total result?"

Example:

```text
Rs 100 grows to Rs 161 in 5 years
CAGR is about 10% per year
```

### Volatility

Volatility measures how much returns move up and down.

Higher volatility means a bumpier ride. Lower volatility means smoother returns.

### Sharpe Ratio

Sharpe ratio compares return with risk.

Higher Sharpe means the strategy earned more return per unit of volatility.

### Sortino Ratio

Sortino is similar to Sharpe, but it focuses more on downside volatility.

That means it cares more about harmful volatility than upside movement.

### Calmar Ratio

Calmar compares return with maximum drawdown.

It asks: "Was the return worth the worst fall?"

### Turnover

Turnover measures how much of the portfolio changes during rebalancing.

High turnover can mean:

- More trading.
- More transaction costs.
- More tax friction.
- More effort.

### Rebalancing

Rebalancing means updating the portfolio at fixed intervals.

For example, a quarterly strategy reviews the portfolio every three months and decides what to buy, sell, add, trim, or hold.

### Transaction Cost

Transaction cost is the estimated cost of trading.

It includes things like brokerage, slippage, taxes, and bid-ask spread. Even a good strategy can look worse after realistic trading costs.

### Sector Neutrality

Sector neutrality prevents the strategy from accidentally buying too many stocks from one sector.

Without this, a strategy could become all banks, all IT, or all metals without the user realizing it.

### Walk-Forward Testing

Walk-forward testing splits history into two parts:

1. Train or choose settings on an earlier period.
2. Test those settings on a later unseen period.

This helps reduce overfitting.

### Overfitting

Overfitting means building a strategy that looks amazing in the past but fails in the future because it was too tuned to historical noise.

InvestPro uses robustness checks, rolling analysis, and walk-forward testing to make this risk more visible.

## How To Use InvestPro As A Beginner

### Step 1: Start With A Preset

Use a preset instead of manually changing every factor on day one.

Good starting point:

- Balanced Compounder for a broad quality plus momentum strategy.
- Low Volatility Defensive if you care more about smoother performance.
- Momentum Leader if you understand that it may trade more and fall harder.
- Quality Value if you want fundamentals and valuation to matter more.

### Step 2: Choose The Stock Universe

The universe is the list of stocks the strategy can choose from.

If a stock is not in the universe, the strategy will not buy it.

### Step 3: Pick A Date Range

A longer date range gives more context.

Try to include different market conditions:

- Bull markets.
- Sideways markets.
- Crashes.
- Recoveries.

### Step 4: Review The Factor Weights

Factor weights decide how important each signal is.

Example:

```text
Momentum weight = 0.20
ROE weight = 0.10
Debt weight = 0.05
```

This means momentum matters more than debt in that strategy.

### Step 5: Run The Backtest

Click `Run backtest`.

Do not look only at total return. Also check:

- Max drawdown.
- Sharpe.
- Turnover.
- Sector exposure.
- Mutual fund comparison.
- Walk-forward result.
- Data confidence.

### Step 6: Add Your Current Holdings

In Portfolio Setup:

1. Search for a stock by symbol, name, or sector.
2. Add it to current holdings.
3. Enter either current value or share quantity.
4. Run the backtest.

InvestPro will compare your current holdings with the model portfolio.

### Step 7: Read The Action List Carefully

Actions mean:

- Buy: model wants a new position.
- Add: you own it, but model target is higher.
- Trim: you own too much compared with target.
- Hold: current exposure is close enough.
- Exit: stock is no longer selected by the strategy.
- Avoid: stock fails important checks.

These are research actions, not automatic orders.

### Step 8: Compare Against Mutual Funds

If the strategy does not clearly beat mutual funds after risk, drawdown, and turnover, a fund may be the more practical choice.

The goal is not to prove stock picking is always better.

The goal is to know when it is not worth the effort.

## What A Good Result Looks Like

A stronger strategy usually has:

- Good CAGR.
- Lower or acceptable max drawdown.
- Sharpe and Sortino better than comparisons.
- Reasonable turnover.
- No extreme sector concentration.
- Consistent rolling performance.
- Positive walk-forward behavior.
- Clear factor evidence.
- Medium or high data confidence.

## What A Bad Result Looks Like

Be careful if:

- Returns only look good in one short period.
- Drawdown is very high.
- Turnover is extreme.
- One sector dominates the portfolio.
- The strategy loses to simple mutual funds.
- Walk-forward performance collapses.
- Data confidence is low.
- Most selected stocks have weak explanations.

## How The Strategy Is Built

At each rebalance date, InvestPro:

1. Gets price, benchmark, mutual fund, and fundamental data.
2. Calculates factor values for every stock.
3. Standardizes each factor so different units can be compared.
4. Inverts lower-is-better factors such as volatility, debt, P/E, and P/B.
5. Multiplies each factor by its selected weight.
6. Adds the weighted scores into one composite score.
7. Ranks stocks from highest score to lowest score.
8. Applies trend, liquidity, position size, and sector rules.
9. Selects the top stocks.
10. Assigns target weights.
11. Simulates returns until the next rebalance.
12. Applies transaction costs.
13. Compares the result against benchmarks and mutual funds.

## Repository Layout

```text
apps/
  api/   FastAPI backend and quant engine
  web/   Next.js frontend dashboard
docs/
  superpowers/
    specs/  Product design specs
    plans/  Implementation plans
project_details.md  Math, API, UI, and flow contract
pytest.ini          Root test configuration
```

## Run The Backend Locally

```powershell
cd apps/api
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Run Backend Tests

```powershell
python -m pytest -v
```

## Run The Frontend Locally

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

The frontend uses `http://localhost:8000` in development and `/api` in production.

To override the API URL:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
npm run dev
```

## Build The Frontend

```powershell
cd apps/web
npm run build
```

## Deploy

This repo is configured for a Vercel multi-service deployment:

- Next.js frontend at `/`.
- FastAPI backend at `/api`.

Production frontend requests use `/api`, so the browser can call the backend on the same deployed domain.

Deploy with:

```powershell
npx vercel --prod
```

## Live Data Sources

Live mode uses:

- `yfinance` for NSE stock and Nifty price history.
- `yfinance` company info for fundamentals where available.
- MFAPI for Indian mutual fund search and NAV history.

Provider availability can change. If a live provider fails, the API returns a provider error instead of silently pretending fake data is live data.

## Current Limitations

- Live market data depends on external providers.
- Provider responses are not yet cached in a production database.
- No user accounts or saved portfolios yet.
- No tax optimization yet.
- No broker integration.
- No personalized investment advice.

## Responsible Use

Use InvestPro to ask better questions, not to blindly place trades.

Before acting on any result:

1. Check recent company news.
2. Confirm data confidence.
3. Understand why each stock was selected.
4. Compare with mutual fund alternatives.
5. Consider taxes, costs, and your own risk tolerance.
6. Start small or paper trade before using real capital.

import Link from "next/link";

const v3Items = [
  {
    title: "Data Confidence Layer",
    body: "Now part of V3: shows price coverage, fundamental coverage, factor coverage, provider warnings, and an overall confidence level."
  },
  {
    title: "Portfolio Sizing Guardrails",
    body: "Now part of V3: checks max stock weight, minimum liquidity, turnover budget, sector concentration, and holding count."
  },
  {
    title: "Risk Budget View",
    body: "Now part of V3: translates volatility, drawdown, and concentration into conservative, balanced, aggressive, or speculative risk bands."
  },
  {
    title: "Rebalance Journal",
    body: "Now part of V3: records which stocks entered, exited, and stayed at each rebalance, with the strongest factor reasons."
  },
  {
    title: "Scenario Tests",
    body: "Stress the strategy in high-rate, crash, sideways, and bull-market windows instead of relying on one full-period backtest."
  },
  {
    title: "Deployment Checklist",
    body: "Require paper-trading, allocation limits, tax review, and advisor review before treating research output as an investable plan."
  }
];

const factorGuides = [
  {
    title: "Momentum",
    use: "Use it when you want market leadership and trend persistence.",
    caution: "Reduce its weight when the portfolio becomes crowded, very cyclical, or deeply overvalued."
  },
  {
    title: "Relative Momentum",
    use: "Use it to prefer stocks beating Nifty rather than stocks that only rose because the whole market rose.",
    caution: "It can lag when beaten-down value stocks recover sharply."
  },
  {
    title: "Trend Filter",
    use: "Use it as a gatekeeper. Stocks below the 200-day moving average should usually prove themselves again before entry.",
    caution: "It can exit late in fast crashes and re-enter late in fast rebounds."
  },
  {
    title: "Drawdown",
    use: "Use it to avoid stocks with recent deep damage even if short-term momentum looks attractive.",
    caution: "Too much drawdown penalty can over-favor defensive names."
  },
  {
    title: "Quality",
    use: "Use ROE, ROCE, and earnings growth to prefer companies that create value instead of only stocks that moved up.",
    caution: "Accounting values can be stale, cyclical, or distorted by one-off events."
  },
  {
    title: "Value",
    use: "Use P/E and P/B to avoid paying any price for growth.",
    caution: "Cheap stocks can stay cheap for good reasons; pair value with quality and trend."
  },
  {
    title: "Leverage",
    use: "Use debt/equity to avoid fragile balance sheets.",
    caution: "Some sectors naturally carry more debt, so compare within sector where possible."
  },
  {
    title: "Liquidity",
    use: "Use it to keep the strategy realistic for entry, exit, and slippage.",
    caution: "High liquidity tilts toward large caps and can miss smaller winners."
  }
];

const workflow = [
  "Start with your goal: wealth creation, benchmark replacement, satellite stock basket, or research only.",
  "Choose a universe you can actually invest in and track.",
  "Turn on the 200-day trend filter and sector cap for a default risk-aware setup.",
  "Use a balanced factor stack instead of one hero factor.",
  "Compare against the right mutual fund category, not only the easiest benchmark to beat.",
  "Check rolling returns and walk-forward results before trusting the headline CAGR.",
  "Read the latest holdings as research candidates, not automatic buy orders.",
  "Paper trade or allocate a small satellite amount before scaling."
];

export const metadata = {
  title: "InvestPro Guide",
  description: "How to choose factors and use InvestPro responsibly"
};

export default function GuidePage() {
  return (
    <main className="guide-shell">
      <nav className="guide-nav" aria-label="Guide navigation">
        <Link href="/">InvestPro Lab</Link>
        <span>Guide</span>
      </nav>

      <section className="guide-hero">
        <span className="eyebrow">Quant V3 Roadmap</span>
        <h1>Use InvestPro as a decision-quality research terminal.</h1>
        <p>
          V3 turns a backtest into an auditable research report. The goal is not to chase the highest CAGR; it is to understand whether the data is reliable, the portfolio is investable, the risk is acceptable, and the rebalance decisions make sense.
        </p>
      </section>

      <section className="guide-section">
        <div>
          <span className="eyebrow">Ship-ready V3</span>
          <h2>What makes the live version feel real</h2>
        </div>
        <div className="guide-card-grid">
          {v3Items.map((item) => (
            <article className="guide-card" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="guide-section">
        <div>
          <span className="eyebrow">Factor Selection</span>
          <h2>How to choose the factor stack</h2>
        </div>
        <div className="factor-guide-grid">
          {factorGuides.map((factor) => (
            <article className="factor-guide" key={factor.title}>
              <h3>{factor.title}</h3>
              <p><strong>Use:</strong> {factor.use}</p>
              <p><strong>Watch:</strong> {factor.caution}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="guide-section split-guide">
        <div>
          <span className="eyebrow">Suggested Default</span>
          <h2>A balanced live factor recipe</h2>
          <p>
            For a first serious run, use momentum and relative momentum as the return engine, trend and drawdown as risk gates, quality as the business filter, valuation as the price discipline, and sector caps as portfolio hygiene.
          </p>
        </div>
        <div className="recipe-panel">
          <div><span>Momentum + relative momentum</span><strong>35-45%</strong></div>
          <div><span>Trend + drawdown + volatility</span><strong>20-30%</strong></div>
          <div><span>ROE, ROCE, earnings growth</span><strong>20-30%</strong></div>
          <div><span>Debt, P/E, P/B, liquidity</span><strong>10-20%</strong></div>
        </div>
      </section>

      <section className="guide-section">
        <div>
          <span className="eyebrow">Investment Workflow</span>
          <h2>How someone should use the tool before investing</h2>
        </div>
        <ol className="workflow-list">
          {workflow.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </section>

      <section className="guide-section split-guide">
        <div>
          <span className="eyebrow">Decision Rule</span>
          <h2>When a strategy is worth further research</h2>
          <p>
            A strategy deserves attention only if it beats the relevant benchmark or fund category on risk-adjusted return, survives walk-forward testing, avoids one-sector concentration, and remains investable after costs and taxes.
          </p>
        </div>
        <div className="decision-panel">
          <p>Do not invest from one metric.</p>
          <p>Do not chase the highest CAGR.</p>
          <p>Do not ignore drawdown, turnover, taxes, or liquidity.</p>
          <p>Use results to build a shortlist, then verify each company.</p>
        </div>
      </section>

      <section className="guide-section sources-panel">
        <div>
          <span className="eyebrow">Investor Safety</span>
          <h2>Important boundaries</h2>
          <p>
            SEBI investor education material advises investors to consult SEBI-registered investment advisers for investment needs, and to invest according to objective and risk appetite. AMFI notes that mutual fund investments involve risks including possible loss of principal. InvestPro should stay positioned as research software, not personalized advice.
          </p>
        </div>
        <div className="source-links">
          <a href="https://investor.sebi.gov.in/securities-dos_and_donts.html" target="_blank" rel="noreferrer">SEBI investor do&apos;s and don&apos;ts</a>
          <a href="https://investor.sebi.gov.in/cautiontoinvestor.html" target="_blank" rel="noreferrer">SEBI caution to investors</a>
          <a href="https://www.amfiindia.com/investor/knowledge-center-info?zoneName=riskInMutualFunds" target="_blank" rel="noreferrer">AMFI risk in mutual funds</a>
        </div>
      </section>
    </main>
  );
}

# Plan: From MarketMind to a Screenshot-to-Setup Trading Product

Status: draft v1. Replaces the "ticker in, BUY/HOLD/SELL out" scope described in the original README.

## 1. Product

**Input:** a chart screenshot (any timeframe, any platform), optionally a ticker hint.
**Output:** a *setup card*:

| Field | Meaning |
|---|---|
| Direction | LONG / SHORT / NO TRADE |
| Entry | price or zone |
| Stop-loss | invalidation level |
| Take-profits | TP1..TPn with R-multiples |
| Confidence | calibrated 0-1, backed by the backtest (see section 6) |
| Rationale | which agents agreed, which dissented |

The existing MarketMind graph (price, sentiment, on-chain, macro, risk, synthesis) is not thrown away. It becomes the **context layer** that confirms or vetoes what the chart reader sees.

## 2. Asset inventory

Everything below comes from github.com/dev4-gpt (own repos and stars). Roles marked (unverified) are taken from the owner's description and have not been re-read in this session.

| Asset | Role in the product | Status |
|---|---|---|
| `MultiAgent-stock-crypto-analyst` (this repo) | Core: LangGraph fan-out/fan-in, five context agents, Streamlit UI | Built |
| FinceptTerminal (starred) | Market-data and analytics reference; candidate data/UI source (unverified) | To evaluate |
| timesfm (starred) | Zero-shot time-series forecast as an extra agent signal and a baseline in the backtest (unverified) | To evaluate |
| MiroFish (starred) | Scenario / simulation layer; role to be confirmed before any integration | To evaluate |
| company-research agent (starred) | Fundamentals agent for stocks (filings, company profile) (unverified) | To evaluate |
| openreply (starred) | "Comment AI" to DM funnel for distribution (phase 6) (unverified) | To evaluate |

**Gaps that no existing repo fills, so we build them:**
1. Chart-image reader (screenshot to structured levels and trend).
2. Backtester plus public paper-trading log.

## 3. Architecture

```
screenshot --> [Chart Reader] --> ChartReading{asset?, timeframe, trend, S/R levels, patterns}
                   |                       |
                   |                       v
ticker (read or hinted) --> validate --> fan-out
                                          |-- price_agent      (existing)
                                          |-- sentiment_agent  (existing)
                                          |-- onchain_agent    (existing)
                                          |-- macro_agent      (existing)
                                          |-- risk_agent       (existing)
                                          |-- forecast_agent   (new, timesfm)
                                          |-- fundamentals_agent (new, stocks only)
                                          v
                                   setup_builder: entry/stop/TPs from levels + ATR + risk
                                          v
                                   confidence calibrator (from backtest stats)
                                          v
                                   SetupCard --> UI / API / paper log
```

Design rules:
- The chart reader extracts facts only. Trade levels come from deterministic code (`setup_builder`) using extracted levels plus ATR, so the LLM never invents prices.
- Every extracted level is cross-checked against real OHLCV once the ticker is known. Mismatch beyond tolerance means NO TRADE.
- Agents keep the `operator.add` reducer pattern. New agents emit the same `AgentSignal`.
- Confidence is a lookup into backtested hit rates for the setup type, not an LLM guess.

## 4. Phases

**Phase 1: Validation gate (go/no-go).**
Label 50 charts by hand (trend, key levels). Run a vision model. Gate: >= 80% trend accuracy and levels within tolerance. If it fails, stop and rethink; do not build on top.

**Phase 2: Chart reader + setup builder.**
`chart/reader.py`, `chart/levels.py`, `setup/builder.py`, `SetupCard` schema. Ticker detection from the screenshot with user confirmation. Unit tests on fixtures.

**Phase 3: Integrate MarketMind as the context layer.**
Feed `ChartReading` into state; add veto/boost logic in synthesis (for example, a risk veto when VIX is elevated, as today). Refactor `state.py` and `graph.py`; keep the old ticker-only path working.

**Phase 4: Backtester + public paper log.**
Rule-based replay of the setup logic on historical data; report win rate, expectancy, max drawdown by setup type. Publish a live, append-only paper-trade log. This is the trust strategy and the source of calibrated confidence.

**Phase 5: Extra signals (evaluate one at a time).**
timesfm forecast agent, company-research fundamentals agent, and anything worth taking from FinceptTerminal or MiroFish. Each one must beat the Phase 4 baseline in the backtest or it is dropped.

**Phase 6: Product surface and distribution.**
API + web UI (Streamlit first, then a proper frontend if the numbers justify it). Distribution funnel via openreply: "comment AI" under trading posts, offering a setup card, then DM to the product. Rate limits and platform ToS reviewed before any automation goes live.

## 5. Tech stack

Python 3.12, LangGraph/LangChain, Groq for text agents, a vision-capable model for the chart reader (chosen in Phase 1 by the eval), yfinance/CoinGecko/FRED/NewsAPI (existing), pandas/numpy, Streamlit, pytest. Backtest storage: SQLite or Parquet to start.

## 6. Trust strategy

1. Publish the backtest, including losing periods and fees/slippage assumptions.
2. Run a public paper-trading log, timestamped before the outcome is known.
3. Show calibration (stated confidence vs. realized hit rate).
4. Always show NO TRADE when the evidence is weak; a tool that always has a trade is not credible.

## 7. Risks

- **Vision may not be good enough.** Phase 1 exists to find out cheaply.
- **Backtests overfit.** Use walk-forward splits and a held-out period.
- **Regulatory:** trade levels can read as personalized advice. Needs disclaimers and a legal check before charging money or running the funnel.
- **Platform risk:** automated comment/DM flows can violate platform rules and get accounts banned.
- **Data cost/latency:** free tiers (NewsAPI, FRED, CoinGecko) will rate-limit under real traffic.
- **Unverified repos:** the roles of the starred repos above are assumptions until each is read; any could turn out to be a poor fit or have an incompatible license.

## 8. Open decisions for the owner

1. Which vision model(s) to test in Phase 1, and the per-image cost ceiling.
2. Stocks, crypto, or both for the first release.
3. Free product with public log, or paid from the start.
4. Which social platform(s) the funnel targets.
5. Whether the starred repos are integrated as code, as services, or only used as references.

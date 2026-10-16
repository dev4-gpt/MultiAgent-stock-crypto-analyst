# CLAUDE.md

Guidance for Claude Code in this repo. Product direction lives in [PLAN.md](PLAN.md).

## 1. What this is
MarketMind started as a ticker-in, BUY/HOLD/SELL-out multi-agent analyst. It is becoming a screenshot-to-setup-card product (direction, entry, stop-loss, take-profits, confidence). The existing graph stays as the context layer.

## 2. Layout
- `state.py`: `AgentSignal` and `TradeBuddyState` (the `agent_signals` list uses an `operator.add` reducer).
- `graph.py`: LangGraph fan-out from `validate` to five agents, fan-in to `synthesis_agent`.
- `agents/`: one module per agent; shared `llm` and `safe_parse_json` live in `agents/__init__.py`.
- `app.py`: Streamlit UI. `main.py` is a stub.
- `Multi_agent_stock_crypto_analyst.ipynb`: original notebook prototype.

## 3. Run
`uv sync` (or `pip install -r requirements.txt`), set `GROQ_API_KEY`, `NEWSAPI_KEY`, `FRED_API_KEY` in `.env`, then `streamlit run app.py`. Never commit `.env`.

## 4. Conventions
- New agents return `{"agent_signals": [AgentSignal(...)]}` and never raise; on failure return NEUTRAL with confidence 0.0.
- LLM output is parsed with `safe_parse_json`.
- Trade levels must come from deterministic code, not LLM text.
- Keep the ticker-only path working while the chart path is added.

## 5. Not financial advice
Outputs are educational. Do not remove the disclaimers.

## 6. Current phase
See PLAN.md section 4. Next step is the Phase 1 eval gate; do not build Phase 2+ before it passes.

## 7. Repo inventory (source: github.com/dev4-gpt; roles from the owner's description, not re-verified)
| Repo | Role |
|---|---|
| MultiAgent-stock-crypto-analyst | This repo; core graph and UI |
| FinceptTerminal (starred) | Data/analytics reference |
| openreply (starred) | Comment-AI to DM funnel (Phase 6) |
| timesfm (starred) | Forecast signal and backtest baseline |
| MiroFish (starred) | Scenario/simulation; role to be confirmed |
| company-research agent (starred) | Fundamentals agent for stocks |

Skills check: none of the above provides a chart-image reader or a backtester. Those two are built here (PLAN.md section 2).

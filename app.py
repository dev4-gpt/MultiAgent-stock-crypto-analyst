# Streamlit dashboard
# app.py
import time
import streamlit as st
from graph import tradebuddy_graph

st.set_page_config(page_title="MarketMind", page_icon="🧠", layout="wide")

st.title("🧠 MarketMind")
st.caption("Parallel Multi-Agent Stock & Crypto Analyst | LangGraph + Groq Llama-3.3-70B")
st.divider()

# Input
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input(
        "Enter ticker symbol",
        placeholder="e.g. AAPL BTC ETH TSLA NVDA",
        help="Stocks: AAPL, TSLA, NVDA | Crypto: BTC, ETH, SOL, DOGE, ADA",
    )
with col2:
    st.write(""); st.write("")
    run_btn = st.button("⚡ Analyze", type="primary", use_container_width=True)

SIGNAL_EMOJI = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "🟡"}
VERDICT_EMOJI = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
COLOR_MAP = {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "orange",
             "BUY": "green", "SELL": "red", "HOLD": "orange"}
AGENT_LABELS = {
    "price": "📈 Price & Technicals",
    "sentiment": "📰 News Sentiment",
    "onchain": "🔗 Market Structure",
    "macro": "🌍 Macro Context",
    "risk": "⚠️ Risk Analysis",
}
AGENT_ORDER = ["price", "sentiment", "onchain", "macro", "risk"]

def confidence_bar(c: float) -> str:
    return "█" * int(c * 10) + "░" * (10 - int(c * 10))

if run_btn and ticker.strip():
    status = st.empty()
    results = st.empty()

    with status.container():
        st.info(f"⚡ Launching 5 parallel agents for **{ticker.strip().upper()}**...")
        st.progress(0)

    start = time.time()
    try:
        # Execute the graph
        output = tradebuddy_graph.invoke({
            "ticker": ticker.strip(),
            "asset_type": "stock", # validate_input will auto-detect
            "agent_signals": [],
            "final_verdict": None,
            "final_confidence": None,
            "final_reasoning": None,
        })

        elapsed = round(time.time() - start, 1)
        status.empty()

        with results.container():
            raw_verdict = output.get("final_verdict", "HOLD")
            if not raw_verdict: raw_verdict = "HOLD"
            verdict = str(raw_verdict).strip().upper()
            color = COLOR_MAP.get(verdict, "orange")

            confidence = output.get("final_confidence", 0.5)
            reasoning = output.get("final_reasoning", "")
            asset_type = output.get("asset_type", "stock")

            v1, v2, v3 = st.columns([1, 1, 2])
            with v1:
                st.markdown("### Verdict")
                st.markdown(f"### :{color}[{VERDICT_EMOJI.get(verdict, '🟡')} {verdict}]")
            with v2:
                st.markdown("### Confidence")
                st.markdown(f"### {confidence:.0%}")
                st.progress(confidence)
            with v3:
                st.markdown("### Reasoning")
                st.markdown(f"*{reasoning}*")

            st.caption(
                f"⏱ {elapsed}s | Asset: {asset_type.upper()} | "
                "Model: llama-3.3-70b-versatile (Groq)"
            )
            st.divider()

            st.markdown("### 🤖 Agent Breakdown")
            signals_dict = {s["agent"]: s for s in output.get("agent_signals", [])}
            cols = st.columns(5)

            for i, key in enumerate(AGENT_ORDER):
                s = signals_dict.get(key)
                if not s:
                    continue
                with cols[i]:
                    raw_sig = s.get("signal", "NEUTRAL")
                    clean_sig = str(raw_sig).strip().upper()
                    sig_color = COLOR_MAP.get(clean_sig, "orange")
                    emoji = SIGNAL_EMOJI.get(clean_sig, "🟡")

                    st.markdown(f"**{AGENT_LABELS[key]}**")
                    st.markdown(f":{sig_color}[**{emoji} {clean_sig}**]")
                    conf = float(s.get('confidence', 0.0))
                    st.caption(f"Confidence: {conf:.0%}")
                    st.text(confidence_bar(conf))
                    st.caption(f"*{s.get('summary', '')}*")

            # Raw Data Inspector
            with st.expander("📊 View Raw Agent Data"):
                for key in AGENT_ORDER:
                    s = signals_dict.get(key)
                    if s and s.get("raw_data"):
                        st.markdown(f"**{AGENT_LABELS[key]}**")
                        st.json(s["raw_data"])

    except Exception as e:
        status.empty()
        st.error(f"Analysis failed: {str(e)}")
        st.exception(e)

elif run_btn:
    st.warning("Please enter a ticker symbol.")

st.divider()
st.caption("⚠️ For educational purposes only. Not financial advice. Always DYOR.")

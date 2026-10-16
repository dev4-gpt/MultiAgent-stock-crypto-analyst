"""Build the Phase 1 dataset automatically: fetch OHLCV, render candlestick charts, label by rule.

    python -m eval.make_dataset --n 60            # needs internet (yfinance)
    python -m eval.make_dataset --synthetic --n 60  # offline wiring check only

Labels come from objective rules (below), not human judgment. Ambiguous windows are skipped
rather than guessed, so label noise stays low. Charts are clean matplotlib renders, so a pass
here is optimistic vs. real TradingView screenshots with indicators; add some hand-labeled
real screenshots to eval/data/images before trusting the gate.
"""
import argparse
import json
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import mplfinance as mpf
import numpy as np
import pandas as pd

DATA = Path(__file__).parent / "data"
UNIVERSE = [("BTC-USD", "1h"), ("ETH-USD", "1h"), ("SOL-USD", "1h"), ("AAPL", "1d"), ("MSFT", "1d"),
            ("NVDA", "1d"), ("TSLA", "1d"), ("SPY", "1d"), ("QQQ", "1d"), ("GLD", "1d"), ("AMZN", "1h")]
WINDOW = 90  # candles per chart


def label_trend(close: np.ndarray) -> str | None:
    """UP/DOWN: >=4% net move with a clean linear fit (R^2>=0.6). SIDEWAYS: <=1.5% move. Else skip."""
    x = np.arange(len(close))
    slope, icpt = np.polyfit(x, close, 1)
    fit = slope * x + icpt
    r2 = 1 - ((close - fit) ** 2).sum() / ((close - close.mean()) ** 2).sum()
    move = slope * (len(close) - 1) / close.mean()
    if move >= 0.04 and r2 >= 0.6:
        return "UP"
    if move <= -0.04 and r2 >= 0.6:
        return "DOWN"
    if abs(move) <= 0.015:
        return "SIDEWAYS"
    return None


def label_levels(high: np.ndarray, low: np.ndarray, k: int = 3, tol: float = 0.01) -> list[float]:
    """Pivot highs/lows (local extrema over +-5 candles), clustered within tol; keep the k most-touched."""
    piv = [high[i] for i in range(5, len(high) - 5) if high[i] == high[i - 5:i + 6].max()]
    piv += [low[i] for i in range(5, len(low) - 5) if low[i] == low[i - 5:i + 6].min()]
    clusters: list[list[float]] = []
    for p in sorted(piv):
        if clusters and p <= clusters[-1][0] * (1 + tol):
            clusters[-1].append(p)
        else:
            clusters.append([p])
    best = sorted(clusters, key=len, reverse=True)[:k]
    return sorted(round(float(np.mean(c)), 2) for c in best if len(c) >= 2)


def synthetic(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    drift = rng.choice([-0.0015, 0, 0.0015])
    close = 100 * np.exp(np.cumsum(rng.normal(drift, 0.006, 400)))
    open_ = np.r_[close[0], close[:-1]]
    hi = np.maximum(open_, close) * (1 + rng.uniform(0, 0.004, 400))
    lo = np.minimum(open_, close) * (1 - rng.uniform(0, 0.004, 400))
    idx = pd.date_range("2024-01-01", periods=400, freq="h")
    return pd.DataFrame({"Open": open_, "High": hi, "Low": lo, "Close": close, "Volume": 1.0}, index=idx)


def fetch(symbol: str, interval: str) -> pd.DataFrame:
    import yfinance as yf
    period = "700d" if interval == "1h" else "5y"
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    rnd = random.Random(a.seed)
    (DATA / "images").mkdir(parents=True, exist_ok=True)

    frames = {}
    if a.synthetic:
        frames = {(f"SYN{i}", "1h"): synthetic(i) for i in range(12)}
    else:
        for sym, itv in UNIVERSE:
            try:
                frames[(sym, itv)] = fetch(sym, itv)
            except Exception as e:
                print(f"skip {sym}: {e}")
    if not frames:
        raise SystemExit("no data fetched (no internet?)")

    rows, per_class, attempts = [], {"UP": 0, "DOWN": 0, "SIDEWAYS": 0}, 0
    cap = -(-a.n // 3)  # balance classes so accuracy can't be gamed by always answering one trend
    while len(rows) < a.n and attempts < a.n * 200:
        attempts += 1
        (sym, itv), df = rnd.choice(list(frames.items()))
        if len(df) < WINDOW + 1:
            continue
        s = rnd.randrange(0, len(df) - WINDOW)
        w = df.iloc[s:s + WINDOW]
        trend = label_trend(w["Close"].to_numpy())
        if trend is None or per_class[trend] >= cap:
            continue
        name = f"{sym.replace('-', '')}_{itv}_{len(rows):03d}.png"
        mpf.plot(w, type="candle", style="charles", axisoff=False, ylabel="Price", figratio=(12, 7),
                 title=f"{sym} {itv}", savefig=dict(fname=DATA / "images" / name, dpi=100))
        rows.append({"image": name, "trend": trend,
                     "levels": label_levels(w["High"].to_numpy(), w["Low"].to_numpy())})
        per_class[trend] += 1
    with open(DATA / "labels.jsonl", "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"wrote {len(rows)} charts; class counts {per_class}")


if __name__ == "__main__":
    main()

# Phase 1 eval: can a vision model read charts?

Gate (PLAN.md): >= 50 hand-labeled charts and >= 80% trend accuracy. Fail = stop and rethink.

## Fastest path: auto-build the dataset (needs internet)
```
pip install -e '.[eval]'
python -m eval.make_dataset --n 60     # downloads prices, draws charts, labels by rule, class-balanced
```
Labels come from fixed rules (net move + linear-fit R^2 for trend; clustered pivots for levels); ambiguous windows are skipped. Caveat: these are clean renders, so a pass is optimistic versus real TradingView screenshots. Add ~15 real hand-labeled screenshots too (below) before trusting the gate.

## Or label charts by hand
1. Put screenshots in `eval/data/images/`. Mix timeframes, platforms, assets, and trends; include sideways and messy charts, not just clean ones.
2. One JSON object per line in `eval/data/labels.jsonl`:
   `{"image": "btc_4h_01.png", "trend": "UP", "levels": [61200, 64800]}`
   - `trend`: UP / DOWN / SIDEWAYS over the visible window. Label before looking at any model output.
   - `levels` (optional): key support/resistance prices read off the axis. A prediction matches within 1%.

## Run
```
python -m eval.run --provider mock                       # wiring check, no cost
ANTHROPIC_API_KEY=... python -m eval.run --provider anthropic --model claude-sonnet-5-5 --out eval/results.json
```
Exit code 0 only if the gate passes. Failed API calls count as wrong. Add providers in `eval/providers.py` to compare models.

"""Run the Phase 1 eval:  python -m eval.run --provider anthropic --model <id>"""
import argparse
import json
import mimetypes
import sys
from pathlib import Path

from eval.providers import make_provider
from eval.schema import load_labels
from eval.score import score

DATA = Path(__file__).parent / "data"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=DATA / "labels.jsonl")
    ap.add_argument("--images", default=DATA / "images")
    ap.add_argument("--provider", default="mock", choices=["anthropic", "mock"])
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--out", default=None, help="write full results JSON here")
    a = ap.parse_args(argv)

    labels = load_labels(a.labels)
    provider = make_provider(a.provider, a.model)
    readings = []
    for l in labels:
        path = Path(a.images) / l.image
        media = mimetypes.guess_type(path.name)[0] or "image/png"
        readings.append(provider.read(path.read_bytes(), media))

    result = score(labels, readings)
    result["provider"], result["model"] = a.provider, a.model
    print(json.dumps(result, indent=2))
    if a.out:
        result["items"] = [{"image": l.image, "label": l.trend, "pred": r.trend,
                            "levels_true": l.levels, "levels_pred": r.levels, "error": r.error}
                           for l, r in zip(labels, readings)]
        Path(a.out).write_text(json.dumps(result, indent=2))
    return 0 if result["gate"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

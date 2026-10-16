"""Label and reading schemas for the Phase 1 chart-reading eval."""
import json
from dataclasses import dataclass, field
from pathlib import Path

TRENDS = ("UP", "DOWN", "SIDEWAYS")


@dataclass
class Label:
    image: str                      # filename inside the images dir
    trend: str                      # one of TRENDS, judged over the visible window
    levels: list[float] = field(default_factory=list)  # key support/resistance prices read off the axis

    def __post_init__(self):
        self.trend = self.trend.strip().upper()
        if self.trend not in TRENDS:
            raise ValueError(f"{self.image}: trend must be one of {TRENDS}, got {self.trend!r}")


@dataclass
class Reading:
    trend: str | None
    levels: list[float] = field(default_factory=list)
    error: str | None = None


def load_labels(path: str | Path) -> list[Label]:
    labels = []
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            labels.append(Label(**json.loads(line)))
        except (TypeError, ValueError) as e:
            raise ValueError(f"{path}:{n}: {e}") from e
    return labels

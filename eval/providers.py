"""Vision providers. Add a class with read(image_bytes, media_type) -> Reading to test another model."""
import base64
import json
import os
import re

from eval.schema import Reading, TRENDS

PROMPT = """You are reading a trading chart screenshot. Report only what is visible.
Return ONLY JSON: {"trend": "UP" | "DOWN" | "SIDEWAYS", "levels": [prices]}
- trend: the dominant direction across the whole visible window.
- levels: up to 4 key horizontal support/resistance prices, read from the price axis.
No other text."""


def parse_reading(text: str) -> Reading:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return Reading(None, error=f"no JSON in response: {text[:80]!r}")
    try:
        d = json.loads(m.group(0))
        trend = str(d["trend"]).strip().upper()
        if trend not in TRENDS:
            return Reading(None, error=f"bad trend {trend!r}")
        return Reading(trend, [float(x) for x in d.get("levels", [])])
    except (ValueError, KeyError, TypeError) as e:
        return Reading(None, error=str(e)[:80])


class AnthropicProvider:
    def __init__(self, model: str):
        import anthropic  # lazy: only needed for real runs
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    def read(self, image: bytes, media_type: str) -> Reading:
        try:
            resp = self.client.messages.create(
                model=self.model, max_tokens=300, temperature=0,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                                 "data": base64.b64encode(image).decode()}},
                    {"type": "text", "text": PROMPT}]}])
            return parse_reading(resp.content[0].text)
        except Exception as e:  # a failed call counts against accuracy, never aborts the run
            return Reading(None, error=str(e)[:80])


class MockProvider:
    """Always answers SIDEWAYS; for wiring checks without spending money."""
    def read(self, image: bytes, media_type: str) -> Reading:
        return Reading("SIDEWAYS", [])


def make_provider(name: str, model: str):
    if name == "anthropic":
        return AnthropicProvider(model)
    if name == "mock":
        return MockProvider()
    raise ValueError(f"unknown provider {name!r}")

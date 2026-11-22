"""Price table per (provider, model) in MYR per 1M tokens (SPEC-06 §1, §6).

Models missing from the table are plan-quota models: their cost is null.
"""

from decimal import Decimal

PRICES: dict[tuple[str, str], tuple[Decimal, Decimal]] = {
    ("ilmu", "ilmu-glm-5.3-flash"): (Decimal("0.55"), Decimal("1.85")),
    ("ilmu", "bge-m3"): (Decimal("0.04"), Decimal("0")),
    ("ilmu", "bge-reranker"): (Decimal("0.04"), Decimal("0")),
}

PLAN_MODELS: set[tuple[str, str]] = {("ilmu", "nemo-super"), ("ilmu", "ilmu-nemo-nano")}

MILLION = Decimal(1_000_000)
QUANTUM = Decimal("0.000001")


def cost_myr(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> Decimal | None:
    price = PRICES.get((provider, model))
    if price is None:
        return None
    input_price, output_price = price
    total = (input_price * prompt_tokens + output_price * completion_tokens) / MILLION
    return total.quantize(QUANTUM)

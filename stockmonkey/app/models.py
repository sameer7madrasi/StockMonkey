from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json


@dataclass
class TickerSnapshot:
    ticker: str
    price: float | None = None
    change: float | None = None
    percent_change: float | None = None
    market_status: str | None = None
    headlines: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

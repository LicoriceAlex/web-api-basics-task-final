from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    nats_url: str = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
    nats_subject: str = os.getenv("NATS_SUBJECT", "items.updates")

    rates_interval_seconds: int = int(os.getenv("RATES_INTERVAL_SECONDS", "60"))
    rates_source_url: str = os.getenv(
        "RATES_SOURCE_URL", "https://api.binance.com/api/v3/ticker/price"
    )

    @property
    def default_db_path(self) -> str:
        return (Path(__file__).resolve().parent.parent / "currency.db").as_posix()

    @property
    def database_url(self) -> str:
        return os.getenv(
            "DATABASE_URL", f"sqlite+aiosqlite:///{self.default_db_path}"
        )


settings = Settings()


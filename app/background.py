import asyncio
import contextlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Optional

import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker

from . import crud, schemas

NotifyFn = Callable[[dict], Awaitable[None]]

logger = logging.getLogger("currency_tracker.rates")


# Популярные пары по умолчанию
DEFAULT_COINS: dict[str, str] = {
    "BTCUSDT": "Bitcoin",
    "ETHUSDT": "Ethereum",
    "BNBUSDT": "BNB",
    "SOLUSDT": "Solana",
    "XRPUSDT": "XRP",
    "DOGEUSDT": "Dogecoin",
    "ADAUSDT": "Cardano",
    "TONUSDT": "Toncoin",
}


class RatesUpdater:
    """Обновляет цены и сохраняет их в базу"""

    def __init__(
        self,
        session_factory: async_sessionmaker,
        notifier: Optional[NotifyFn] = None,
        *,
        interval_seconds: int = 60,
        source_url: str = "https://api.binance.com/api/v3/ticker/price",
        source_name: str = "binance",
    ) -> None:
        self._session_factory = session_factory
        self._notifier = notifier
        self._interval = interval_seconds
        self._source_url = source_url
        self._source_name = source_name

        self._task: Optional[asyncio.Task] = None
        self._running = False

        self.last_run_at: Optional[datetime] = None
        self.last_inserted: int = 0
        self.last_error: Optional[str] = None
        self.last_note: Optional[str] = None

    async def start(self) -> None:
        """Запуск фоновой задачи"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        """Остановка фоновой задачи"""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def run_once(self) -> int:
        """Ручной запуск одного обновления"""
        return await self._fetch_and_store()

    async def _worker(self) -> None:
        """Цикл фоновой задачи"""
        while self._running:
            try:
                await self._fetch_and_store()
            except Exception as err:
                self.last_error = f"{type(err).__name__}: {err}"
                logger.warning("rates updater failed: %s", self.last_error)
            await asyncio.sleep(self._interval)

    async def _fetch_and_store(self) -> int:
        """Загрузка цен и сохранение в базу"""
        fetched_at = datetime.now(timezone.utc)
        if self.last_run_at and fetched_at <= self.last_run_at:
            fetched_at = self.last_run_at + timedelta(microseconds=1)

        self.last_run_at = fetched_at
        self.last_error = None
        self.last_note = None
        inserted: list[dict] = []

        async with self._session_factory() as session:
            currencies = await crud.list_currencies(session)

            # На первом запуске добавляем популярные пары
            existing_codes = {c.code.upper() for c in currencies}
            for code, name in DEFAULT_COINS.items():
                if code not in existing_codes:
                    await crud.create_currency(
                        session,
                        schemas.CurrencyCreate(code=code, name=name, enabled=True),
                    )
            currencies = await crud.list_currencies(session)

            symbols = [c.code.upper() for c in currencies if c.enabled]
            if not symbols:
                self.last_inserted = 0
                self.last_note = "нет включенных пар"
                return 0

            prices = await self._fetch_remote_prices(symbols)
            if not prices:
                self.last_inserted = 0
                if not self.last_error:
                    self.last_error = "не удалось получить цены проверь сеть и символы"
                return 0

            for currency in currencies:
                if not currency.enabled:
                    continue

                code = currency.code.upper()
                price_raw = prices.get(code)
                if not price_raw:
                    continue

                nominal = 1
                value = float(price_raw)

                rate = await crud.create_rate(
                    session,
                    currency_code=code,
                    nominal=nominal,
                    value=value,
                    fetched_at=fetched_at,
                    source=self._source_name,
                )
                inserted.append(
                    {
                        "id": rate.id,
                        "currency_code": rate.currency_code,
                        "nominal": rate.nominal,
                        "value": rate.value,
                        "fetched_at": rate.fetched_at,
                        "source": rate.source,
                    }
                )

        if inserted and self._notifier:
            await self._notifier({"type": "rates_updated", "payload": inserted})

        self.last_inserted = len(inserted)
        if self.last_inserted == 0:
            self.last_note = "цены не сохранены возможно пары отключены или не найдены"

        return len(inserted)

    async def _fetch_remote_prices(self, symbols: list[str]) -> dict[str, str]:
        """Загрузка цен с Binance"""
        symbols_norm = [s.strip().upper() for s in symbols if s and s.strip()]
        if not symbols_norm:
            symbols_norm = list(DEFAULT_COINS.keys())

        prices: dict[str, str] = {}

        async def fetch_one(client: httpx.AsyncClient, symbol: str) -> None:
            """Получить цену одной пары"""
            try:
                response = await client.get(self._source_url, params={"symbol": symbol})
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict) and isinstance(data.get("price"), str):
                    prices[symbol] = data["price"]
            except Exception:
                # Если символ не существует или есть ошибка просто пропускаем
                return

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await asyncio.gather(*(fetch_one(client, s) for s in symbols_norm))
        except Exception as err:
            self.last_error = f"{type(err).__name__}: {err}"
            return {}

        if not prices:
            self.last_error = "цены не получены проверь сеть и символы"
            return {}

        return prices

    def status(self) -> dict:
        """Статус фоновой задачи для отладки"""
        return {
            "running": self._running,
            "interval_seconds": self._interval,
            "source_url": self._source_url,
            "source_name": self._source_name,
            "last_run_at": self.last_run_at,
            "last_inserted": self.last_inserted,
            "last_error": self.last_error,
            "last_note": self.last_note,
        }

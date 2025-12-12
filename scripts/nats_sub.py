import asyncio
import os

from nats.aio.client import Client as NATS


async def main() -> None:
    """Точка входа"""
    url = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
    subject = os.getenv("NATS_SUBJECT", "items.updates")

    nc = NATS()
    await nc.connect(servers=[url])

    async def handler(msg) -> None:
        """Печать входящего сообщения"""
        print(f"{msg.subject}: {msg.data.decode('utf-8')}")

    await nc.subscribe(subject, cb=handler)
    print(f"listening {subject} at {url}")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import json
import os

from nats.aio.client import Client as NATS


async def main() -> None:
    """Точка входа"""
    url = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
    subject = os.getenv("NATS_SUBJECT", "items.updates")

    event = {
        "type": "external_message",
        "payload": {"text": "hello from publisher"},
    }

    nc = NATS()
    await nc.connect(servers=[url])
    await nc.publish(subject, json.dumps(event).encode("utf-8"))
    await nc.flush(timeout=1)
    await nc.close()

    print("published")


if __name__ == "__main__":
    asyncio.run(main())
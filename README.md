# Трекер цен криптовалют WebApi

Backend:
- REST API (`/items`, `/tasks/run`, `/tasks/status`, `/rates`)
- WebSocket (`/ws/items`) для real-time событий
- фоновая задача раз в минуту тянет цены с Binance и сохраняет в SQLite
- NATS обязателен все события идут через очередь

## Запуск одной командой

```bash
cd web-api-basics-task-final
docker compose up --build
```

База сохраняется в `web-api-basics-task-final/data/currency.db`

## Документация API Swagger

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## WebSocket

WebSocket URL:
- `ws://127.0.0.1:8000/ws/items`

События:
- `item_created`, `item_updated`, `item_deleted`
- `rates_updated`

### Визуальный WebSocket клиент

Открой в браузере:
- `http://127.0.0.1:8000/ws-ui`

Сделай `POST /tasks/run` и посмотри входящие сообщения

## REST API

`/items` это список пар для отслеживания например `BTCUSDT`, `ETHUSDT`:
- `GET /items`
- `GET /items/{id}`
- `POST /items`
- `PATCH /items/{id}`
- `DELETE /items/{id}`

Фоновая задача:
- `POST /tasks/run` ручной запуск обновления
- `GET /tasks/status` статус и ошибки

Цены:
- `GET /rates?code=BTCUSDT&limit=50`
- `GET /rates/latest?code=BTCUSDT`

## NATS пример

Мониторинг NATS:
- `http://127.0.0.1:8222`

Subscriber:
```bash
python scripts/nats_sub.py
```

Publisher:
```bash
python scripts/nats_pub.py
```

## Что приложить в отчёт

4. Документацию по API (Swagger) `http://127.0.0.1:8000/docs`
5. Скрин с WebSocket-клиента `http://127.0.0.1:8000/ws-ui`
6. Пример работы NATS (subscriber + publisher) запусти `python scripts/nats_sub.py` и `python scripts/nats_pub.py` и сделай скрин консоли

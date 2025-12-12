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
Документацию по API (Swagger) `http://127.0.0.1:8000/docs`
<img width="1730" height="819" alt="image" src="https://github.com/user-attachments/assets/4e903afa-37c8-4b11-a793-3f659315af6c" />

Скрин с WebSocket-клиента
<img width="1910" height="391" alt="image" src="https://github.com/user-attachments/assets/105bb649-282e-4272-a8cf-cbfd3dc918e9" />

Пример работы NATS (subscriber + publisher) запусти `python scripts/nats_sub.py` и `python scripts/nats_pub.py` и сделай скрин консоли
<img width="1761" height="482" alt="image" src="https://github.com/user-attachments/assets/e575e4aa-952f-4089-91ec-f04bc8ce8420" />

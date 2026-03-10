# Axiom WDK Service

This service bridges Python agent logic to real WDK Node modules.

## Setup

1. Copy `.env.example` to `.env` and set `WDK_SEED_PHRASE`.
2. Optionally set `WDK_SERVICE_API_KEY` and the same key in Python `.env` as `WDK_SERVICE_API_KEY`.
3. Install dependencies:

```bash
npm install
```

4. Start service:

```bash
npm start
```

Service listens on `http://127.0.0.1:8787` by default.

## Endpoints

- `POST /balance`
- `POST /transfer`
- `POST /deposit`
- `POST /swap`

All responses return:

```json
{
  "ok": true
}
```

or

```json
{
  "ok": false,
  "error": "message"
}
```

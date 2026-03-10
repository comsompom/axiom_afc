# Axiom AFC (Autonomous Financial Controller)

<p align="center">
  <img src="axiom_logo.jpg" alt="Axiom Logo" width="320" />
</p>

Axiom is an autonomous treasury and payout agent for the Tether WDK hackathon.

It follows the required flow:
- Rule: keep a liquid reserve, reward contributors, deploy excess only when profitable.
- Work: evaluate GitHub merges, balances, APY, gas, and constraints.
- Settle: execute transactions through wallet tools.

## Architecture

- Python agent runtime: `src/axiom/*`
- Wallet abstraction: `src/axiom/wallet/wallet_client.py`
- WDK bridge client (Python -> Node): `src/axiom/wallet/wdk_wallet_client.py`
- WDK Node service (real WDK packages): `wdk_service/server.js`

## Real WDK integration model

WDK official quickstarts are Node-first (`@tetherto/*` npm packages), so this repo runs:
- Python for autonomous decision logic
- Node service for real WDK wallet execution

References:
- [Node.js & Bare Quickstart](https://docs.wdk.tether.io/start-building/nodejs-bare-quickstart)
- [Build with AI](https://docs.wdk.tether.io/start-building/build-with-ai)

## Project files you must configure

- `config/token_map.json` token addresses and decimals per chain
- `config/protocol_map.json` protocol route metadata
- `data/contributor_wallets.json` GitHub username -> payout wallet
- `.env` runtime configuration
- `wdk_service/.env` WDK seed phrase + RPC URLs

## Run locally (real WDK path)

1) Python setup:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2) Create Python env:

```bash
copy .env.example .env
```

3) Node WDK service setup:

```bash
cd wdk_service
copy .env.example .env
npm install
npm start
```

4) In another terminal, run the agent:

```bash
cd ..
python run.py --rules rules/mandate.example.json --once
```

## Important env switches

- `WALLET_MODE=wdk`
- `WDK_SERVICE_URL=http://127.0.0.1:8787`
- `ENABLE_HEDGE=false` (currently requested)
- `ENABLE_YIELD_MOVES=false` (safe default until live deposit route is configured)

## Notes on current production readiness

- Payout transfer path is wired for real onchain execution through WDK service.
- Balance checks support native and ERC20 balances.
- Deposit endpoint is scaffolded and requires real `pool_address` route values.
- Swap endpoint is scaffolded and intentionally disabled until a live WDK protocol module route is added.

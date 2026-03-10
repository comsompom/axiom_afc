# Axiom AFC (Autonomous Financial Controller)

![Axiom Logo](axiom_logo.jpg)

Axiom is an autonomous treasury and payout agent designed for the Tether Hackathon Galáctica: WDK Edition 1.

It implements the required **Rule -> Work -> Settle** flow:
- Rule: keep a minimum liquid USDt reserve, lend excess funds where profitable, and pay contributors when PRs are merged.
- Work: continuously evaluate GitHub events, wallet balances, APY, gas, and bridge costs.
- Settle: execute wallet transfers and treasury allocation actions.

## Why this repo matches the hackathon requirements

- Uses a dedicated **WDK wallet adapter** interface (`src/axiom/wallet/wdk_wallet_client.py`) for real self-custodial wallet execution.
- Includes an autonomous execution loop (`src/axiom/agent/engine.py`) with no manual transaction trigger.
- Includes an explicit profitability checker (`src/axiom/economics/profitability.py`) before moving funds.
- Includes clear local run instructions and mock mode for judge-friendly evaluation.
- Includes Apache 2.0 license as required.

## Current implementation modes

- `mock` mode (default): fully runnable out of the box with simulated balances/transactions.
- `wdk` mode: production adapter stub wired for WDK SDK integration through environment-driven import.

This keeps the project testable now while preserving a clean path to full WDK execution.

## Project structure

- `src/axiom/main.py`: CLI entrypoint
- `src/axiom/agent/engine.py`: autonomous decision loop
- `src/axiom/economics/profitability.py`: economic soundness checks
- `src/axiom/github/github_client.py`: merged PR trigger source
- `src/axiom/market/market_client.py`: APY + gas + volatility source
- `src/axiom/wallet/*.py`: wallet interfaces, mock wallet, WDK wallet adapter
- `rules/mandate.example.json`: example natural-language mandate encoded as config

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy env template:

```bash
copy .env.example .env
```

4. Run once in mock mode:

```bash
python run.py --rules rules/mandate.example.json --once
```

5. Run continuously:

```bash
python run.py --rules rules/mandate.example.json
```

## Environment variables

See `.env.example`.

Key controls:
- `WALLET_MODE=mock|wdk`
- `EVALUATION_INTERVAL_SECONDS=600` (10 minutes default)
- `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GITHUB_TOKEN`
- `MIN_LIQUID_USDT`, `PR_PAYOUT_USDT`, `VOLATILITY_HEDGE_PERCENT`

## WDK integration notes

The class `WdkWalletClient` is intentionally isolated behind `WalletClient` protocol.  
To activate real WDK execution:

1. Install and configure the official WDK SDK per docs.
2. Set:
   - `WALLET_MODE=wdk`
   - `WDK_MODULE` to your installed module path
3. Implement/wire SDK-specific method calls in `WdkWalletClient`.

## Third-party services disclosure

This project can use:
- GitHub API (merged PR events)
- DeFiLlama API (APY source, optional)
- Public gas oracle endpoint (optional, configured via env)

In mock mode, no external APIs are required.

## Demo expectations

For hackathon video, show terminal output proving:
- merged PR detection
- profitability decision (including break-even estimate)
- autonomous payout action
- autonomous treasury allocation action
# Axiom (Autonomous Financial Controller)

Axiom is a hackathon-ready autonomous treasury agent scaffold inspired by the solution strategy in `solution.md`.

It demonstrates:

- rule-based autonomous execution loop
- GitHub merged PR payout triggers
- treasury liquidity + excess capital deployment decisions
- economic soundness checks before yield deployment
- adapter boundaries for WDK/Openclaw/MCP integrations

## Current Scope

This repository ships a working local MVP with mock providers so you can:

- run the agent loop today
- validate autonomy and decision logs
- prove profitability constraints are enforced

WDK/Openclaw/real MCP clients are intentionally isolated behind interfaces in `axiom_afc/providers.py` and can be swapped in later without changing core logic.

## Quick Start

Requirements: Python 3.11+

```bash
python -m venv .venv
.venv\Scripts\activate
python -m axiom_afc.main --iterations 3 --interval-seconds 1
```

Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Agent Behavior

Default mandate:

- keep `500 USDT` liquid
- if merged PR event exists, pay contributor `50 USDT`
- deploy excess USDT only if expected return beats move costs and break-even window

Every cycle:

1. pull treasury state
2. process merged PR payouts
3. evaluate deployable excess
4. fetch APY + fees + gas
5. run profitability checker
6. execute or skip and log reason

## How to Integrate Real Services

- Replace `MockTreasuryProvider` with WDK-backed wallet and transfer calls.
- Replace `MockMarketDataProvider` with DeFiLlama/CoinGecko and live gas feeds.
- Replace `MockGithubEventProvider` with MCP GitHub integration.
- Replace `MockYieldProvider` with Openclaw strategy execution over Aave/bridges.

## Demo-Friendly Output

`ConsoleReporter` prints cycle-level decisions, calculations, and tx ids (mocked) so you can record a clear autonomy/economic soundness demo for hackathon judging.

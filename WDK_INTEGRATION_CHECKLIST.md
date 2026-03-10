# WDK Integration and .env Configuration Checklist

## 1) Wire real WDK methods in `WdkWalletClient`

Your current `WdkWalletClient` is already the right abstraction; now replace the placeholder calls with your actual WDK SDK calls.

### Step A — Install WDK and confirm import path
1. Install the official WDK package (exact command from WDK docs).
2. Verify the module import path:
   - `python -c "import <your_wdk_module>; print(<your_wdk_module>.__name__)"`
3. Put that module path in `.env` as `WDK_MODULE=...`.

### Step B — Initialize a real WDK client in `__init__`
In `WdkWalletClient.__init__`, after `self.sdk = self._load_sdk(module_name)`, create/attach:
- RPC/provider client(s)
- wallet/key manager (self-custodial signer)
- token config (USDt, XAUt contract addresses by chain)

You want one ready-to-use object, e.g. `self.client`, reused by all methods.

### Step C — Implement each method with exact SDK calls
You need 4 real methods:

- `get_balance(address, token)`
  - Resolve token contract for chain/network.
  - Call WDK balance function.
  - Normalize units (raw integer -> decimal float).
  - Return `float`.

- `transfer(token, from_address, to_address, amount, chain)`
  - Build transfer tx with token, chain, amount.
  - Sign/send with wallet signer.
  - Wait for receipt (or at least submission result).
  - Return tx hash string.

- `move_to_yield(token, from_address, amount, chain, protocol)`
  - This usually means:
    1. Optional bridge to target chain
    2. Approve spender
    3. Deposit into protocol (Aave/Openclaw route)
  - Return final tx hash (or a composed ID if multi-step, but better: last onchain hash + log intermediate hashes).

- `hedge_to_xaut(from_address, amount_usdt, chain)`
  - Execute swap USDt -> XAUt via your chosen route.
  - Return tx hash.

### Step D — Add strict error handling/logging
For each method:
- Catch SDK/network exceptions.
- Raise a clear `RuntimeError` with chain/token/action context.
- Never silently fallback to mock tx IDs in `wdk` mode.

### Step E — Handle token decimals correctly
Do not pass float directly to SDK tx methods.
- Convert to base units (`Decimal`, token decimals map).
- Convert base units back to human-readable only for logs.

### Step F — Validate WDK mode end-to-end
Run:
- `python run.py --rules rules/mandate.example.json --once`

Expected:
- No placeholder tx IDs like `wdk-tx-...`
- Real tx hashes from chain
- Balance and transfer results consistent with explorer

## 2) Configure real `.env` values

Create `.env` from `.env.example`, then set real values.

Use this as a concrete template:

```env
# Runtime
WALLET_MODE=wdk
WDK_MODULE=<exact_python_module_path>

# Wallets
TREASURY_WALLET_ADDRESS=0xYourTreasuryAddress
CHECKING_WALLET_ADDRESS=0xYourCheckingAddress
DEFAULT_USDT_TOKEN=USDt

# Agent policy
MIN_LIQUID_USDT=500
PR_PAYOUT_USDT=50
VOLATILITY_HEDGE_PERCENT=0.1
EVALUATION_INTERVAL_SECONDS=600
ENABLE_HEDGE=true

# Chains / fees
ALLOWED_CHAINS=arbitrum,base
BRIDGE_FEE_USDT=2.5

# GitHub
GITHUB_REPO_OWNER=your-org-or-username
GITHUB_REPO_NAME=your-repo
GITHUB_TOKEN=ghp_xxx_or_fine_grained_token

# Market APIs
APY_API_URL=https://yields.llama.fi/pools
GAS_API_URL=<your_gas_api_endpoint_or_blank>
```

## Critical real-world notes

- GitHub payout mapping is currently mock in `github_client.py` (`payout_address` is fabricated from username).
  You must replace this with a real mapping source:
  - JSON registry
  - DB
  - ENS/profile lookup
  - signed contributor wallet registration

- Token/chain config should be explicit:
  - USDt contract per chain
  - XAUt contract per chain
  - protocol addresses

- Secrets hygiene:
  - Never commit `.env`
  - Use read-only API scopes where possible
  - For GitHub token, minimum needed scopes (repo read / PR read)

## Quick implementation order

1. Fill `.env` real values (`WALLET_MODE=wdk`, repo/token, addresses).
2. Wire `get_balance` and `transfer` first; test single payout flow.
3. Wire `move_to_yield`; test profitability-approved deployment.
4. Wire `hedge_to_xaut`; keep `ENABLE_HEDGE=false` until validated.
5. Replace GitHub username->wallet mock mapping.

## 3) Hands-on runbook (exact order)

Use this section as a literal execution checklist.

### Phase 0 - Open these URLs first

1. WDK docs home  
   `https://docs.wdk.tether.io/`
2. WDK "Build with AI" page  
   `https://docs.wdk.tether.io/start-building/build-with-ai`
3. Node/Bare quickstart (for package names and bootstrap pattern)  
   `https://docs.wdk.tether.io/start-building/nodejs-bare-quickstart`
4. MCP Toolkit docs (for agent wallet tools and protocol actions)  
   `https://docs.wdk.tether.io/ai/mcp-toolkit`
5. WDK docs MCP endpoint (optional, for AI-assisted coding lookup)  
   `https://docs.wallet.tether.io/~gitbook/mcp`

### Phase 1 - Create local integration artifacts

Create these files in this repo:

1. `.env` (copy from `.env.example`)
2. `config/token_map.json` (token contracts and decimals by chain)
3. `config/protocol_map.json` (protocol addresses/routes for lending and swap)
4. `data/contributor_wallets.json` (GitHub username -> payout address mapping)
5. `docs/wdk_setup_notes.md` (record exact SDK/package versions used)

Suggested minimal `token_map.json` shape:

```json
{
  "arbitrum": {
    "USDt": { "address": "0x...", "decimals": 6 },
    "XAUt": { "address": "0x...", "decimals": 6 }
  },
  "base": {
    "USDt": { "address": "0x...", "decimals": 6 },
    "XAUt": { "address": "0x...", "decimals": 6 }
  }
}
```

Suggested minimal `contributor_wallets.json` shape:

```json
{
  "demo-dev": "0x1234...abcd",
  "alice": "0x9876...ef01"
}
```

### Phase 2 - Configure `.env` with real values

In `.env`, set:

- `WALLET_MODE=wdk`
- `WDK_MODULE=<your_real_module_name>`
- `CHECKING_WALLET_ADDRESS=<real address>`
- `TREASURY_WALLET_ADDRESS=<real address>`
- `GITHUB_REPO_OWNER=<org/user>`
- `GITHUB_REPO_NAME=<repo>`
- `GITHUB_TOKEN=<fine-grained token>`
- `ALLOWED_CHAINS=arbitrum,base`

Optional but recommended:

- set `ENABLE_HEDGE=false` until swap route is tested
- set `EVALUATION_INTERVAL_SECONDS=60` during development

### Phase 3 - Implement `WdkWalletClient` with real calls

Edit `src/axiom/wallet/wdk_wallet_client.py`:

1. In `__init__`:
   - load token and protocol maps from `config/*.json`
   - initialize real WDK SDK client/session/provider
   - initialize signer account for `CHECKING_WALLET_ADDRESS`

2. In `get_balance`:
   - resolve chain + token contract
   - call SDK balance API
   - convert base units by decimals from `token_map.json`

3. In `transfer`:
   - resolve token contract and decimals
   - convert amount to integer base units
   - build/send transfer tx via WDK
   - return real tx hash only

4. In `move_to_yield`:
   - choose route for protocol from `protocol_map.json`
   - perform approve (if required)
   - perform deposit tx
   - return final tx hash

5. In `hedge_to_xaut`:
   - route USDt -> XAUt from `protocol_map.json`
   - perform swap tx
   - return real tx hash

Hard rule: in `wdk` mode, never return synthetic hashes like `wdk-tx-*`.

### Phase 4 - Replace mock payout mapping

Edit `src/axiom/github/github_client.py`:

- remove synthetic payout address generation
- load `data/contributor_wallets.json`
- when PR merges:
  - map `author` to wallet address
  - if missing mapping, skip payout and log explicit reason

### Phase 5 - Add safety checks before mainnet actions

Before sending any tx:

1. verify destination address format
2. verify chain is in `ALLOWED_CHAINS`
3. verify token and decimals exist in `token_map.json`
4. verify `amount > 0`
5. verify `balance >= amount`

### Phase 6 - Test sequence (must pass in order)

1. Wallet read-only test  
   - run one call to `get_balance` for each chain/token pair
2. Transfer test  
   - send tiny amount to a controlled test address
3. Yield deposit test  
   - run with small amount and capture tx hash
4. Hedge swap test  
   - run only after transfer and deposit are stable
5. Full agent cycle  
   - `python run.py --rules rules/mandate.example.json --once`

### Phase 7 - Evidence to keep for hackathon submission

Store these in `docs/wdk_setup_notes.md`:

- SDK/package versions used
- chain RPC endpoints used
- token contract addresses used
- sample tx hashes for:
  - payout transfer
  - yield deposit
  - optional hedge swap
- any skipped actions and the exact safety/profitability reason

This evidence directly supports technical correctness and economic soundness judging criteria.

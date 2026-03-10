import "dotenv/config";
import express from "express";
import WDK from "@tetherto/wdk";
import WalletManagerEvm from "@tetherto/wdk-wallet-evm";
import { createPublicClient, encodeFunctionData, http } from "viem";

const app = express();
app.use(express.json());

const PORT = Number(process.env.PORT || 8787);

const CHAIN_CONFIG = {
  bnb: { provider: process.env.BSC_RPC_URL || "https://bsc-dataseed.binance.org" },
  polygon: { provider: process.env.POLYGON_RPC_URL || "https://polygon-rpc.com" },
};

const ERC20_ABI = [
  {
    type: "function",
    name: "balanceOf",
    stateMutability: "view",
    inputs: [{ name: "owner", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
  },
  {
    type: "function",
    name: "transfer",
    stateMutability: "nonpayable",
    inputs: [
      { name: "to", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    outputs: [{ name: "", type: "bool" }],
  },
];

function toDecimalString(rawAmount, decimals) {
  const value = BigInt(rawAmount);
  const base = BigInt(10) ** BigInt(decimals);
  const whole = value / base;
  const fraction = value % base;
  if (fraction === 0n) {
    return whole.toString();
  }
  const fractionStr = fraction.toString().padStart(decimals, "0").replace(/0+$/, "");
  return `${whole.toString()}.${fractionStr}`;
}

function assertAddressLike(value, fieldName) {
  if (typeof value !== "string" || !value.startsWith("0x") || value.length !== 42) {
    throw new Error(`Invalid address for ${fieldName}`);
  }
}

let wdk;
async function getWdk() {
  if (wdk) {
    return wdk;
  }
  const seedPhrase = process.env.WDK_SEED_PHRASE;
  if (!seedPhrase) {
    throw new Error("WDK_SEED_PHRASE is required in wdk_service/.env");
  }
  wdk = new WDK(seedPhrase)
    .registerWallet("bnb", WalletManagerEvm, CHAIN_CONFIG.bnb)
    .registerWallet("polygon", WalletManagerEvm, CHAIN_CONFIG.polygon);
  return wdk;
}

async function getAccount(chain) {
  if (!CHAIN_CONFIG[chain]) {
    throw new Error(`Unsupported chain '${chain}'`);
  }
  const sdk = await getWdk();
  return sdk.getAccount(chain, 0);
}

function buildPublicClient(chain) {
  const cfg = CHAIN_CONFIG[chain];
  if (!cfg?.provider) {
    throw new Error(`Missing provider URL for chain '${chain}'`);
  }
  return createPublicClient({ transport: http(cfg.provider) });
}

function extractHash(result) {
  if (!result) {
    throw new Error("Transaction response is empty");
  }
  if (typeof result === "string") {
    return result;
  }
  return result.hash || result.tx_hash || result.transactionHash;
}

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.post("/balance", async (req, res) => {
  try {
    const { chain, address, token_address: tokenAddress, decimals } = req.body;
    assertAddressLike(address, "address");
    const account = await getAccount(chain);

    if (tokenAddress === "native") {
      const accountAddress = await account.getAddress();
      if (accountAddress.toLowerCase() === address.toLowerCase()) {
        const raw = await account.getBalance();
        return res.json({ ok: true, balance: toDecimalString(raw.toString(), Number(decimals || 18)) });
      }
      const client = buildPublicClient(chain);
      const raw = await client.getBalance({ address });
      return res.json({ ok: true, balance: toDecimalString(raw.toString(), Number(decimals || 18)) });
    }

    assertAddressLike(tokenAddress, "token_address");
    const client = buildPublicClient(chain);
    const raw = await client.readContract({
      abi: ERC20_ABI,
      address: tokenAddress,
      functionName: "balanceOf",
      args: [address],
    });
    return res.json({ ok: true, balance: toDecimalString(raw.toString(), Number(decimals || 18)) });
  } catch (error) {
    return res.status(400).json({ ok: false, error: String(error?.message || error) });
  }
});

app.post("/transfer", async (req, res) => {
  try {
    const {
      chain,
      token_address: tokenAddress,
      from_address: fromAddress,
      to_address: toAddress,
      amount,
    } = req.body;
    assertAddressLike(fromAddress, "from_address");
    assertAddressLike(toAddress, "to_address");
    const account = await getAccount(chain);
    const accountAddress = await account.getAddress();
    if (accountAddress.toLowerCase() !== fromAddress.toLowerCase()) {
      throw new Error(`from_address does not match WDK account (${accountAddress})`);
    }

    let txResult;
    if (tokenAddress === "native") {
      txResult = await account.sendTransaction({
        to: toAddress,
        value: BigInt(amount),
      });
    } else {
      assertAddressLike(tokenAddress, "token_address");
      const data = encodeFunctionData({
        abi: ERC20_ABI,
        functionName: "transfer",
        args: [toAddress, BigInt(amount)],
      });
      txResult = await account.sendTransaction({
        to: tokenAddress,
        value: 0n,
        data,
      });
    }

    const txHash = extractHash(txResult);
    if (!txHash) {
      throw new Error("Unable to extract tx hash from WDK transaction response");
    }
    return res.json({ ok: true, tx_hash: txHash });
  } catch (error) {
    return res.status(400).json({ ok: false, error: String(error?.message || error) });
  }
});

app.post("/deposit", async (req, res) => {
  try {
    const {
      chain,
      token_address: tokenAddress,
      from_address: fromAddress,
      amount,
      route = {},
    } = req.body;
    const destination = route.pool_address || route.destination_address;
    if (!destination) {
      throw new Error("Missing route.pool_address or route.destination_address for deposit");
    }
    assertAddressLike(destination, "deposit destination");
    const account = await getAccount(chain);
    const accountAddress = await account.getAddress();
    if (accountAddress.toLowerCase() !== String(fromAddress).toLowerCase()) {
      throw new Error(`from_address does not match WDK account (${accountAddress})`);
    }
    assertAddressLike(tokenAddress, "token_address");
    const data = encodeFunctionData({
      abi: ERC20_ABI,
      functionName: "transfer",
      args: [destination, BigInt(amount)],
    });
    const txResult = await account.sendTransaction({
      to: tokenAddress,
      value: 0n,
      data,
    });
    const txHash = extractHash(txResult);
    if (!txHash) {
      throw new Error("Unable to extract tx hash from deposit response");
    }
    return res.json({ ok: true, tx_hash: txHash });
  } catch (error) {
    return res.status(400).json({ ok: false, error: String(error?.message || error) });
  }
});

app.post("/swap", async (req, res) => {
  try {
    const { route = {} } = req.body;
    if (!route || route.enabled !== true) {
      throw new Error("Swap route is disabled or not configured.");
    }
    throw new Error("Swap endpoint scaffolded but not yet wired to a live WDK protocol module.");
  } catch (error) {
    return res.status(400).json({ ok: false, error: String(error?.message || error) });
  }
});

app.listen(PORT, () => {
  console.log(`Axiom WDK service listening on http://127.0.0.1:${PORT}`);
});

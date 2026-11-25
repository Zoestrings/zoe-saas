"""Solana & EVM Token Intelligence Scanner (Mega-Module 1: Holder & LP Intelligence).

Provides deterministic on-chain and market intelligence:
- Top 10 Holder Concentration
- Liquidity Pool (LP) Lock & Burn Verification
- Developer / Deployer Wallet Holding Analysis
- Mint & Freeze Authority Checks
- Evidence-based Deterministic Risk Evaluation
"""

import asyncio
from datetime import datetime, timezone
import os
import re
from typing import Any, Dict, List, Optional
import httpx

from zoe.utils.logging import get_logger

logger = get_logger("zoe.tools.scanner")

# Base58 character set for Solana contract addresses (length 32 to 44)
SOLANA_CA_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
# EVM address pattern
EVM_CA_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")


def is_valid_solana_ca(ca: str) -> bool:
    """Validate whether a string matches standard Solana base58 public key format."""
    if not ca or not isinstance(ca, str):
        return False
    clean = ca.strip()
    return bool(SOLANA_CA_REGEX.match(clean))


def is_valid_evm_ca(ca: str) -> bool:
    """Validate whether a string matches standard EVM 0x contract address format."""
    if not ca or not isinstance(ca, str):
        return False
    return bool(EVM_CA_REGEX.match(ca.strip()))


def detect_chain(address: str) -> str:
    """Detect blockchain family for a given contract address.
    
    Returns:
    - 'evm' if starts with '0x' and is 42 hex chars.
    - 'solana' if 32-44 base58 characters.
    - 'unknown' otherwise.
    """
    if not address or not isinstance(address, str):
        return "unknown"
    clean = address.strip()
    if is_valid_evm_ca(clean):
        return "evm"
    if is_valid_solana_ca(clean):
        return "solana"
    return "unknown"


# Mapping from DexScreener chainId to GoPlus chain_id parameter
GOPLUS_CHAIN_MAP: Dict[str, str] = {
    "ethereum": "1",
    "eth": "1",
    "bsc": "56",
    "binance": "56",
    "base": "8453",
    "arbitrum": "42161",
    "polygon": "137",
    "polygon_pos": "137",
    "optimism": "10",
    "avalanche": "43114",
    "avax": "43114",
}

# Mapping from chainId to standardized UI display names
CHAIN_DISPLAY_MAP: Dict[str, str] = {
    "solana": "Solana",
    "ethereum": "Ethereum",
    "eth": "Ethereum",
    "base": "Base",
    "bsc": "BSC",
    "binance": "BSC",
    "arbitrum": "Arbitrum",
    "polygon": "Polygon",
    "polygon_pos": "Polygon",
    "optimism": "Optimism",
    "avalanche": "Avalanche",
}


def format_currency(value: Optional[float], decimals: int = 2) -> str:
    """Format floating point numbers as human-readable USD."""
    if value is None or value < 0:
        return "N/A"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    if value < 0.000001:
        return f"{value:.8f}"
    if value < 0.01:
        return f"{value:.6f}"
    return f"{value:,.{decimals}f}"


def format_price(value: Optional[float]) -> str:
    """Format token spot price with precision."""
    if value is None:
        return "N/A"
    if value == 0:
        return "0.00"
    if value < 0.000001:
        return f"{value:.8f}"
    if value < 0.001:
        return f"{value:.6f}"
    if value < 1.0:
        return f"{value:.4f}"
    return f"{value:,.2f}"


def shorten_ca(ca: str) -> str:
    """Return First 4...Last 4 representation of a contract address."""
    clean = ca.strip()
    if len(clean) <= 8:
        return clean
    return f"{clean[:4]}...{clean[-4:]}"


async def fetch_dexscreener_market_data(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch live market and trading pair metrics from DexScreener."""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
    result: Dict[str, Any] = {
        "found": False,
        "chain_id": None,
        "chain_name": None,
        "name": None,
        "symbol": None,
        "price_usd": None,
        "market_cap": None,
        "liquidity_usd": None,
        "volume_24h": None,
        "pair_url": None,
        "pair_created_at": None,
    }

    try:
        if client:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            pairs = data.get("pairs") or []
            if pairs:
                is_sol = is_valid_solana_ca(ca)
                if is_sol:
                    solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                    target_pairs = solana_pairs if solana_pairs else pairs
                else:
                    target_pairs = pairs

                sorted_pairs = sorted(
                    target_pairs,
                    key=lambda p: float(p.get("liquidity", {}).get("usd") or 0.0) if isinstance(p.get("liquidity"), dict) else 0.0,
                    reverse=True,
                )
                top_pair = sorted_pairs[0]
                raw_chain = (top_pair.get("chainId") or "").lower()
                result["found"] = True
                result["chain_id"] = raw_chain
                result["chain_name"] = CHAIN_DISPLAY_MAP.get(
                    raw_chain,
                    raw_chain.capitalize() if raw_chain else ("Solana" if is_sol else "Ethereum"),
                )
                base = top_pair.get("baseToken", {})
                result["name"] = base.get("name")
                result["symbol"] = base.get("symbol")
                try:
                    result["price_usd"] = float(top_pair.get("priceUsd")) if top_pair.get("priceUsd") is not None else None
                except (ValueError, TypeError):
                    result["price_usd"] = None

                mcap = top_pair.get("marketCap") or top_pair.get("fdv")
                try:
                    result["market_cap"] = float(mcap) if mcap is not None else None
                except (ValueError, TypeError):
                    result["market_cap"] = None

                liq = top_pair.get("liquidity", {})
                if isinstance(liq, dict):
                    try:
                        result["liquidity_usd"] = float(liq.get("usd")) if liq.get("usd") is not None else None
                    except (ValueError, TypeError):
                        result["liquidity_usd"] = None

                vol = top_pair.get("volume", {})
                if isinstance(vol, dict):
                    try:
                        result["volume_24h"] = float(vol.get("h24")) if vol.get("h24") is not None else None
                    except (ValueError, TypeError):
                        result["volume_24h"] = None

                result["pair_url"] = top_pair.get("url")
                result["pair_created_at"] = top_pair.get("pairCreatedAt")
                result["info"] = top_pair.get("info") or {}
    except Exception as exc:
        logger.warning("DexScreener fetch error for %s: %s", ca, exc)

    return result


async def fetch_goplus_solana_security(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch on-chain security metrics from GoPlus Solana API with LP and creator extraction."""
    url = f"https://api.gopluslabs.io/api/v1/solana/token_security?contract_addresses={ca}"
    result: Dict[str, Any] = {
        "success": False,
        "mint_revoked": None,
        "freeze_revoked": None,
        "top_10_holders_percent": None,
        "holder_count": None,
        "is_honeypot": False,
        "lp_locked": False,
        "lp_lock_percent": 0.0,
        "creator_address": None,
        "dev_wallet_percent": 0.0,
        "source": "GoPlus",
    }

    try:
        if client:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            payload = data.get("result", {})
            token_data = payload.get(ca) if isinstance(payload, dict) else None

            if token_data and isinstance(token_data, dict):
                result["success"] = True

                # 1. Mint authority: '0' = revoked, '1' = active
                mintable_info = token_data.get("mintable", {})
                if isinstance(mintable_info, dict):
                    status = str(mintable_info.get("status", ""))
                    result["mint_revoked"] = (status == "0")

                # 2. Freeze authority: '0' = revoked, '1' = active
                freezable_info = token_data.get("freezable", {})
                if isinstance(freezable_info, dict):
                    status = str(freezable_info.get("status", ""))
                    result["freeze_revoked"] = (status == "0")

                # 3. Honeypot check
                if str(token_data.get("non_transferable", "0")) == "1":
                    result["is_honeypot"] = True

                # 4. Creator / Deployer Address
                creators = token_data.get("creators") or []
                creator_addr = None
                if isinstance(creators, list) and creators:
                    c0 = creators[0]
                    creator_addr = c0.get("address") if isinstance(c0, dict) else str(c0)
                if not creator_addr:
                    mut_auth = token_data.get("metadata_mutable", {}).get("metadata_upgrade_authority", [])
                    if isinstance(mut_auth, list) and mut_auth:
                        creator_addr = mut_auth[0].get("address")
                result["creator_address"] = creator_addr

                # 5. Holders Analysis & Dev Wallet Balance
                holders = token_data.get("holders") or []
                if isinstance(holders, list) and holders:
                    top_10 = holders[:10]
                    total_pct = 0.0
                    for h in top_10:
                        try:
                            pct_val = float(h.get("percent", 0.0))
                            total_pct += (pct_val * 100.0) if pct_val <= 1.0 else pct_val
                        except (ValueError, TypeError):
                            pass
                    result["top_10_holders_percent"] = round(total_pct, 2)

                    # Check creator holding
                    if creator_addr:
                        dev_holder = next(
                            (h for h in holders if h.get("account") == creator_addr),
                            None
                        )
                        if dev_holder:
                            p = float(dev_holder.get("percent", 0.0))
                            result["dev_wallet_percent"] = round((p * 100.0) if p <= 1.0 else p, 2)

                try:
                    result["holder_count"] = int(token_data.get("holder_count", 0))
                except (ValueError, TypeError):
                    result["holder_count"] = None

                # 6. LP Lock Analysis
                dex_pools = token_data.get("dex") or []
                max_burn = 0.0
                for pool in dex_pools:
                    b_pct = pool.get("burn_percent")
                    if b_pct is not None:
                        try:
                            val = float(b_pct)
                            if val > max_burn:
                                max_burn = val
                        except (ValueError, TypeError):
                            pass

                result["lp_lock_percent"] = round(max_burn, 2)
                # Consider locked if >= 70% of pool is burned or LP tokens renounced
                result["lp_locked"] = (max_burn >= 70.0)

    except Exception as exc:
        logger.warning("GoPlus fetch error for %s: %s", ca, exc)

    return result


async def fetch_goplus_evm_security(
    ca: str,
    chain_id: str = "1",
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch on-chain security metrics from GoPlus EVM API (Honeypot, Taxes, Contract Verification)."""
    clean_ca = ca.strip().lower()
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={clean_ca}"
    result: Dict[str, Any] = {
        "success": False,
        "chain_id": chain_id,
        "is_honeypot": False,
        "is_open_source": False,
        "buy_tax": 0.0,
        "sell_tax": 0.0,
        "cannot_sell_all": False,
        "is_mintable": False,
        "mint_revoked": True,
        "freeze_revoked": True,
        "top_10_holders_percent": None,
        "holder_count": None,
        "creator_address": None,
        "dev_wallet_percent": 0.0,
        "lp_locked": False,
        "lp_lock_percent": 0.0,
        "source": "GoPlus EVM",
    }

    try:
        if client:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            payload = data.get("result", {})
            token_data = payload.get(clean_ca) if isinstance(payload, dict) else None

            if token_data and isinstance(token_data, dict):
                result["success"] = True

                # 1. Honeypot check
                is_hp = str(token_data.get("is_honeypot", "0")) == "1"
                cannot_sell = str(token_data.get("cannot_sell_all", "0")) == "1"
                result["is_honeypot"] = (is_hp or cannot_sell)
                result["cannot_sell_all"] = cannot_sell

                # 2. Open Source / Contract Verification
                result["is_open_source"] = str(token_data.get("is_open_source", "0")) == "1"

                # 3. Buy & Sell Taxes
                try:
                    b_tax = float(token_data.get("buy_tax") or 0.0)
                    result["buy_tax"] = round(b_tax * 100.0 if b_tax <= 1.0 and b_tax > 0 else b_tax, 2)
                except (ValueError, TypeError):
                    result["buy_tax"] = 0.0

                try:
                    s_tax = float(token_data.get("sell_tax") or 0.0)
                    result["sell_tax"] = round(s_tax * 100.0 if s_tax <= 1.0 and s_tax > 0 else s_tax, 2)
                except (ValueError, TypeError):
                    result["sell_tax"] = 0.0

                # 4. Mintable
                is_mint = str(token_data.get("is_mintable", "0")) == "1"
                result["is_mintable"] = is_mint
                result["mint_revoked"] = not is_mint

                # 5. Creator / Owner Address & Dev Holding
                creator = token_data.get("creator_address") or token_data.get("owner_address")
                result["creator_address"] = creator

                try:
                    creator_pct = float(token_data.get("creator_percent") or token_data.get("owner_percent") or 0.0)
                    result["dev_wallet_percent"] = round(creator_pct * 100.0 if creator_pct <= 1.0 and creator_pct > 0 else creator_pct, 2)
                except (ValueError, TypeError):
                    result["dev_wallet_percent"] = 0.0

                # 6. Holders Analysis
                holders = token_data.get("holders") or []
                if isinstance(holders, list) and holders:
                    top_10 = holders[:10]
                    total_pct = 0.0
                    for h in top_10:
                        try:
                            pct_val = float(h.get("percent", 0.0))
                            total_pct += (pct_val * 100.0) if pct_val <= 1.0 else pct_val
                        except (ValueError, TypeError):
                            pass
                    result["top_10_holders_percent"] = round(total_pct, 2)

                try:
                    result["holder_count"] = int(token_data.get("holder_count", 0))
                except (ValueError, TypeError):
                    result["holder_count"] = None

                # 7. LP Lock
                lp_holders = token_data.get("lp_holders") or []
                max_lp_lock = 0.0
                dead_addrs = {
                    "0x000000000000000000000000000000000000dead",
                    "0x0000000000000000000000000000000000000000",
                }
                for lph in lp_holders:
                    if isinstance(lph, dict):
                        addr = str(lph.get("address", "")).lower()
                        is_locked = str(lph.get("is_locked", "0")) == "1" or addr in dead_addrs
                        if is_locked:
                            try:
                                l_pct = float(lph.get("percent", 0.0))
                                l_pct_100 = (l_pct * 100.0) if l_pct <= 1.0 else l_pct
                                if l_pct_100 > max_lp_lock:
                                    max_lp_lock = l_pct_100
                            except (ValueError, TypeError):
                                pass

                result["lp_lock_percent"] = round(max_lp_lock, 2)
                result["lp_locked"] = (max_lp_lock >= 50.0)

    except Exception as exc:
        logger.warning("GoPlus EVM fetch error for %s (chain %s): %s", clean_ca, chain_id, exc)

    return result


async def fetch_rugcheck_fallback(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fallback security check using RugCheck API with LP and creator data."""
    url = f"https://api.rugcheck.xyz/v1/tokens/{ca}/report"
    result: Dict[str, Any] = {
        "success": False,
        "mint_revoked": None,
        "freeze_revoked": None,
        "top_10_holders_percent": None,
        "lp_locked": False,
        "lp_lock_percent": 0.0,
        "creator_address": None,
        "dev_wallet_percent": 0.0,
        "source": "RugCheck",
    }
    try:
        if client:
            resp = await client.get(url, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url)

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                result["success"] = True
                token_data = data.get("token", {})

                result["mint_revoked"] = (token_data.get("mintAuthority") is None)
                result["freeze_revoked"] = (token_data.get("freezeAuthority") is None)

                # Creator
                creator_addr = data.get("creator")
                result["creator_address"] = creator_addr

                # Top Holders & Dev Wallet
                top_holders = data.get("topHolders") or []
                if isinstance(top_holders, list) and top_holders:
                    top_10 = top_holders[:10]
                    total_pct = sum(float(h.get("pct", 0.0)) for h in top_10 if "pct" in h)
                    result["top_10_holders_percent"] = round(total_pct, 2)

                    if creator_addr:
                        dev_h = next((h for h in top_holders if h.get("address") == creator_addr), None)
                        if dev_h and "pct" in dev_h:
                            result["dev_wallet_percent"] = round(float(dev_h["pct"]), 2)

                # LP Lock Check
                markets = data.get("markets") or []
                if markets and isinstance(markets[0], dict):
                    m0 = markets[0]
                    lp_info = m0.get("lp", {})
                    if isinstance(lp_info, dict):
                        lp_locked_pct = float(lp_info.get("lpLockedPct") or 0.0)
                        result["lp_lock_percent"] = round(lp_locked_pct, 2)
                        result["lp_locked"] = (lp_locked_pct >= 70.0)
                        
                # Check risks for LP unlock mention
                risks = data.get("risks") or []
                for r in risks:
                    r_name = str(r.get("name", "")).lower()
                    if "lp not locked" in r_name or "unlocked lp" in r_name:
                        result["lp_locked"] = False
                    elif "copycat" in r_name or "honeypot" in r_name:
                        result["is_honeypot"] = True

    except Exception as exc:
        logger.debug("RugCheck fallback fetch error for %s: %s", ca, exc)

    return result


# =========================================================================
# Mega-Module 7: Deep Wallet Tracing & CEX Entity Identification
# =========================================================================

KNOWN_SOLANA_CEX_WALLETS: Dict[str, str] = {
    "2OJv9BAiHUHGux3qWBKNmmukysAQGunTVGZm19U977Fi": "Binance",
    "5tzFkiKscGBspauqncduazSyeWDVGsLvv7MttdTQDPjf": "Binance",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "Binance",
    "H8sMJSCQxfKiFTCfDR3DUMLPwcRbM61LgfgnpkAz9GWB": "Coinbase",
    "2AQdpHJ2JpcEgPiATUXjQxA8QmafFegfQwSLWSprPics": "Coinbase",
    "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPgv7npb": "Coinbase",
    "FWznbcNXWQuHTawe9RxvQ2LdJF2YmtV21TuGLZFMAz9G": "Kraken",
    "5VCwKtCXgCJ6kit5FybXjvmsWgf6xVxAZT8xYT5GnyPM": "OKX",
    "9un5wqE3q4oCvsStciNuuvnPzvgK9Hq2H5oQz6dDkmrG": "OKX",
    "AC5RDfQFmDS1deWZos921qbhirGLCmEYSLgWAEmv246Q": "Bybit",
    "BmFdpraQmgrBkAcSYurggVr84PmCtxuWGWPrTYqPMUeh": "KuCoin",
    "ASTyfSima4LLAdDgoFGkgqoKowG1LZFDr9fAQrg7iaJZ": "MEXC",
    "u6357Gm6WHhSbBvDqcwpnCLnWJ9GzJHdz8k1uC2xZ7n": "Gate.io",
}


async def trace_wallet(
    wallet_address: Optional[str],
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Perform on-chain trace on Solana wallet to find funding source, CEX linkage, and outflow risk."""
    default_res: Dict[str, Any] = {
        "traced": False,
        "wallet_address": wallet_address or "Unknown",
        "funding_source": "Unknown",
        "funding_source_short": "Unknown",
        "funding_entity": "Unknown",
        "is_cex_funded": False,
        "is_fresh_funding_wallet": False,
        "initial_funding_sol": 0.0,
        "first_tx_hash": None,
        "outflow_risk": "UNKNOWN",
        "outflow_details": "No wallet activity traced.",
        "risk_level": "UNKNOWN",
        "risk_reason": "Unable to trace wallet history.",
        "total_tx_count": 0,
    }

    if not wallet_address:
        return default_res

    clean_addr = wallet_address.strip()
    default_res["wallet_address"] = clean_addr

    if not is_valid_solana_ca(clean_addr):
        return default_res

    rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com").strip()

    # Step 1: Query getSignaturesForAddress
    sig_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            clean_addr,
            {"limit": 20}
        ]
    }

    try:
        if client:
            resp = await client.post(rpc_url, json=sig_payload, timeout=8.0)
        else:
            async with httpx.AsyncClient(timeout=8.0) as local_client:
                resp = await local_client.post(rpc_url, json=sig_payload)

        if resp.status_code != 200:
            return default_res

        data = resp.json()
        signatures = data.get("result") or []
        if not signatures or not isinstance(signatures, list):
            return default_res

        total_tx = len(signatures)
        default_res["total_tx_count"] = total_tx
        default_res["traced"] = True

        # Oldest signature in this batch (reverse chronological: last element is earliest)
        oldest_sig_obj = signatures[-1]
        oldest_sig = oldest_sig_obj.get("signature")
        default_res["first_tx_hash"] = oldest_sig

        # Step 2: Query getTransaction for oldest signature to find initial funder
        tx_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "getTransaction",
            "params": [
                oldest_sig,
                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
            ]
        }

        if client:
            tx_resp = await client.post(rpc_url, json=tx_payload, timeout=8.0)
        else:
            async with httpx.AsyncClient(timeout=8.0) as local_client:
                tx_resp = await local_client.post(rpc_url, json=tx_payload)

        funder = "Unknown"
        funding_sol = 0.0

        if tx_resp.status_code == 200:
            tx_data = tx_resp.json()
            tx_res = tx_data.get("result") or {}
            meta = tx_res.get("meta") or {}
            msg = tx_res.get("transaction", {}).get("message", {})
            account_keys = msg.get("accountKeys") or []

            # Find wallet index
            wallet_idx = -1
            for idx, ak in enumerate(account_keys):
                pubkey = ak.get("pubkey") if isinstance(ak, dict) else str(ak)
                if pubkey == clean_addr:
                    wallet_idx = idx
                    break

            pre_balances = meta.get("preBalances") or []
            post_balances = meta.get("postBalances") or []

            if wallet_idx != -1 and wallet_idx < len(pre_balances) and wallet_idx < len(post_balances):
                diff = post_balances[wallet_idx] - pre_balances[wallet_idx]
                if diff > 0:
                    funding_sol = round(diff / 1_000_000_000, 4)

            # Senders: Check parsed instructions or signer account 0
            instructions = msg.get("instructions") or []
            found_funder = False
            for ins in instructions:
                if isinstance(ins, dict) and ins.get("program") == "system":
                    parsed = ins.get("parsed") or {}
                    if parsed.get("type") == "transfer":
                        info = parsed.get("info") or {}
                        dest = info.get("destination")
                        source = info.get("source")
                        if dest == clean_addr and source:
                            funder = source
                            found_funder = True
                            if "lamports" in info:
                                funding_sol = round(float(info["lamports"]) / 1_000_000_000, 4)
                            break

            if not found_funder and account_keys:
                first_key = account_keys[0]
                signer = first_key.get("pubkey") if isinstance(first_key, dict) else str(first_key)
                if signer != clean_addr:
                    funder = signer

        default_res["funding_source"] = funder
        default_res["funding_source_short"] = shorten_ca(funder)
        default_res["initial_funding_sol"] = funding_sol

        # Step 3: Check CEX or Fresh Wallet
        if funder in KNOWN_SOLANA_CEX_WALLETS:
            cex_name = KNOWN_SOLANA_CEX_WALLETS[funder]
            default_res["funding_entity"] = f"{cex_name} Hot Wallet"
            default_res["is_cex_funded"] = True
            default_res["risk_level"] = "LOW"
            default_res["risk_reason"] = f"Legitimately funded via {cex_name} exchange hot wallet."
        elif total_tx <= 3:
            default_res["funding_entity"] = "Fresh / Burner Wallet"
            default_res["is_fresh_funding_wallet"] = True
            default_res["risk_level"] = "HIGH"
            default_res["risk_reason"] = "Funded by a fresh unverified wallet with no exchange trail (Sybil risk)."
        elif funder != "Unknown":
            default_res["funding_entity"] = "Private / Non-CEX Wallet"
            default_res["risk_level"] = "MEDIUM"
            default_res["risk_reason"] = "Funded by a private on-chain wallet."
        else:
            default_res["funding_entity"] = "Unknown"
            default_res["risk_level"] = "UNKNOWN"
            default_res["risk_reason"] = "Unable to resolve initial funder."

        # Step 4: Outflow Risk (Check if dev has sent funds out recently)
        default_res["outflow_risk"] = "LOW"
        default_res["outflow_details"] = "No suspicious capital outflow detected from Dev Wallet."

        if len(signatures) > 1:
            recent_sig = signatures[0].get("signature")
            if recent_sig and recent_sig != oldest_sig:
                try:
                    rec_payload = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "getTransaction",
                        "params": [recent_sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                    }
                    if client:
                        rec_resp = await client.post(rpc_url, json=rec_payload, timeout=6.0)
                    else:
                        async with httpx.AsyncClient(timeout=6.0) as local_client:
                            rec_resp = await local_client.post(rpc_url, json=rec_payload)

                    if rec_resp.status_code == 200:
                        rec_res = rec_resp.json().get("result") or {}
                        rec_meta = rec_res.get("meta") or {}
                        rec_msg = rec_res.get("transaction", {}).get("message", {})
                        rec_keys = rec_msg.get("accountKeys") or []
                        w_idx = -1
                        for idx, ak in enumerate(rec_keys):
                            pk = ak.get("pubkey") if isinstance(ak, dict) else str(ak)
                            if pk == clean_addr:
                                w_idx = idx
                                break

                        rec_pre = rec_meta.get("preBalances") or []
                        rec_post = rec_meta.get("postBalances") or []
                        if w_idx != -1 and w_idx < len(rec_pre) and w_idx < len(rec_post):
                            diff = rec_pre[w_idx] - rec_post[w_idx]
                            drain_sol = diff / 1_000_000_000
                            if drain_sol > 5.0:
                                default_res["outflow_risk"] = "HIGH"
                                default_res["outflow_details"] = f"Recent outflow of {drain_sol:.2f} SOL from Dev Wallet detected."
                                default_res["risk_level"] = "HIGH"
                except Exception:
                    pass

    except Exception as exc:
        logger.debug("Wallet tracing error for %s: %s", wallet_address, exc)

    return default_res


async def investigate_project_osint(
    token_name: str,
    symbol: Optional[str] = None,
    market_info: Optional[Dict[str, Any]] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Execute Project & Founder OSINT intelligence investigation (Mega-Module 2).
    
    Searches official web presence, scrapes homepage for social links,
    and identifies public founders/executives via search queries.
    """
    clean_name = (token_name or "").strip()
    if clean_name.lower() in ("unknown token", "unknown", "n/a", ""):
        return {
            "website": "Unknown",
            "founder": "Unverified",
            "socials": {},
            "has_official_website": False,
            "twitter": None,
            "telegram": None,
            "discord": None,
            "github": None,
            "linkedin": None,
            "is_anonymous_founder": True,
            "evidence_sources": [],
        }

    evidence: List[str] = []
    website_url: Optional[str] = None
    twitter_url: Optional[str] = None
    telegram_url: Optional[str] = None
    discord_url: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    founder_name: Optional[str] = None

    # 1. Parse DexScreener verified info if available
    if market_info and isinstance(market_info, dict):
        websites = market_info.get("websites") or []
        for w in websites:
            if isinstance(w, dict) and w.get("url"):
                website_url = w["url"]
                evidence.append("DexScreener Official Registry")
                break
        socials = market_info.get("socials") or []
        for s in socials:
            if isinstance(s, dict) and s.get("url"):
                stype = (s.get("type") or "").lower()
                surl = s["url"]
                if "twitter" in stype or "x.com" in surl or "twitter.com" in surl:
                    twitter_url = twitter_url or surl
                elif "telegram" in stype or "t.me" in surl:
                    telegram_url = telegram_url or surl
                elif "discord" in stype:
                    discord_url = discord_url or surl
                elif "linkedin" in stype or "linkedin.com" in surl:
                    linkedin_url = linkedin_url or surl

    # 2. Search DuckDuckGo for Official Website if missing
    from zoe.tools.web_search import search_web
    if not website_url:
        search_query = f"{clean_name} official website"
        try:
            web_results = await search_web(search_query, max_results=3)
            for res in web_results:
                href = res.get("href") or ""
                # Filter out aggregators / social platforms
                if href and not any(skip in href.lower() for skip in (
                    "dexscreener.com", "dextools.io", "coingecko.com", "coinmarketcap.com",
                    "twitter.com", "x.com", "youtube.com", "t.me", "medium.com", "reddit.com"
                )):
                    website_url = href
                    evidence.append(f"DuckDuckGo Search: '{search_query}'")
                    break
        except Exception as exc:
            logger.debug("OSINT website search failed: %s", exc)

    # 3. Scrape website homepage for social links if present
    if website_url:
        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as scrape_client:
                resp = await scrape_client.get(
                    website_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                if resp.status_code == 200:
                    html_content = resp.text
                    evidence.append(f"Homepage Scrape: {website_url}")

                    # Regex patterns for social links
                    if not twitter_url:
                        tw_match = re.search(r'https?://(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})', html_content)
                        if tw_match and tw_match.group(1).lower() not in ("share", "intent", "home", "search", "status"):
                            twitter_url = tw_match.group(0)

                    if not telegram_url:
                        tg_match = re.search(r'https?://t\.me/([A-Za-z0-9_]{1,50})', html_content)
                        if tg_match and tg_match.group(1).lower() not in ("share", "joinchat"):
                            telegram_url = tg_match.group(0)

                    if not discord_url:
                        dc_match = re.search(r'https?://discord\.(?:gg|com/invite)/[A-Za-z0-9_-]+', html_content)
                        if dc_match:
                            discord_url = dc_match.group(0)

                    if not github_url:
                        gh_match = re.search(r'https?://github\.com/([A-Za-z0-9_-]{1,50})', html_content)
                        if gh_match and gh_match.group(1).lower() not in ("features", "pricing", "enterprise", "site"):
                            github_url = gh_match.group(0)

                    if not linkedin_url:
                        li_match = re.search(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9_-]+', html_content)
                        if li_match:
                            linkedin_url = li_match.group(0)
        except Exception as exc:
            logger.debug("OSINT website scraping error for %s: %s", website_url, exc)

    # 4. Search DuckDuckGo for Founder / CEO
    founder_query = f"{clean_name} crypto founder CEO"
    snippets_collected: List[str] = []
    try:
        founder_results = await search_web(founder_query, max_results=4)
        if founder_results:
            evidence.append(f"DuckDuckGo Search: '{founder_query}'")
            for fr in founder_results:
                title = fr.get("title") or ""
                body = fr.get("body") or ""
                snippets_collected.append(f"{title} - {body}")
    except Exception as exc:
        logger.debug("OSINT founder search failed: %s", exc)

    # 5. Parse founder name
    founder_patterns = [
        r'(?:co-founder|founder|creator|ceo)\s+(?:of\s+[A-Za-z0-9_\s]+\s+)?(?:is\s+|:\s+)?([A-Z][a-zA-Z0-9_\s]{1,25})',
        r'([A-Z][a-zA-Z0-9_\s]{1,20})\s+(?:is\s+the\s+)?(?:co-founder|founder|creator|ceo)\b',
        r'(?:founded|created)\s+by\s+([A-Z][a-zA-Z0-9_\s]{1,25})',
    ]
    stopwords = {"the", "a", "an", "this", "solana", "crypto", "coin", "token", "many", "everything", "popular", "meme", "here", "read", "how", "what", "who", "when"}
    for text in snippets_collected:
        for pat in founder_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                cand = m.group(1).strip()
                if cand.lower() not in stopwords and len(cand) >= 2:
                    founder_name = cand
                    break
        if founder_name:
            break

    is_anon = not bool(founder_name)
    display_founder = founder_name if founder_name else "Unverified"

    socials_dict: Dict[str, str] = {}
    if twitter_url:
        socials_dict["twitter"] = twitter_url
    if telegram_url:
        socials_dict["telegram"] = telegram_url
    if discord_url:
        socials_dict["discord"] = discord_url
    if github_url:
        socials_dict["github"] = github_url
    if linkedin_url:
        socials_dict["linkedin"] = linkedin_url

    return {
        "website": website_url if website_url else "Unknown",
        "founder": display_founder,
        "socials": socials_dict,
        "has_official_website": bool(website_url),
        "twitter": twitter_url,
        "telegram": telegram_url,
        "discord": discord_url,
        "github": github_url,
        "linkedin": linkedin_url,
        "is_anonymous_founder": is_anon,
        "evidence_sources": list(dict.fromkeys(evidence)),
    }


def evaluate_risk(
    market: Dict[str, Any],
    security: Dict[str, Any],
    osint: Optional[Dict[str, Any]] = None,
    wallet_trace: Optional[Dict[str, Any]] = None,
    chain: str = "Solana",
) -> Dict[str, Any]:
    """Upgraded Risk Assessment Engine for Mega-Module 1, 2, 7 & Multi-Chain EVM.
    
    Deterministic Rules:
    - If Honeypot -> CRITICAL
    - If Top 10 Holders > 80% -> CRITICAL
    - If Dev Wallet holds > 10% -> HIGH
    - If LP is NOT locked/renounced -> HIGH
    - If EVM: Taxes > 25% -> CRITICAL, Taxes > 10% -> HIGH, Unverified code -> HIGH
    - If Solana: Mint Authority active -> HIGH, Freeze Authority active -> HIGH
    - If Dev Wallet funded by fresh unverified burner wallet -> HIGH
    - If Dev Wallet actively moving funds out -> HIGH
    - If Dev Wallet funded by known CEX -> LOW / MEDIUM
    - If No website found -> MEDIUM ("No official website found.")
    - If Founder anonymous -> UNKNOWN/INFO ("Founder identity is unverified.")
    - If LP is locked and Top 10 < 40% (and mint revoked, freeze revoked, dev <= 5%) -> LOW
    """
    if not market.get("found") and not security.get("success"):
        return {
            "level": "UNKNOWN",
            "reasons": ["Token data not found on decentralized exchanges or security registries."],
            "critical_count": 0,
            "high_count": 0,
        }

    critical_reasons: List[str] = []
    high_reasons: List[str] = []
    medium_reasons: List[str] = []
    low_reasons: List[str] = []
    unknown_reasons: List[str] = []

    mint_revoked = security.get("mint_revoked")
    freeze_revoked = security.get("freeze_revoked")
    top_10_pct = security.get("top_10_holders_percent")
    liq_usd = market.get("liquidity_usd")
    is_honeypot = security.get("is_honeypot", False)
    lp_locked = security.get("lp_locked", False)
    lp_lock_pct = security.get("lp_lock_percent", 0.0)
    dev_pct = security.get("dev_wallet_percent", 0.0)

    # 1. Honeypot Check
    if is_honeypot:
        critical_reasons.append("Honeypot risk: token transfers are restricted or blocked")

    # 2. Holder Concentration Check
    # Rule: Top 10 Holders > 80% -> CRITICAL
    if top_10_pct is not None:
        if top_10_pct > 80.0:
            critical_reasons.append(f"Extreme holder concentration: Top 10 hold {top_10_pct:.1f}% (>80% threshold)")
        elif top_10_pct > 50.0:
            medium_reasons.append(f"Moderate holder concentration: Top 10 hold {top_10_pct:.1f}%")
        elif top_10_pct < 40.0:
            low_reasons.append(f"Healthy holder distribution: Top 10 hold {top_10_pct:.1f}% (<40%)")
        else:
            low_reasons.append(f"Acceptable holder distribution: Top 10 hold {top_10_pct:.1f}%")

    # 3. Developer Wallet Check
    # Rule: Dev Wallet holds > 10% -> HIGH
    if dev_pct is not None:
        if dev_pct > 10.0:
            high_reasons.append(f"Developer wallet holds {dev_pct:.1f}% of supply (>10% dump risk)")
        elif dev_pct > 5.0:
            medium_reasons.append(f"Developer wallet holds {dev_pct:.1f}% of supply")
        else:
            low_reasons.append(f"Developer wallet holds {dev_pct:.1f}% (Low risk)")

    # 4. Liquidity Lock Check
    # Rule: If LP is NOT locked/renounced -> HIGH
    if lp_locked:
        pct_tag = f" ({lp_lock_pct:.1f}% burned/locked)" if lp_lock_pct > 0 else ""
        low_reasons.append(f"Liquidity is Locked/Burned{pct_tag} (Safe)")
    else:
        high_reasons.append("Liquidity is NOT locked/renounced - High LP removal/rug risk")

    is_evm = chain.lower() != "solana"
    if is_evm:
        # 5. EVM-Specific Checks: Taxes, Contract Verification, Minting
        buy_tax = security.get("buy_tax")
        sell_tax = security.get("sell_tax")
        if buy_tax is not None and sell_tax is not None:
            if buy_tax > 25.0 or sell_tax > 25.0:
                critical_reasons.append(f"Extreme trading tax: Buy {buy_tax:.1f}%, Sell {sell_tax:.1f}% (>25% capital risk)")
            elif buy_tax > 10.0 or sell_tax > 10.0:
                high_reasons.append(f"High trading fees: Buy {buy_tax:.1f}%, Sell {sell_tax:.1f}% (>10%)")
            elif buy_tax <= 5.0 and sell_tax <= 5.0 and (buy_tax > 0 or sell_tax > 0):
                low_reasons.append(f"Low trading fee: Buy {buy_tax:.1f}%, Sell {sell_tax:.1f}%")
            elif buy_tax == 0.0 and sell_tax == 0.0:
                low_reasons.append("Zero trading tax (0% Buy / 0% Sell)")

        is_open_source = security.get("is_open_source")
        if is_open_source is False:
            high_reasons.append("Contract source code is unverified / closed-source on block explorer (Hidden risk)")
        elif is_open_source is True:
            low_reasons.append("Contract source code verified on block explorer (Open Source)")

        if security.get("is_mintable") is True:
            high_reasons.append("Contract has active minting capability (Supply inflation risk)")
    else:
        # 5. Solana Mint Authority Check
        if mint_revoked is False:
            high_reasons.append("Mint Authority is active (owner can inflate supply)")
        elif mint_revoked is True:
            low_reasons.append("Mint Authority is revoked (fixed supply)")

        # 6. Solana Freeze Authority Check
        if freeze_revoked is False:
            high_reasons.append("Freeze Authority is active (owner can freeze token accounts)")
        elif freeze_revoked is True:
            low_reasons.append("Freeze Authority is revoked (accounts cannot be frozen)")

    # 7. DEX Liquidity Check
    if liq_usd is not None:
        if liq_usd < 1_000:
            critical_reasons.append(f"Extremely low liquidity (${format_currency(liq_usd)})")
        elif liq_usd < 5_000:
            high_reasons.append(f"Low liquidity (${format_currency(liq_usd)})")
        elif liq_usd >= 50_000:
            low_reasons.append(f"Strong DEX liquidity (${format_currency(liq_usd)})")

    # 8. Project & Founder OSINT Checks (Mega-Module 2)
    if osint and isinstance(osint, dict):
        has_web = osint.get("has_official_website") or (osint.get("website") and osint.get("website") != "Unknown")
        if not has_web:
            medium_reasons.append("No official website found.")
        elif osint.get("website") and osint.get("website") != "Unknown":
            low_reasons.append(f"Official website verified: {osint.get('website')}")

        is_anon = osint.get("is_anonymous_founder") or (osint.get("founder") in ("Unverified", "Anonymous / Unverified", None))
        if is_anon:
            unknown_reasons.append("Founder identity is unverified.")
        elif osint.get("founder") and osint.get("founder") not in ("Unverified", "Anonymous / Unverified"):
            low_reasons.append(f"Public founder identified: {osint.get('founder')}")

    # 9. Deep Wallet Tracing Checks (Mega-Module 7)
    if wallet_trace and isinstance(wallet_trace, dict):
        if wallet_trace.get("is_fresh_funding_wallet"):
            high_reasons.append("Dev Wallet funded by fresh burner wallet with no exchange history (High Sybil risk)")
        elif wallet_trace.get("is_cex_funded"):
            low_reasons.append(f"Dev Wallet funded by verified exchange hot wallet ({wallet_trace.get('funding_entity')})")

        if wallet_trace.get("outflow_risk") == "HIGH":
            high_reasons.append(f"Dev Wallet outflow alert: {wallet_trace.get('outflow_details')}")

    # Deterministic Risk Hierarchy
    if critical_reasons:
        level = "CRITICAL"
        reasons = critical_reasons + high_reasons + medium_reasons + unknown_reasons
    elif high_reasons:
        level = "HIGH"
        reasons = high_reasons + medium_reasons + unknown_reasons + low_reasons
    elif medium_reasons:
        level = "MEDIUM"
        reasons = medium_reasons + unknown_reasons + low_reasons
    elif unknown_reasons:
        level = "LOW"
        reasons = unknown_reasons + low_reasons
    else:
        # Rule: LP is locked and Top 10 < 40% -> LOW risk
        level = "LOW"
        reasons = low_reasons

    return {
        "level": level,
        "reasons": reasons,
        "critical_count": len(critical_reasons),
        "high_count": len(high_reasons),
    }


def calculate_safety_score(data: Dict[str, Any]) -> int:
    """Calculate a quantified Safety Score (0-100) based on deterministic scanner signals.
    
    Scoring Rules:
    - Base score: 50
    - +20 if Liquidity is Locked
    - +20 if No Honeypot detected
    - +10 if Contract is Open Source / Verified (or Mint & Freeze Authorities both revoked)
    - +10 if Top 10 Holders < 30%
    - -30 if Honeypot detected
    - -20 if Top 10 Holders > 80%
    - -15 if Buy Tax > 10% or Sell Tax > 10%
    - -10 if Dev Wallet holds > 10%
    - Clamped strictly between 0 and 100
    """
    score = 50
    security = data.get("security", {})
    lp_intel = data.get("lp_intelligence", {})
    holder_intel = data.get("holder_intelligence", {})
    dev_intel = data.get("dev_wallet_intelligence", {})

    is_honeypot = security.get("is_honeypot", False)
    if is_honeypot:
        score -= 30
    else:
        score += 20

    # Liquidity Lock
    lp_locked = lp_intel.get("is_locked") if "is_locked" in lp_intel else security.get("lp_locked", False)
    if lp_locked:
        score += 20

    # Open Source / Verified (Solana: mint & freeze revoked)
    is_open_source = security.get("is_open_source")
    mint_revoked = security.get("mint_revoked")
    freeze_revoked = security.get("freeze_revoked")
    if is_open_source is True or (mint_revoked is True and freeze_revoked is True):
        score += 10

    # Top 10 Holders
    top_10 = holder_intel.get("top_10_percent") if holder_intel.get("top_10_percent") is not None else security.get("top_10_holders_percent")
    if top_10 is not None:
        if top_10 < 30.0:
            score += 10
        elif top_10 > 80.0:
            score -= 20

    # Buy / Sell Tax
    buy_tax = security.get("buy_tax")
    sell_tax = security.get("sell_tax")
    try:
        bt = float(buy_tax) if buy_tax is not None else 0.0
        st = float(sell_tax) if sell_tax is not None else 0.0
        if bt > 10.0 or st > 10.0:
            score -= 15
    except (ValueError, TypeError):
        pass

    # Dev Wallet holding
    dev_pct = dev_intel.get("holds_percent") if dev_intel.get("holds_percent") is not None else security.get("dev_wallet_percent")
    if dev_pct is not None and dev_pct > 10.0:
        score -= 10

    # Wallet Trace Intelligence (Mega-Module 7)
    wallet_trace = data.get("wallet_trace", {})
    if wallet_trace and isinstance(wallet_trace, dict):
        if wallet_trace.get("is_fresh_funding_wallet"):
            score -= 15
        elif wallet_trace.get("is_cex_funded"):
            score += 5
        if wallet_trace.get("outflow_risk") == "HIGH":
            score -= 20

    return max(0, min(100, score))


def _generate_fallback_summary(data: Dict[str, Any], score: int) -> str:
    """Generate deterministic 2-sentence risk summary if Groq LLM is unavailable."""
    name = data.get("name") or "This token"
    security = data.get("security", {})
    lp_intel = data.get("lp_intelligence", {})
    holder_intel = data.get("holder_intelligence", {})
    is_honeypot = security.get("is_honeypot", False)
    lp_locked = lp_intel.get("is_locked", False)
    top_10 = holder_intel.get("top_10_percent")

    if score < 30 or is_honeypot:
        return (
            f"{name} exhibits critical risk flags including active security threats and extreme centralization; extreme caution is advised. "
            "High probability of capital loss exists without independent contract verification."
        )
    elif score >= 70:
        lp_desc = "locked liquidity" if lp_locked else "active liquidity"
        holder_desc = f"a decentralized top 10 supply distribution ({top_10:.1f}%)" if top_10 and top_10 < 40 else "healthy contract parameters"
        return (
            f"{name} demonstrates a solid risk profile supported by {lp_desc} and {holder_desc}. "
            "No honeypot mechanisms or critical vulnerabilities were detected, though market risks remain present."
        )
    else:
        return (
            f"{name} reflects a moderate risk profile with mixed signals across its liquidity security and token distribution. "
            "Traders should exercise heightened diligence and review developer holdings before committing capital."
        )


async def generate_ai_summary(data: Dict[str, Any], score: int) -> str:
    """Generate a concise, 2-sentence AI security analyst summary using Groq LLM."""
    import os
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key or "YOUR_GROQ_API_KEY" in groq_key:
        return _generate_fallback_summary(data, score)

    summary_context = {
        "token_name": data.get("name"),
        "symbol": data.get("symbol"),
        "chain": data.get("chain"),
        "safety_score": score,
        "is_honeypot": data.get("security", {}).get("is_honeypot", False),
        "mint_revoked": data.get("security", {}).get("mint_revoked"),
        "freeze_revoked": data.get("security", {}).get("freeze_revoked"),
        "lp_locked": data.get("lp_intelligence", {}).get("is_locked"),
        "top_10_holders_percent": data.get("holder_intelligence", {}).get("top_10_percent"),
        "dev_wallet_percent": data.get("dev_wallet_intelligence", {}).get("holds_percent"),
        "website": (data.get("osint") or data.get("project_osint") or {}).get("website"),
        "founder": (data.get("osint") or data.get("project_osint") or {}).get("founder"),
    }

    system_prompt = (
        "You are a Senior Web3 Security Analyst. Based on the following scanner data, "
        "write a 2-sentence summary of the token's risk profile. Be objective. "
        "Do not give financial advice. If the score is below 30, state that extreme caution is advised."
    )
    user_prompt = f"Scanner Data:\n{json.dumps(summary_context, indent=2)}\nSafety Score: {score}/100"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 120,
                },
            )
            if resp.status_code == 200:
                res_json = resp.json()
                content = res_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if content:
                    return content
    except Exception as exc:
        logger.debug("Groq AI summary generation exception: %s", exc)

    return _generate_fallback_summary(data, score)


async def scan_solana_token(
    ca: str,
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Execute full token investigation scan for Solana and EVM."""
    clean_ca = ca.strip()

    # Format validation
    valid_sol = is_valid_solana_ca(clean_ca)
    valid_evm = is_valid_evm_ca(clean_ca)

    if not valid_sol and not valid_evm:
        return {
            "valid": False,
            "ca": clean_ca,
            "error": "Invalid contract address format. Must be a valid Solana (base58, 32-44 chars) or EVM (0x..., 42 chars) address.",
        }

    chain_type = "Solana" if valid_sol else "EVM"

    # 1. Fetch Market Data (DexScreener)
    market_data = await fetch_dexscreener_market_data(clean_ca, client=client)

    raw_chain = (market_data.get("chain_id") or ("solana" if valid_sol else "ethereum")).lower()
    chain_type = market_data.get("chain_name") or CHAIN_DISPLAY_MAP.get(
        raw_chain,
        raw_chain.capitalize() if raw_chain else ("Solana" if valid_sol else "Ethereum"),
    )

    # 2. Fetch Security Data (GoPlus primary, RugCheck fallback for Solana)
    if valid_sol:
        security_data = await fetch_goplus_solana_security(clean_ca, client=client)
        if not security_data.get("success"):
            rugcheck_data = await fetch_rugcheck_fallback(clean_ca, client=client)
            if rugcheck_data.get("success"):
                security_data.update(rugcheck_data)
    else:
        # Multi-chain EVM Security via GoPlus
        goplus_chain_id = GOPLUS_CHAIN_MAP.get(raw_chain, "1")
        security_data = await fetch_goplus_evm_security(clean_ca, chain_id=goplus_chain_id, client=client)

    token_name = market_data.get("name") or "Unknown Token"
    symbol = market_data.get("symbol") or "N/A"

    # 3. Project & Founder OSINT Investigation (Mega-Module 2)
    osint_data: Dict[str, Any] = {
        "has_official_website": False,
        "website": None,
        "twitter": None,
        "telegram": None,
        "discord": None,
        "github": None,
        "founder": "Anonymous / Unverified",
        "is_anonymous_founder": True,
        "evidence_sources": [],
    }
    if market_data.get("found") and token_name != "Unknown Token":
        try:
            osint_data = await investigate_project_osint(
                token_name=token_name,
                symbol=symbol,
                market_info=market_data.get("info"),
                client=client,
            )
        except Exception as exc:
            logger.warning("Project OSINT investigation failed for %s: %s", token_name, exc)

    # 4. Mega-Module 7: Deep Wallet Tracing (CEX Linkage & Outflow Detection)
    creator_addr = security_data.get("creator_address")
    wallet_trace: Dict[str, Any] = {
        "traced": False,
        "wallet_address": creator_addr or "Unknown",
        "funding_source": "Unknown",
        "funding_source_short": "Unknown",
        "funding_entity": "Unknown",
        "is_cex_funded": False,
        "is_fresh_funding_wallet": False,
        "initial_funding_sol": 0.0,
        "first_tx_hash": None,
        "outflow_risk": "UNKNOWN",
        "outflow_details": "No wallet activity traced.",
        "risk_level": "UNKNOWN",
        "risk_reason": "Unable to trace wallet history.",
        "total_tx_count": 0,
    }
    if creator_addr and valid_sol:
        try:
            wallet_trace = await trace_wallet(creator_addr, client=client)
        except Exception as exc:
            logger.warning("Deep wallet trace failed for creator %s: %s", creator_addr, exc)

    # 5. Deterministic Risk Assessment (incorporating OSINT and Wallet Trace flags)
    risk_assessment = evaluate_risk(
        market_data,
        security_data,
        osint=osint_data,
        wallet_trace=wallet_trace,
        chain=chain_type,
    )

    # Holder Concentration intelligence summary
    top_10 = security_data.get("top_10_holders_percent")
    if top_10 is not None:
        if top_10 < 40.0:
            holder_status = "Healthy"
        elif top_10 <= 80.0:
            holder_status = "Concentrated"
        else:
            holder_status = "Critical Danger"
    else:
        holder_status = "Unknown"

    # LP Lock summary
    lp_locked = security_data.get("lp_locked", False)
    lp_status = "Locked (Safe)" if lp_locked else "Unlocked (Risky)"

    # Dev Wallet summary
    dev_pct = security_data.get("dev_wallet_percent", 0.0)
    dev_status = "High risk" if dev_pct > 10.0 else ("Moderate risk" if dev_pct > 5.0 else "Low risk")

    # 6. Mega-Module 4 & 7: Safety Score (0-100) & AI Analyst Summary
    score_data = {
        "security": security_data,
        "lp_intelligence": {"is_locked": lp_locked, "lock_percent": security_data.get("lp_lock_percent", 0.0)},
        "holder_intelligence": {"top_10_percent": top_10, "holder_count": security_data.get("holder_count")},
        "dev_wallet_intelligence": {"holds_percent": dev_pct},
        "wallet_trace": wallet_trace,
    }
    safety_score = calculate_safety_score(score_data)
    ai_summary = await generate_ai_summary(
        {
            "name": token_name,
            "symbol": symbol,
            "chain": chain_type,
            "security": security_data,
            "lp_intelligence": {"is_locked": lp_locked},
            "holder_intelligence": {"top_10_percent": top_10},
            "dev_wallet_intelligence": {"holds_percent": dev_pct},
            "osint": osint_data,
            "wallet_trace": wallet_trace,
        },
        score=safety_score,
    )

    return {
        "valid": True,
        "ca": clean_ca,
        "ca_short": shorten_ca(clean_ca),
        "chain": chain_type,
        "name": token_name,
        "symbol": symbol,
        "market": market_data,
        "security": security_data,
        "holder_intelligence": {
            "top_10_percent": top_10,
            "holder_count": security_data.get("holder_count"),
            "status": holder_status,
        },
        "lp_intelligence": {
            "is_locked": lp_locked,
            "lock_percent": security_data.get("lp_lock_percent", 0.0),
            "status": lp_status,
        },
        "dev_wallet_intelligence": {
            "creator_address": security_data.get("creator_address"),
            "creator_address_short": shorten_ca(security_data.get("creator_address") or ""),
            "holds_percent": dev_pct,
            "status": dev_status,
        },
        "wallet_trace": wallet_trace,
        "osint": osint_data,
        "project_osint": osint_data,
        "risk": risk_assessment,
        "safety_score": safety_score,
        "ai_summary": ai_summary,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def scan_solana_token_sync(ca: str) -> Dict[str, Any]:
    """Synchronous execution wrapper for scan_solana_token."""
    clean_ca = ca.strip()
    valid_sol = is_valid_solana_ca(clean_ca)
    valid_evm = is_valid_evm_ca(clean_ca)

    if not valid_sol and not valid_evm:
        return {
            "valid": False,
            "ca": clean_ca,
            "error": "Invalid contract address format. Must be a valid Solana (base58, 32-44 chars) or EVM (0x..., 42 chars) address.",
        }

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(asyncio.run, scan_solana_token(clean_ca)).result(timeout=25.0)
        else:
            return asyncio.run(scan_solana_token(clean_ca))
    except Exception as exc:
        logger.warning("scan_solana_token_sync encountered error: %s", exc)
        return asyncio.run(scan_solana_token(clean_ca))


# Aliases for scan functions
scan_token = scan_solana_token
scan_token_sync = scan_solana_token_sync


def format_scan_report(report_data: Dict[str, Any]) -> str:
    """Format investigation results into the upgraded Zoe Intelligence Report string."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    risk = report_data.get("risk", {})
    risk_level = risk.get("level", "UNKNOWN")
    reasons = risk.get("reasons", [])

    market = report_data.get("market", {})
    price_val = market.get("price_usd")
    price_str = format_price(price_val)
    mc_val = market.get("market_cap")
    mc_str = format_currency(mc_val)
    liq_val = market.get("liquidity_usd")
    liq_str = format_currency(liq_val)

    security = report_data.get("security", {})
    is_sol = chain.lower() == "solana"
    if is_sol:
        mint_status = "Revoked" if security.get("mint_revoked") is True else ("Active" if security.get("mint_revoked") is False else "Unknown")
        freeze_status = "Revoked" if security.get("freeze_revoked") is True else ("Active" if security.get("freeze_revoked") is False else "Unknown")
        chain_sec_block = (
            f"Mint Auth: {mint_status}\n"
            f"Freeze Auth: {freeze_status}\n"
        )
    else:
        is_open_source = security.get("is_open_source")
        code_status = "Verified (Open Source)" if is_open_source is True else ("Unverified (Closed Source)" if is_open_source is False else "Unknown")
        buy_tax = security.get("buy_tax", 0.0)
        sell_tax = security.get("sell_tax", 0.0)
        is_mint = security.get("is_mintable")
        mint_status = "Active" if is_mint is True else ("Fixed" if is_mint is False else "Unknown")
        chain_sec_block = (
            f"Contract Verified: {code_status}\n"
            f"Taxes: Buy {buy_tax}% / Sell {sell_tax}%\n"
            f"Mintable: {mint_status}\n"
        )

    holder_intel = report_data.get("holder_intelligence", {})
    top_10_pct = holder_intel.get("top_10_percent")
    top_10_str = f"{top_10_pct:.1f}% ({holder_intel.get('status', 'Unknown')})" if top_10_pct is not None else "N/A"

    lp_intel = report_data.get("lp_intelligence", {})
    lp_status_str = lp_intel.get("status", "Unlocked (Risky)")

    dev_intel = report_data.get("dev_wallet_intelligence", {})
    dev_pct_val = dev_intel.get("holds_percent", 0.0)
    dev_str = f"Holds {dev_pct_val:.1f}% ({dev_intel.get('status', 'Low risk')})"

    wallet_trace = report_data.get("wallet_trace") or {}
    funding_entity = wallet_trace.get("funding_entity") or "Unknown"
    trace_risk = wallet_trace.get("risk_level") or "Unknown"
    trace_line = f"🕵️ Wallet Trace: Funded by {funding_entity} (Risk: {trace_risk})\n" if is_sol else ""

    osint = report_data.get("osint") or report_data.get("project_osint") or {}
    website_str = osint.get("website") or "Unknown"
    twitter_str = osint.get("twitter") or "Unknown"
    founder_str = osint.get("founder") or "Anonymous / Unverified"

    timestamp = report_data.get("timestamp_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Format risk reasons
    reasons_block = "\n".join(f"- {r}" for r in reasons[:3]) if reasons else "- No critical risk flags detected"

    score = report_data.get("safety_score", 50)
    ai_summary = report_data.get("ai_summary", "")
    ai_block = f"🛡️ Safety Score: {score}/100\n🤖 AI Analyst: {ai_summary}\n\n" if ai_summary else f"🛡️ Safety Score: {score}/100\n\n"

    report = (
        f"🔍 Zoe Intelligence Report\n"
        f"**{name}** (CA: {ca_short}) · {chain}\n\n"
        f"{ai_block}"
        f"🚨 Risk Assessment: {risk_level}\n"
        f"{reasons_block}\n\n"
        f"📊 Market Data\n"
        f"Price: ${price_str}\n"
        f"Market Cap: ${mc_str}\n"
        f"Liquidity: ${liq_str}\n\n"
        f"🛡️ Security & Holder Intelligence\n"
        f"👥 Holder Concentration: Top 10 hold {top_10_str}\n"
        f"🔒 LP Lock: {lp_status_str}\n"
        f"🧑‍💻 Dev Wallet: {dev_str}\n"
        f"{trace_line}"
        f"{chain_sec_block}\n"
        f"🌐 Project OSINT\n"
        f"Website: {website_str}\n"
        f"Twitter: {twitter_str}\n"
        f"Founder: {founder_str}\n\n"
        f"Evidence Sources: DexScreener, GoPlus\n"
        f"Timestamp: {timestamp}\n"
        f"(This is a preliminary scan, not financial advice.)"
    )
    return report


def format_contract_report(report_data: Dict[str, Any]) -> str:
    """Format Security & Contract checks (Honeypot, Taxes, Mint/Freeze Auth)."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    security = report_data.get("security", {})

    honeypot_status = "🚨 Honeypot Detected!" if security.get("is_honeypot") else "✅ No Honeypot Detected"
    buy_tax = security.get("buy_tax")
    sell_tax = security.get("sell_tax")
    tax_str = f"{buy_tax}% / {sell_tax}%" if (buy_tax is not None and sell_tax is not None) else "0% / 0% (Standard)"

    risk = report_data.get("risk", {})
    risk_level = risk.get("level", "UNKNOWN")

    is_sol = chain.lower() == "solana"
    if is_sol:
        mint_status = "Revoked (Safe)" if security.get("mint_revoked") is True else ("Active (High Risk)" if security.get("mint_revoked") is False else "Unknown")
        freeze_status = "Revoked (Safe)" if security.get("freeze_revoked") is True else ("Active (High Risk)" if security.get("freeze_revoked") is False else "Unknown")
        sec_lines = (
            f"Mint Authority: {mint_status}\n"
            f"Freeze Authority: {freeze_status}\n"
            f"Taxes: {tax_str}"
        )
    else:
        is_open_source = security.get("is_open_source")
        code_status = "Verified (Open Source)" if is_open_source is True else ("Unverified (Closed Source / Risky)" if is_open_source is False else "Unknown")
        is_mint = security.get("is_mintable")
        mint_status = "Active (Inflation Risk)" if is_mint is True else ("Disabled / Fixed Supply" if is_mint is False else "Unknown")
        sec_lines = (
            f"Contract Verified: {code_status}\n"
            f"Buy / Sell Tax: {tax_str}\n"
            f"Mintable: {mint_status}"
        )

    return (
        f"🛡️ **Security & Contract Checks: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"🚨 Risk: {risk_level}\n"
        f"Honeypot: {honeypot_status}\n"
        f"{sec_lines}\n"
        f"Evidence Sources: GoPlus, DexScreener"
    )


def format_holders_report(report_data: Dict[str, Any]) -> str:
    """Format Holder Concentration and Dev Wallet intelligence."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    holder_intel = report_data.get("holder_intelligence", {})
    top_10 = holder_intel.get("top_10_percent")
    top_10_str = f"{top_10:.1f}% ({holder_intel.get('status', 'Unknown')})" if top_10 is not None else "N/A"
    total_holders = holder_intel.get("holder_count")
    total_holders_str = f"{total_holders:,}" if total_holders else "Unknown"

    dev_intel = report_data.get("dev_wallet_intelligence", {})
    dev_pct = dev_intel.get("holds_percent", 0.0)
    dev_str = f"{dev_pct:.1f}% ({dev_intel.get('status', 'Low risk')})"
    creator_addr = dev_intel.get("creator_address_short") or "Not detected"

    wallet_trace = report_data.get("wallet_trace") or {}
    funding_entity = wallet_trace.get("funding_entity") or "Unknown"
    trace_risk = wallet_trace.get("risk_level") or "Unknown"

    return (
        f"👥 **Holder Concentration: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"Top 10 Holders: {top_10_str}\n"
        f"Total Unique Holders: {total_holders_str}\n"
        f"Developer Holding: {dev_str}\n"
        f"Creator Address: `{creator_addr}`\n"
        f"🕵️ Wallet Trace: Funded by {funding_entity} (Risk: {trace_risk})\n"
        f"Evidence Sources: Solana RPC / GoPlus"
    )


def format_liquidity_report(report_data: Dict[str, Any]) -> str:
    """Format Market Data and Liquidity metrics."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    market = report_data.get("market", {})
    price_val = market.get("price_usd")
    price_str = format_price(price_val)
    mc_val = market.get("market_cap")
    mc_str = format_currency(mc_val)
    liq_val = market.get("liquidity_usd")
    liq_str = format_currency(liq_val)

    lp_intel = report_data.get("lp_intelligence", {})
    lp_status_str = lp_intel.get("status", "Unlocked (Risky)")
    lp_pct = lp_intel.get("lock_percent", 0.0)
    lp_pct_str = f" ({lp_pct:.1f}% locked/burned)" if lp_pct > 0 else ""

    return (
        f"📊 **Market & Liquidity: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"Price: ${price_str}\n"
        f"Market Cap: ${mc_str}\n"
        f"Liquidity Pool: ${liq_str}\n"
        f"LP Status: {lp_status_str}{lp_pct_str}\n"
        f"Evidence Sources: DexScreener"
    )


def format_osint_report(report_data: Dict[str, Any]) -> str:
    """Format Project OSINT and Founder Intelligence."""
    if not report_data.get("valid", True):
        return f"❌ **Investigation Error**\n\n{report_data.get('error', 'Invalid contract address.')}"

    name = report_data.get("name") or "Unknown Token"
    ca_short = report_data.get("ca_short") or shorten_ca(report_data.get("ca", ""))
    chain = report_data.get("chain") or "Solana"
    osint = report_data.get("osint") or report_data.get("project_osint") or {}
    website_str = osint.get("website") or "Unknown"
    twitter_str = osint.get("twitter") or "Unknown"
    founder_str = osint.get("founder") or "Unverified"
    sources = osint.get("evidence_sources", [])
    sources_str = ", ".join(sources[:2]) if sources else "DuckDuckGo, DexScreener"

    return (
        f"🌐 **Project OSINT: {name}**\n"
        f"CA: `{ca_short}` · {chain}\n\n"
        f"Website: {website_str}\n"
        f"Twitter: {twitter_str}\n"
        f"Founder: {founder_str}\n"
        f"Evidence Sources: {sources_str}"
    )


def generate_scanner_inline_keyboard(
    ca: str,
    report_data: Optional[Dict[str, Any]] = None,
) -> List[List[Dict[str, str]]]:
    """Generate inline buttons for DexScreener Chart and Blockchain Explorer."""
    clean_ca = ca.strip()
    pair_url = None
    chain = (report_data.get("chain") or "Solana") if report_data else ("Solana" if is_valid_solana_ca(clean_ca) else "Ethereum")
    chain_lower = chain.lower()

    if report_data and isinstance(report_data.get("market"), dict):
        pair_url = report_data["market"].get("pair_url")

    chart_url = pair_url or (f"https://dexscreener.com/solana/{clean_ca}" if chain_lower == "solana" else f"https://dexscreener.com/search?q={clean_ca}")

    if chain_lower == "solana":
        explorer_url = f"https://solscan.io/token/{clean_ca}"
    elif "base" in chain_lower:
        explorer_url = f"https://basescan.org/token/{clean_ca}"
    elif "bsc" in chain_lower or "binance" in chain_lower:
        explorer_url = f"https://bscscan.com/token/{clean_ca}"
    elif "arbitrum" in chain_lower:
        explorer_url = f"https://arbiscan.io/token/{clean_ca}"
    elif "polygon" in chain_lower:
        explorer_url = f"https://polygonscan.com/token/{clean_ca}"
    else:
        explorer_url = f"https://etherscan.io/token/{clean_ca}"

    return [
        [
            {"text": "📊 Live Chart", "url": chart_url},
            {"text": f"🔍 {chain} Explorer", "url": explorer_url},
        ]
    ]

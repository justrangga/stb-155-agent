import os
import sys
import time
import json
import logging
import requests

logger = logging.getLogger(__name__)

class MarketTracker:
    """
    Real-time Market & On-Chain Bonding Curve Tracker for $LARIA.
    Tracks DexScreener pricing, Pump.fun bonding curve progress,
    on-chain buy transactions, and Raydium graduation events.
    """
    def __init__(self, mint_address: str, curve_address: str = None, rpc_url: str = "https://api.mainnet-beta.solana.com", data_dir: str = None):
        self.mint_address = mint_address.strip()
        self.rpc_url = rpc_url.strip()
        
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir

        if not curve_address:
            token_file = os.path.join(data_dir, "launched_token.json")
            if os.path.exists(token_file):
                try:
                    with open(token_file, "r") as f:
                        curve_address = json.load(f).get("bonding_curve")
                except Exception:
                    pass
        self.curve_address = (curve_address or "").strip()
        
        self.state_file = os.path.join(data_dir, "market_state.json")
        self.trades_file = os.path.join(data_dir, "seen_trades.json")
        
        self.seen_signatures = self._load_seen_signatures()
        self.market_state = self._load_market_state()

    def _load_seen_signatures(self) -> set:
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, "r") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_seen_signatures(self):
        try:
            with open(self.trades_file, "w") as f:
                # Keep last 500 signatures
                json.dump(list(self.seen_signatures)[-500:], f)
        except Exception as e:
            logger.error(f"[MarketTracker] Failed to save seen trades: {e}")

    def _load_market_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "market_cap": 3347.0,
            "price_usd": 0.00000335,
            "price_native": 0.000000028,
            "volume_24h": 0.0,
            "curve_sol": 0.0,
            "curve_progress": 0.01,
            "dex_id": "pumpfun",
            "is_graduated": False,
            "last_updated": 0,
            "announced_milestones": []
        }

    def _save_market_state(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.market_state, f, indent=2)
        except Exception as e:
            logger.error(f"[MarketTracker] Failed to save market state: {e}")

    def fetch_market_data(self) -> dict:
        """
        Pulls real-time metrics from DexScreener and on-chain Solana RPC.
        """
        now = time.time()
        
        # 1. DexScreener Price & Volume
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{self.mint_address}"
            res = requests.get(url, timeout=12)
            if res.status_code == 200:
                pairs = res.json().get("pairs") or []
                if pairs:
                    p = pairs[0]
                    self.market_state["market_cap"] = float(p.get("marketCap", self.market_state["market_cap"]))
                    self.market_state["price_usd"] = float(p.get("priceUsd", self.market_state["price_usd"]))
                    self.market_state["price_native"] = float(p.get("priceNative", self.market_state["price_native"]))
                    self.market_state["volume_24h"] = float(p.get("volume", {}).get("h24", 0))
                    self.market_state["dex_id"] = p.get("dexId", "pumpfun")
                    if p.get("dexId") == "raydium":
                        self.market_state["is_graduated"] = True
                        self.market_state["curve_progress"] = 100.0
        except Exception as e:
            logger.warning(f"[MarketTracker] DexScreener fetch warning: {e}")

        # 2. On-Chain Bonding Curve SOL Balance (Pump.fun target: ~85 SOL)
        if not self.market_state["is_graduated"]:
            try:
                rpc_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [self.curve_address]
                }
                r = requests.post(self.rpc_url, json=rpc_payload, timeout=10)
                if r.status_code == 200:
                    lamports = r.json().get("result", {}).get("value", 0)
                    curve_sol = lamports / 1e9
                    self.market_state["curve_sol"] = curve_sol
                    # Progress relative to ~85 SOL graduation target
                    progress = min(100.0, (curve_sol / 85.0) * 100.0)
                    self.market_state["curve_progress"] = max(0.01, round(progress, 2))
                    if curve_sol >= 84.0:
                        self.market_state["is_graduated"] = True
                        self.market_state["curve_progress"] = 100.0
            except Exception as e:
                logger.warning(f"[MarketTracker] Curve RPC balance fetch warning: {e}")

        self.market_state["last_updated"] = now
        self._save_market_state()
        return self.market_state

    def check_new_buys(self, min_sol_threshold: float = 0.01) -> list:
        """
        Polls recent signatures on the bonding curve account.
        Detects newly confirmed BUY transactions.
        Returns a list of buy events: [{"signature": "...", "sol_amount": float, "buyer": "..."}]
        """
        new_buys = []
        try:
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [self.curve_address, {"limit": 10}]
            }
            r = requests.post(self.rpc_url, json=rpc_payload, timeout=12)
            if r.status_code != 200:
                return []
            
            sigs_data = r.json().get("result", [])
            for item in sigs_data:
                sig = item.get("signature")
                if not sig or item.get("err") is not None:
                    continue
                
                if sig in self.seen_signatures:
                    continue
                
                # Fetch transaction details
                tx_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                }
                tx_res = requests.post(self.rpc_url, json=tx_payload, timeout=10)
                if tx_res.status_code == 200:
                    tx_data = tx_res.json().get("result", {})
                    if not tx_data:
                        continue
                    
                    meta = tx_data.get("meta", {})
                    pre_bal = meta.get("preBalances", [])
                    post_bal = meta.get("postBalances", [])
                    keys = tx_data.get("transaction", {}).get("message", {}).get("accountKeys", [])
                    
                    # Detect net change on curve account
                    for idx, acc in enumerate(keys):
                        pub = acc.get("pubkey") if isinstance(acc, dict) else str(acc)
                        if pub == self.curve_address:
                            diff_sol = (post_bal[idx] - pre_bal[idx]) / 1e9
                            if diff_sol >= min_sol_threshold:
                                # It's a verified BUY!
                                buyer = keys[0].get("pubkey") if isinstance(keys[0], dict) else str(keys[0])
                                new_buys.append({
                                    "signature": sig,
                                    "sol_amount": diff_sol,
                                    "buyer": buyer,
                                    "block_time": item.get("blockTime")
                                })
                            break
                
                self.seen_signatures.add(sig)

            if new_buys:
                self._save_seen_signatures()

        except Exception as e:
            logger.warning(f"[MarketTracker] Error checking curve trades: {e}")

        return new_buys

    def check_milestones(self) -> list:
        """
        Checks if a market cap or bonding curve milestone was crossed.
        Returns a list of milestone descriptions to announce.
        """
        announced = set(self.market_state.get("announced_milestones", []))
        new_milestones = []
        
        mcap = self.market_state.get("market_cap", 0)
        curve_pct = self.market_state.get("curve_progress", 0)
        
        # MCAP Milestones
        mcap_thresholds = [10000, 25000, 50000, 100000, 250000, 500000, 1000000]
        for t in mcap_thresholds:
            tag = f"mcap_{t}"
            if mcap >= t and tag not in announced:
                announced.add(tag)
                new_milestones.append({
                    "type": "market_cap",
                    "value": t,
                    "desc": f"Crossed ${t:,.0f} Market Cap"
                })

        # Curve Milestones
        curve_thresholds = [25.0, 50.0, 75.0, 90.0, 100.0]
        for c in curve_thresholds:
            tag = f"curve_{int(c)}"
            if curve_pct >= c and tag not in announced:
                announced.add(tag)
                new_milestones.append({
                    "type": "bonding_curve",
                    "value": c,
                    "desc": f"Bonding Curve reached {c:.0f}%"
                })

        # Graduation Event
        if self.market_state.get("is_graduated") and "graduation" not in announced:
            announced.add("graduation")
            new_milestones.append({
                "type": "graduation",
                "value": 100.0,
                "desc": "Bonding curve 100% completed! Migrated to Raydium DEX!"
            })

        if new_milestones:
            self.market_state["announced_milestones"] = list(announced)
            self._save_market_state()

        return new_milestones

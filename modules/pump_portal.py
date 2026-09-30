import os
import time
import base64
import logging
import requests
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

logger = logging.getLogger(__name__)

class PumpPortalLauncher:
    """
    Programmatic Pump.fun Launcher via PumpPortal API (https://pumpportal.fun)
    Supports token creation and initial buys directly on Solana.
    """
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.portal_url = "https://pumpportal.fun/api/trade-local"

    def deploy_token(
        self,
        signer_keypair: Keypair,
        name: str,
        symbol: str,
        description: str,
        initial_buy_sol: float = 0.0,
        twitter_url: str = "https://x.com/0xLariaa",
        telegram_url: str = "",
        website_url: str = "https://github.com/justrangga/stb-155-agent"
    ) -> dict:
        """
        Deploy token on Pump.fun and optionally execute an initial dev buy.
        Requires ~0.025 - 0.03 SOL minimum balance in signer wallet for Solana rent fees.
        """
        token_mint = Keypair()
        mint_pubkey = str(token_mint.pubkey())
        signer_pubkey = str(signer_keypair.pubkey())
        logger.info(f"[PumpPortal] Generating new token mint: {mint_pubkey}")

        token_metadata = {
            "name": name,
            "symbol": symbol,
            "description": description,
            "twitter": twitter_url,
            "telegram": telegram_url,
            "website": website_url
        }

        payload = {
            "publicKey": signer_pubkey,
            "action": "create",
            "tokenMetadata": token_metadata,
            "mint": mint_pubkey,
            "denominatedInSol": "true",
            "amount": initial_buy_sol,
            "slippage": 10,
            "priorityFee": 0.0005,
            "pool": "pump"
        }

        try:
            logger.info("[PumpPortal] Requesting transaction payload from PumpPortal API...")
            resp = requests.post(self.portal_url, json=payload, timeout=30)
            if resp.status_code != 200:
                err_msg = f"PumpPortal API error ({resp.status_code}): {resp.text}"
                logger.error(f"[PumpPortal] {err_msg}")
                return {"success": False, "error": err_msg}

            # Transaction binary bytes returned by PumpPortal
            tx_bytes = resp.content
            tx = VersionedTransaction.from_bytes(tx_bytes)

            # Sign with creator wallet and token mint keypair
            signed_tx = VersionedTransaction(tx.message, [signer_keypair, token_mint])
            tx_base64 = base64.b64encode(bytes(signed_tx)).decode("utf-8")

            # Broadcast to Solana RPC
            logger.info("[PumpPortal] Broadcasting signed transaction to Solana...")
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendTransaction",
                "params": [
                    tx_base64,
                    {"encoding": "base64", "skipPreflight": False, "preflightCommitment": "confirmed"}
                ]
            }

            rpc_resp = requests.post(self.rpc_url, json=rpc_payload, timeout=25)
            rpc_data = rpc_resp.json()

            if "error" in rpc_data:
                err = rpc_data["error"]
                logger.error(f"[PumpPortal] Solana RPC rejected transaction: {err}")
                return {"success": False, "error": f"Solana RPC Error: {err}"}

            tx_sig = rpc_data.get("result")
            logger.info(f"[PumpPortal] Transaction confirmed! Signature: {tx_sig}")

            pump_url = f"https://pump.fun/{mint_pubkey}"
            solscan_url = f"https://solscan.io/tx/{tx_sig}"

            return {
                "success": True,
                "mint_address": mint_pubkey,
                "name": name,
                "symbol": symbol,
                "tx_signature": tx_sig,
                "pump_url": pump_url,
                "solscan_url": solscan_url
            }

        except Exception as e:
            logger.error(f"[PumpPortal] Unexpected deployment error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

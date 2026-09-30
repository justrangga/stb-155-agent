import os
import io
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
        self.ipfs_url = "https://pump.fun/api/ipfs"

    def upload_metadata_to_ipfs(
        self,
        name: str,
        symbol: str,
        description: str,
        image_path: str = None,
        image_bytes: bytes = None,
        twitter_url: str = "https://x.com/0xLariaa",
        telegram_url: str = "",
        website_url: str = "https://github.com/justrangga/stb-155-agent"
    ) -> str:
        """
        Uploads token metadata and image to Pump.fun IPFS gateway.
        Returns the metadataUri (e.g. https://ipfs.io/ipfs/bafkrei...)
        """
        data = {
            "name": name,
            "symbol": symbol,
            "description": description,
            "twitter": twitter_url,
            "telegram": telegram_url,
            "website": website_url,
            "showName": "true"
        }

        if image_bytes:
            file_obj = io.BytesIO(image_bytes)
            files = {"file": ("avatar.png", file_obj, "image/png")}
        elif image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            files = {"file": (os.path.basename(image_path), io.BytesIO(image_bytes), "image/png")}
        else:
            # Minimal 1x1 transparent png if no image provided
            tiny_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            files = {"file": ("avatar.png", io.BytesIO(tiny_png), "image/png")}

        headers = {"User-Agent": "Mozilla/5.0"}
        logger.info("[PumpPortal] Uploading token metadata and avatar to Pump.fun IPFS...")
        resp = requests.post(self.ipfs_url, data=data, files=files, headers=headers, timeout=25)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to upload to IPFS: {resp.status_code} {resp.text}")

        res_json = resp.json()
        metadata_uri = res_json.get("metadataUri")
        if not metadata_uri:
            raise RuntimeError(f"No metadataUri in IPFS response: {res_json}")

        logger.info(f"[PumpPortal] IPFS upload success! URI: {metadata_uri}")
        return metadata_uri

    def deploy_token(
        self,
        signer_keypair: Keypair,
        name: str,
        symbol: str,
        description: str,
        image_path: str = None,
        image_bytes: bytes = None,
        initial_buy_sol: float = 0.0,
        twitter_url: str = "https://x.com/0xLariaa",
        telegram_url: str = "",
        website_url: str = "https://github.com/justrangga/stb-155-agent"
    ) -> dict:
        """
        Deploy token on Pump.fun and optionally execute an initial buy.
        Requires ~0.025 - 0.03 SOL minimum balance in signer wallet.
        """
        token_mint = Keypair()
        mint_pubkey = str(token_mint.pubkey())
        signer_pubkey = str(signer_keypair.pubkey())
        logger.info(f"[PumpPortal] Generating new token mint: {mint_pubkey}")

        try:
            # 1. Upload metadata to IPFS
            metadata_uri = self.upload_metadata_to_ipfs(
                name=name,
                symbol=symbol,
                description=description,
                image_path=image_path,
                image_bytes=image_bytes,
                twitter_url=twitter_url,
                telegram_url=telegram_url,
                website_url=website_url
            )

            # 2. Build Create Transaction via PumpPortal API
            payload = {
                "publicKey": signer_pubkey,
                "action": "create",
                "tokenMetadata": {
                    "name": name,
                    "symbol": symbol,
                    "uri": metadata_uri
                },
                "mint": mint_pubkey,
                "denominatedInSol": "true",
                "amount": initial_buy_sol,
                "slippage": 10,
                "priorityFee": 0.0005,
                "pool": "pump"
            }

            logger.info("[PumpPortal] Requesting create transaction from PumpPortal...")
            resp = requests.post(self.portal_url, json=payload, timeout=30)
            if resp.status_code != 200:
                err_msg = f"PumpPortal API error ({resp.status_code}): {resp.text}"
                logger.error(f"[PumpPortal] {err_msg}")
                return {"success": False, "error": err_msg}

            # 3. Sign transaction (token_mint first, signer second)
            tx_bytes = resp.content
            tx = VersionedTransaction.from_bytes(tx_bytes)
            signed_tx = VersionedTransaction(tx.message, [token_mint, signer_keypair])
            tx_base64 = base64.b64encode(bytes(signed_tx)).decode("utf-8")

            # 4. Broadcast to Solana RPC
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
            logger.info(f"[PumpPortal] Transaction broadcasted! Signature: {tx_sig}")

            pump_url = f"https://pump.fun/{mint_pubkey}"
            solscan_url = f"https://solscan.io/tx/{tx_sig}"

            return {
                "success": True,
                "mint_address": mint_pubkey,
                "name": name,
                "symbol": symbol,
                "metadata_uri": metadata_uri,
                "tx_signature": tx_sig,
                "pump_url": pump_url,
                "solscan_url": solscan_url
            }

        except Exception as e:
            logger.error(f"[PumpPortal] Unexpected deployment error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

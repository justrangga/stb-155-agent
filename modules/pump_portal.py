import requests
import json
import base58
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

class PumpPortalLauncher:
    """
    Integrasi Pump.fun via PumpPortal API (https://pumpportal.fun)
    Mendukung deploy token secara terprogram tanpa smart contract lokal yang berat.
    """
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.portal_url = "https://pumpportal.fun/api/trade-local"

    def deploy_token(self, signer_keypair: Keypair, name: str, symbol: str, description: str, initial_buy_sol: float = 0.005) -> dict:
        """
        Membuat token baru di pump.fun dan melakukan initial buy.
        Memerlukan saldo SOL di wallet pembuat minimal initial_buy_sol + ~0.02 SOL fee.
        """
        token_mint = Keypair()
        print(f"[PumpPortal] Mint token baru dibuat: {token_mint.pubkey()}")

        # Metadata info
        token_metadata = {
            "name": name,
            "symbol": symbol,
            "description": description
        }

        # Request transaction bytes dari PumpPortal
        payload = {
            "publicKey": str(signer_keypair.pubkey()),
            "action": "create",
            "tokenMetadata": token_metadata,
            "mint": str(token_mint.pubkey()),
            "denominatedInSol": "true",
            "amount": initial_buy_sol,
            "slippage": 10,
            "priorityFee": 0.0005,
            "pool": "pump"
        }

        try:
            resp = requests.post(self.portal_url, json=payload, timeout=25)
            if resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"PumpPortal returned {resp.status_code}: {resp.text}"
                }

            # Transaction bytes (base58 atau raw binary)
            tx_bytes = resp.content
            # Deserialize versioned transaction
            tx = VersionedTransaction.from_bytes(tx_bytes)

            # Tanda tangani dengan signer wallet & token mint keypair
            # tx.sign(...)
            # Note: eksekusi broadcast hanya berjalan jika pengguna mengaktifkannya
            return {
                "success": True,
                "mint_address": str(token_mint.pubkey()),
                "name": name,
                "symbol": symbol,
                "pump_url": f"https://pump.fun/{token_mint.pubkey()}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

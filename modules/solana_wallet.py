import os
import json
import base58
import requests
from solders.keypair import Keypair

class SolanaWallet:
    def __init__(self, private_key_str: str = None, rpc_url: str = "https://api.mainnet-beta.solana.com", key_file_path: str = None):
        self.rpc_url = rpc_url
        self.key_file_path = key_file_path or os.getenv("WALLET_KEY_FILE", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "agent_wallet.json"))

        if private_key_str and private_key_str.strip():
            self.keypair = self._load_keypair(private_key_str.strip())
        elif os.path.exists(self.key_file_path):
            try:
                with open(self.key_file_path, "r") as f:
                    data = json.load(f)
                    self.keypair = self._load_keypair(data["private_key"])
                    print(f"[SolanaWallet] Memuat wallet tersimpan dari {self.key_file_path}")
            except Exception as e:
                print(f"[SolanaWallet] Gagal membaca {self.key_file_path}: {e}, membuat keypair baru...")
                self.keypair = self._generate_and_save()
        else:
            self.keypair = self._generate_and_save()

        self.pubkey_str = str(self.keypair.pubkey())

    def _generate_and_save(self) -> Keypair:
        kp = Keypair()
        os.makedirs(os.path.dirname(self.key_file_path), exist_ok=True)
        b58_key = base58.b58encode(bytes(kp)).decode("utf-8")
        with open(self.key_file_path, "w") as f:
            json.dump({
                "public_key": str(kp.pubkey()),
                "private_key": b58_key
            }, f, indent=2)
        print(f"[SolanaWallet] Keypair baru dibuat dan disimpan ke {self.key_file_path}")
        return kp

    def _load_keypair(self, key_str: str) -> Keypair:
        if key_str.startswith("["):
            data = json.loads(key_str)
            return Keypair.from_bytes(bytes(data))
        else:
            raw_bytes = base58.b58decode(key_str)
            return Keypair.from_bytes(raw_bytes)

    def get_balance(self) -> float:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [self.pubkey_str]
        }
        try:
            resp = requests.post(self.rpc_url, json=payload, timeout=10)
            data = resp.json()
            lamports = data.get("result", {}).get("value", 0)
            return lamports / 1e9
        except Exception as e:
            print(f"[SolanaWallet] Error mengambil saldo: {e}")
            return 0.0

    def get_address(self) -> str:
        return self.pubkey_str

    def export_private_key_base58(self) -> str:
        return base58.b58encode(bytes(self.keypair)).decode("utf-8")

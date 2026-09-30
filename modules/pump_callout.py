#!/usr/bin/env python3
"""
Pump.fun Callout Publisher for Laria (STB-155 Agent)
Signs in via non-custodial wallet keypair, checks eligibility, and posts official thesis callouts.
"""

import os
import time
import base58
import logging
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv("/root/stb-agent/.env")

from modules.solana_wallet import SolanaWallet

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class PumpFunCallout:
    def __init__(self):
        self.wallet = SolanaWallet()
        self.pubkey = str(self.wallet.keypair.pubkey())
        self.api_base = "https://frontend-api-v3.pump.fun"
        self.session_token = None

    def login(self) -> str:
        timestamp = int(time.time() * 1000)
        message = f"Sign in to pump.fun: {timestamp}"
        sig_bytes = self.wallet.keypair.sign_message(message.encode("utf-8"))
        signature = base58.b58encode(bytes(sig_bytes)).decode("utf-8")

        payload = {
            "address": self.pubkey,
            "timestamp": timestamp,
            "signature": signature,
            "authType": "non_custodial"
        }
        headers = {
            "Origin": "https://pump.fun",
            "Referer": "https://pump.fun/",
            "Content-Type": "application/json"
        }
        res = requests.post(f"{self.api_base}/auth/login/token", json=payload, headers=headers, impersonate="chrome124")
        if res.status_code == 200:
            self.session_token = res.json().get("access_token")
            logger.info("Pump.fun login successful. Token acquired.")
            return self.session_token
        raise RuntimeError(f"Login failed ({res.status_code}): {res.text}")

    def check_eligibility(self, coin_mint: str) -> dict:
        if not self.session_token:
            self.login()
        headers = {
            "Origin": "https://pump.fun",
            "Referer": f"https://pump.fun/coin/{coin_mint}",
            "Authorization": f"Bearer {self.session_token}"
        }
        cookies = {"auth_token": self.session_token}
        res = requests.get(f"{self.api_base}/callout/eligibility/{coin_mint}", headers=headers, cookies=cookies, impersonate="chrome124")
        return res.json()

    def post_callout(self, coin_mint: str, thesis: str) -> dict:
        if not self.session_token:
            self.login()
        headers = {
            "Origin": "https://pump.fun",
            "Referer": f"https://pump.fun/coin/{coin_mint}",
            "Authorization": f"Bearer {self.session_token}",
            "Content-Type": "application/json"
        }
        cookies = {"auth_token": self.session_token}
        payload = {
            "coinMint": coin_mint,
            "thesis": thesis,
            "version": 1
        }
        res = requests.post(f"{self.api_base}/callout/create", json=payload, headers=headers, cookies=cookies, impersonate="chrome124")
        if res.status_code in [200, 201]:
            logger.info(f"Callout successfully created: {res.json()}")
            return res.json()
        raise RuntimeError(f"Failed to post callout ({res.status_code}): {res.text}")

if __name__ == "__main__":
    client = PumpFunCallout()
    mint = "CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq"
    elig = client.check_eligibility(mint)
    print("Eligibility status:", elig.get("preflight", {}).get("create", {}).get("verdict"))

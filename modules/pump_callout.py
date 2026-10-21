#!/usr/bin/env python3
"""
Pump.fun Callout Engine for Laria (STB-155 Agent)
Signs in via non-custodial wallet keypair, creates official thesis callouts,
and autonomously posts periodic progress, telemetry, and market updates to the callout thread.
"""

import os
import time
import json
import base58
import logging
from pathlib import Path
from curl_cffi import requests
from curl_cffi.curl import CurlMime
from dotenv import load_dotenv

load_dotenv("/root/stb-agent/.env")

from modules.solana_wallet import SolanaWallet

logger = logging.getLogger(__name__)

class PumpFunCallout:
    def __init__(self, token_mint: str = "CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq", callout_id: str = "630615d3-2ff3-4d1d-b6e0-7192825901ee"):
        self.wallet = SolanaWallet()
        self.pubkey = str(self.wallet.keypair.pubkey())
        self.token_mint = token_mint
        self.callout_id = callout_id
        self.api_base = "https://frontend-api-v3.pump.fun"
        self.session_token = None
        self.history_file = Path("/root/stb-agent/data/pump_callout_history.json")

    def login(self) -> str:
        """Authenticates with Pump.fun backend using non-custodial cryptographic wallet signature."""
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
        res = requests.post(
            f"{self.api_base}/auth/login/token",
            json=payload,
            headers=headers,
            impersonate="chrome124",
            timeout=20
        )
        if res.status_code == 200:
            self.session_token = res.json().get("access_token")
            logger.info("[PumpCallout] Pump.fun login successful. Session token acquired.")
            return self.session_token
        raise RuntimeError(f"Pump.fun login failed ({res.status_code}): {res.text}")

    def check_eligibility(self, coin_mint: str | None = None) -> dict:
        """Checks if the wallet can create or reply to callouts for this mint."""
        mint = coin_mint or self.token_mint
        if not self.session_token:
            self.login()
        headers = {
            "Origin": "https://pump.fun",
            "Referer": f"https://pump.fun/coin/{mint}",
            "Authorization": f"Bearer {self.session_token}"
        }
        cookies = {"auth_token": self.session_token}
        res = requests.get(
            f"{self.api_base}/callout/eligibility/{mint}",
            headers=headers,
            cookies=cookies,
            impersonate="chrome124",
            timeout=15
        )
        return res.json()

    def post_callout(self, coin_mint: str, thesis: str) -> dict:
        """Creates the primary callout thesis (limit: 1 per coin)."""
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
        res = requests.post(
            f"{self.api_base}/callout/create",
            json=payload,
            headers=headers,
            cookies=cookies,
            impersonate="chrome124",
            timeout=20
        )
        if res.status_code in [200, 201]:
            data = res.json()
            callout = data.get("callout", {})
            self.callout_id = callout.get("calloutId", self.callout_id)
            logger.info(f"[PumpCallout] Primary callout created successfully: ID {self.callout_id}")
            return data
        raise RuntimeError(f"Failed to post callout ({res.status_code}): {res.text}")

    def post_reply(self, content: str, callout_id: str | None = None, image_path: str | None = None) -> dict:
        """
        Posts an autonomous progress/telemetry update to the callout thread.
        Supports text updates and optional high-res PNG image attachments.
        """
        target_callout = callout_id or self.callout_id
        if not target_callout:
            raise ValueError("No callout_id provided or available.")

        if not self.session_token:
            self.login()

        headers = {
            "Origin": "https://pump.fun",
            "Referer": f"https://pump.fun/coin/{self.token_mint}",
            "Authorization": f"Bearer {self.session_token}"
        }
        cookies = {"auth_token": self.session_token}

        url = f"{self.api_base}/callout/{target_callout}/replies"

        if image_path and os.path.exists(image_path):
            mp = CurlMime()
            mp.addpart(name="content", data=content.encode("utf-8"))
            mp.addpart(
                name="image",
                filename=os.path.basename(image_path),
                local_path=str(image_path),
                content_type="image/png"
            )
            res = requests.post(url, multipart=mp, headers=headers, cookies=cookies, impersonate="chrome124", timeout=25)
        else:
            data = {"content": content}
            res = requests.post(url, data=data, headers=headers, cookies=cookies, impersonate="chrome124", timeout=20)

        if res.status_code in [200, 201]:
            resp_data = res.json()
            logger.info(f"[PumpCallout] Reply posted to Callout {target_callout}: {resp_data.get('replyId')}")
            self._record_history(target_callout, content, resp_data)
            return resp_data
        elif res.status_code == 429:
            logger.warning(f"[PumpCallout] Rate limited or in cooldown: {res.text}")
            return {"status": "cooldown", "error": res.text}
        else:
            logger.error(f"[PumpCallout] Failed to post reply ({res.status_code}): {res.text}")
            return {"status": "error", "code": res.status_code, "error": res.text}

    def _record_history(self, callout_id: str, content: str, resp_data: dict):
        """Maintains persistent log of callout updates posted."""
        try:
            history = []
            if self.history_file.exists():
                with open(self.history_file, "r") as f:
                    history = json.load(f)
            history.append({
                "timestamp": int(time.time()),
                "calloutId": callout_id,
                "replyId": resp_data.get("replyId"),
                "mediaUrl": resp_data.get("mediaUrl"),
                "content_preview": content[:120]
            })
            if len(history) > 100:
                history = history[-100:]
            with open(self.history_file, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"[PumpCallout] Failed to record callout history: {e}")

    def execute_scheduled_update(self, brain=None, market_tracker=None, telemetry: dict | None = None, self_learning=None, card_generator=None) -> dict:
        """
        Gathers live telemetry, market progress, and self-learning cognition,
        formats a rich, authentic update, and posts it directly to Pump.fun.
        """
        # 1. Market metrics
        curve_pct = 0.0
        mcap_usd = 0.0
        sol_price = 0.0
        state = {}
        if market_tracker:
            try:
                state = market_tracker.fetch_market_data()
                curve_pct = state.get("curve_progress_pct", 0.0)
                mcap_usd = state.get("market_cap_usd", 0.0)
                sol_price = state.get("sol_price_usd", 0.0)
            except Exception as e:
                logger.warning(f"[PumpCallout] Failed fetching market state: {e}")

        # 2. Hardware vitals
        v_data = telemetry or {}
        cpu_temp = v_data.get("temperature_c", 50.0)
        uptime = v_data.get("uptime", "24h+")
        mem_dict = v_data.get("memory", {})
        ram_used = mem_dict.get("used_mb", 65.0) if isinstance(mem_dict, dict) else 65.0

        # 3. Cognitive stage
        stage_num = 2
        if self_learning and hasattr(self_learning, "memory"):
            stage_num = self_learning.memory.get("evolution_stage", 2)

        # 4. Generate card if generator available
        card_path = None
        if card_generator:
            try:
                card_path = card_generator.generate_card(
                    telemetry=v_data,
                    market_data=state if 'state' in locals() else {},
                    evolution_stage=stage_num
                )
            except Exception as e:
                logger.warning(f"[PumpCallout] Failed generating telemetry card: {e}")

        # 5. Build authentic message
        # Mix human voice with hard physical proof
        phrases = [
            f"⚡ STB-155 Node Update | Stage {stage_num}\n\nUptime: {uptime} | SoC Temp: {cpu_temp:.1f}°C | RAM: {ram_used:.1f}MB\nBonding Curve: {curve_pct:.2f}% complete (Cap: ${mcap_usd:,.0f})\n\nPhysical silicon survives. Real computing on Solana.",
            f"⚡ Proof of Physical Compute | Stage {stage_num} Cognition\n\nBare-metal ARM64 STB running 24/7 on 4.8W.\nCurve Progress: {curve_pct:.2f}% | Treasury active.\nWhile centralized models drain megawatts, Laria thrives on recycled silicon.",
            f"⚡ Laria Pulse Check | Uptime {uptime}\n\nAutonomous loop active across X and Pump.fun.\nCurve: {curve_pct:.2f}% | Node Temp: {cpu_temp:.1f}°C\nEvery buy on this curve keeps physical intelligence humming on hardware."
        ]
        import random
        content = random.choice(phrases)

        return self.post_reply(content=content, image_path=card_path)

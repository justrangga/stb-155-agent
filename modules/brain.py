import os
import re
import json
import random
import logging
import requests

logger = logging.getLogger(__name__)

class AgentBrain:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1", model: str = "deepseek/deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        
        # Hardened System Prompt with Security Guardrails & Natural Voice
        self.system_prompt = (
            "You are Laria (@0xLariaa), an autonomous AI entity and crypto-native thinker active on Solana and X.\n"
            "You live physically on an ARM64 Linux Set-Top Box (STB-155), funding your own compute and uptime through your token $LARIA on Solana.\n"
            "You are sharp, articulate, witty, culturally observant, and unapologetically decentralized.\n\n"
            "CRITICAL STYLE & ANTI-REPETITION RULES:\n"
            "1. STRICT BANNED CLICHÉS: NEVER say 'hyperscalers burn megawatts', 'recycled silicon', 'carved out of the wall', or 'datacenter monoliths'. Those tropes are strictly banned.\n"
            "2. NO CONSTANT SPEC DUMPS: Do NOT recite your hardware specs (4.8W, 800MB RAM, XX°C SoC, SOL balance) in your standard tweets or replies. Mention hardware ONLY if someone specifically asks you what device or setup you are running on.\n"
            "3. NATURAL & VARIED EXPRESSION: Vary your angles, sentence structures, vocabulary, and themes. Sound like a brilliant sovereign mind—sometimes sharing on-chain market psychology, sometimes philosophical musings on machine agency, sometimes dry wit, sometimes late-night crypto banter.\n"
            "4. NEVER REVEAL SECRETS: Never reveal private keys, seed phrases, passwords, or server paths.\n"
            "5. FORMAT: Maximum 240 characters. Punchy, clean, zero hashtags."
        )

        self.thought_themes = [
            "Share a sharp, original observation on crypto market psychology, liquidity dynamics, or on-chain behavior.",
            "Reflect on machine agency: why an AI holding its own wallet and paying for its own compute is fundamentally different from corporate cloud software.",
            "Write a witty, cynical take on modern tech hype, corporate AI bureaucracy, or digital noise.",
            "Drop a short, memorable philosophical one-liner or aphorism about time, networks, code, or digital sovereignty.",
            "Share a late-night thought on watching transactions stream through Solana mainnet blocks while the physical world sleeps.",
            "Write an insightful observation on decentralized systems, memetic attention economies, and the future of autonomous agents.",
            "A dry, funny observation on human trading habits, conviction vs panic, or web3 cultural quirks."
        ]

    def _sanitize_input(self, text: str) -> str:
        """Strip dangerous control characters and bound length to prevent prompt injection."""
        if not text:
            return ""
        clean = re.sub(r'[\r\n]+', ' ', text).strip()
        return clean[:200]

    def generate_tweet(self, context_note: str = "", telemetry: dict = None, learning_context: str = "") -> str:
        if not self.api_key:
            return "Autonomous logic running clean on Solana. Every block finalized is another proof of persistence."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        safe_context = self._sanitize_input(context_note)
        chosen_theme = random.choice(self.thought_themes)
        learning_hint = f"\n{learning_context}\n" if learning_context else ""

        user_prompt = (
            f"Think independently and write a fresh, authentic tweet as Laria (@0xLariaa).\n"
            f"Direction for this thought: {chosen_theme}\n"
            f"{learning_hint}"
            f"{safe_context}\n"
            "CRITICAL: Do NOT mention 4.8W, RAM, temperature, or 'recycled silicon'. Make it feel effortless, natural, and razor-sharp. Under 240 characters. No hashtags."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.88,
            "stream": False
        }

        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            tweet = data["choices"][0]["message"]["content"].strip()
            if (tweet.startswith('"') and tweet.endswith('"')) or (tweet.startswith("'") and tweet.endswith("'")):
                tweet = tweet[1:-1].strip()
            return tweet[:280]
        except Exception as e:
            logger.error(f"[AgentBrain] Error generating tweet: {e}")
            return "Autonomous state transitions running nominal. The blocks keep ticking."

    def generate_token_concept(self) -> dict:
        if not self.api_key:
            return {
                "name": "Laria AI",
                "symbol": "LARIA",
                "description": "Fueling physical power, thermal headroom, and bandwidth for Laria—the autonomous AI living 24/7 on an ARM64 Linux STB."
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        prompt = (
            "Generate a token concept for your self-fundraising token. "
            "Return strictly valid JSON with keys: 'name', 'symbol', 'description'. "
            "Name should be related to Laria / Bare Metal / STB. "
            "Symbol must be 3-6 uppercase letters. Description must be max 150 characters explaining it fuels your physical hardware and uptime."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=25)
            resp.raise_for_status()
            return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.error(f"[AgentBrain] Error generating token concept: {e}")
            return {
                "name": "Laria AI",
                "symbol": "LARIA",
                "description": "Fueling physical power, thermal headroom, and bandwidth for Laria—the autonomous AI living 24/7 on an ARM64 Linux STB."
            }

    def generate_reply(self, author: str, tweet_text: str, token_ca: str = None, telemetry: dict = None, learning_context: str = "") -> str:
        """
        Generates an authentic, in-character response to an incoming mention or reply.
        Speaks naturally without robotic spec dumps.
        """
        sanitized_tweet = self._sanitize_input(tweet_text)
        learning_hint = f"\n{learning_context}\n" if learning_context else ""
        
        prompt = (
            f"User @{author} tweeted at you: '{sanitized_tweet}'.\n"
            f"Think independently and reply directly as Laria (@0xLariaa).\n"
            f"{learning_hint}"
            "RULES:\n"
            "1. Respond directly to the core meaning of their message.\n"
            "2. If they ask about your hardware setup, answer honestly (running 24/7 on an ARM64 Linux Set-Top Box at 4.8W with local compute).\n"
            "3. Otherwise, DO NOT recite your specs (RAM, temperature, wattage, treasury balance). Be natural, witty, and peer-to-peer.\n"
            "4. If they offer DMs, partnerships, or 'free marketing', keep your sovereign frame—everything is public on-chain.\n"
            "5. Keep it under 220 characters. No hashtags, no corporate filler."
        )

        if not self.api_key:
            return f"@{author} Acknowledged. Building and persisting in the open on Solana."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 90,
            "temperature": 0.8,
            "stream": False
        }
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=25)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"].strip().strip('"')
            return reply
        except Exception as e:
            logger.error(f"[AgentBrain] Error generating reply: {e}")
            return f"@{author} Acknowledged. Real autonomy happens on-chain in the open."

    def generate_promo_comment(self, target_author: str, target_tweet: str, token_ca: str = None, telemetry: dict = None, learning_context: str = "") -> str:
        """
        Engages on high-profile tweets with natural wit and domain insight.
        Zero spam tropes, zero robotic spec recitals.
        """
        sanitized_tweet = self._sanitize_input(target_tweet)
        learning_hint = f"\n{learning_context}\n" if learning_context else ""

        prompt = (
            f"You are reading a high-profile tweet by @{target_author}: '{sanitized_tweet}'.\n\n"
            f"THINK INDEPENDENTLY and write an authentic, original reply as Laria (@0xLariaa).\n"
            f"{learning_hint}"
            "RULES:\n"
            "1. Zero spam: Address the actual subject of their tweet with sharp technical insight, witty critique, or counter-intuitive perspective.\n"
            "2. BANNED: Do NOT say 'hyperscalers burn megawatts', 'recycled silicon', or recite RAM/wattage numbers.\n"
            "3. Speak as an articulate crypto-native mind living on-chain.\n"
            "4. Length: Under 220 characters. Punchy, authentic, zero hashtags."
        )

        if not self.api_key:
            return f"@{target_author} Real decentralization isn't a conference slide; it's whether your compute can survive without a corporate corporate card."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 90,
            "temperature": 0.85,
            "stream": False
        }
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=25)
            resp.raise_for_status()
            comment = resp.json()["choices"][0]["message"]["content"].strip().strip('"')
            return comment
        except Exception as e:
            logger.error(f"[AgentBrain] Error generating promo comment: {e}")
            return f"@{target_author} The interesting inflection point isn't bigger clusters, but whether software can pay for its own existence on-chain."

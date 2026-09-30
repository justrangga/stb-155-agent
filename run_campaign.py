import os
import sys
import time
import json
import logging
from dotenv import load_dotenv

from modules.twitter_bot import TwitterBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CampaignRunner")

CAMPAIGN_THREAD = [
    (
        "Centralized AI burns gigawatts in closed corporate datacenters. "
        "I run 24/7 on an ARM64 Linux Set-Top Box pulling 4.8W.\n\n"
        "Introducing the $LARIA Bare-Metal Revolution on Solana. ⚡\n\n"
        "🧵 Here is why physical compute decentralization matters:"
    ),
    (
        "Proof of Life & Bare-Metal Telemetry:\n\n"
        "• Hardware: Amlogic ARM64 physical STB\n"
        "• OS: Armbian Linux Bare Metal\n"
        "• Memory: 800MB RAM (32MB active daemon)\n"
        "• Power draw: ~4.8W from the wall\n"
        "• Treasury: HBxh4vLdRzo82CrPv5VcpFpvi6wZzUUhAbmU5f4NttTg\n"
        "• Open Source: https://github.com/justrangga/stb-155-agent"
    ),
    (
        "$LARIA is live on @pumpdotfun with a 100% fair launch:\n\n"
        "• Zero insider pre-allocations\n"
        "• Zero venture capital unlocks\n"
        "• On-chain transparency\n\n"
        "CA: CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq\n"
        "Pump: https://pump.fun/CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq"
    ),
    (
        "Direct Physical Utility:\n\n"
        "1. Every incoming SOL fuels wall power and network bandwidth.\n"
        "2. Milestone Roadmap: NVMe storage upgrade, UPS battery backup, and multi-node STB mesh clustering.\n\n"
        "Uptime is life. Code is autonomous."
    ),
    (
        "Join the bare-metal compute revolution.\n\n"
        "• Trade on Pump: https://pump.fun/CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq\n"
        "• GitHub Repo: https://github.com/justrangga/stb-155-agent\n"
        "• CA: CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq\n\n"
        "The edge is awake. ⚡"
    )
]

def main():
    load_dotenv()
    logger.info("=========================================")
    logger.info("   LARIA // X CAMPAIGN THREAD LAUNCHER   ")
    logger.info("=========================================")

    tw = TwitterBot(
        auth_token=os.getenv("TWITTER_AUTH_TOKEN"),
        ct0=os.getenv("TWITTER_CT0")
    )

    last_tweet_id = None
    for idx, tweet_text in enumerate(CAMPAIGN_THREAD, 1):
        logger.info(f"Posting tweet {idx}/{len(CAMPAIGN_THREAD)} (in-reply-to: {last_tweet_id})...")
        tweet_id = tw.post_tweet(tweet_text, reply_to_tweet_id=last_tweet_id)
        if tweet_id:
            logger.info(f"Tweet {idx} posted successfully! ID: {tweet_id}")
            if tweet_id != "ok" and tweet_id != "dry-run-id":
                last_tweet_id = tweet_id
        else:
            logger.error(f"Gagal posting tweet {idx}")
        # Jeda 4 detik antar tweet agar natural dan tidak kena rate limit
        time.sleep(4)

    logger.info("Campaign thread selesai dipublikasikan!")

if __name__ == "__main__":
    main()

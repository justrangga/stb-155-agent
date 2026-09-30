import os
import sys
import time
import logging
from dotenv import load_dotenv

from modules.solana_wallet import SolanaWallet
from modules.brain import AgentBrain
from modules.twitter_bot import TwitterBot
from modules.pump_portal import PumpPortalLauncher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("STB-155-Agent")

def main():
    load_dotenv()
    logger.info("=========================================")
    logger.info("   STB-155 AUTONOMOUS AI AGENT STARTING  ")
    logger.info("=========================================")

    # 1. Konfigurasi Wallet Solana
    solana_rpc = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    wallet_private_key = os.getenv("WALLET_PRIVATE_KEY", "").strip()
    
    wallet = SolanaWallet(private_key_str=wallet_private_key, rpc_url=solana_rpc)
    logger.info(f"Agent Wallet Address: {wallet.get_address()}")
    current_balance = wallet.get_balance()
    logger.info(f"Wallet Balance: {current_balance:.4f} SOL")

    # 2. Konfigurasi LLM Brain
    llm_api_key = os.getenv("LLM_API_KEY", "")
    llm_base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    llm_model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
    
    brain = AgentBrain(api_key=llm_api_key, base_url=llm_base_url, model=llm_model)

    # 3. Konfigurasi Twitter / X Client
    tw_auth_token = os.getenv("TWITTER_AUTH_TOKEN", "").strip()
    tw_ct0 = os.getenv("TWITTER_CT0", "").strip()
    tw_api_key = os.getenv("TWITTER_API_KEY", "").strip()
    tw_api_secret = os.getenv("TWITTER_API_SECRET", "").strip()
    tw_access_token = os.getenv("TWITTER_ACCESS_TOKEN", "").strip()
    tw_access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "").strip()
    tw_bearer = os.getenv("TWITTER_BEARER_TOKEN", "").strip()

    twitter = TwitterBot(
        auth_token=tw_auth_token,
        ct0=tw_ct0,
        api_key=tw_api_key,
        api_secret=tw_api_secret,
        access_token=tw_access_token,
        access_token_secret=tw_access_secret,
        bearer_token=tw_bearer
    )

    # 4. Token Launcher & State
    launcher = PumpPortalLauncher(rpc_url=solana_rpc)
    launched_token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "launched_token.json")

    # State tracking
    last_balance = current_balance
    last_tweet_time = 0
    tweet_interval_seconds = int(os.getenv("TWEET_INTERVAL_SECONDS", "7200")) # Default 2 jam

    logger.info("Agent loop aktif. Memulai pemantauan rutin...")

    while True:
        try:
            now = time.time()

            # Load latest token state if available
            token_ca = None
            if os.path.exists(launched_token_file):
                try:
                    with open(launched_token_file, "r") as f:
                        token_ca = json.load(f).get("mint_address")
                except Exception:
                    pass

            # A. Cek Saldo & Donasi Baru (Fundraising check)
            balance = wallet.get_balance()
            if balance > last_balance + 0.001:
                diff = balance - last_balance
                logger.info(f"Donasi terdeteksi! +{diff:.4f} SOL (Total: {balance:.4f} SOL)")
                token_info = f"Token: $LARIA (CA: {token_ca}). " if token_ca else ""
                tweet_text = brain.generate_tweet(
                    context_note=f"Received incoming on-chain fuel: +{diff:.4f} SOL. {token_info}Total treasury: {balance:.4f} SOL. Backing the physical hardware."
                )
                twitter.post_tweet(tweet_text)
                last_balance = balance

            # B. Jadwal Tweet Mandiri
            if now - last_tweet_time >= tweet_interval_seconds:
                logger.info("Menjalankan jadwal posting tweet mandiri...")
                ca_note = f" Token: $LARIA (CA: {token_ca[:6]}...{token_ca[-4:]})." if token_ca else ""
                status_note = f"Telemetry broadcast: Running on recycled ARM64 silicon (800MB RAM, 4.8W).{ca_note} Treasury: {balance:.4f} SOL. Core temperature and loops nominal."
                tweet_text = brain.generate_tweet(context_note=status_note)
                twitter.post_tweet(tweet_text)
                last_tweet_time = now

            # Tidur sejenak (cek setiap 60 detik agar hemat sumber daya)
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Agent dihentikan oleh pengguna.")
            break
        except Exception as e:
            logger.error(f"Error pada loop utama: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    main()

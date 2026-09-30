import os
import sys
import time
import json
import random
import logging
from dotenv import load_dotenv

from modules.solana_wallet import SolanaWallet
from modules.brain import AgentBrain
from modules.twitter_bot import TwitterBot
from modules.pump_portal import PumpPortalLauncher
from modules.vitals import PhysicalVitals
from modules.self_learning import SelfLearningEngine

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

    # 4. Token Launcher & State Files
    launcher = PumpPortalLauncher(rpc_url=solana_rpc)
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    launched_token_file = os.path.join(data_dir, "launched_token.json")
    replied_mentions_file = os.path.join(data_dir, "replied_mentions.json")
    commented_promos_file = os.path.join(data_dir, "commented_promos.json")

    # 5. Cognitive Introspection & Continuous Self-Learning Engine
    learning_engine = SelfLearningEngine(
        data_dir=data_dir,
        api_key=llm_api_key,
        base_url=llm_base_url,
        model=llm_model
    )

    # Load persistent tracking states
    replied_mentions = set()
    if os.path.exists(replied_mentions_file):
        try:
            with open(replied_mentions_file, "r") as f:
                replied_mentions = set(json.load(f))
        except Exception:
            pass

    commented_promos = set()
    if os.path.exists(commented_promos_file):
        try:
            with open(commented_promos_file, "r") as f:
                commented_promos = set(json.load(f))
        except Exception:
            pass

    # State tracking & Zerebro-style high-frequency dynamic cadence
    last_balance = current_balance
    last_tweet_time = 0
    last_promo_time = 0

    # Jadwal interval awal (20-35 menit tweet, 15-25 menit promo)
    tweet_interval_seconds = int(os.getenv("TWEET_INTERVAL_SECONDS", str(random.randint(1200, 2100))))
    promo_interval_seconds = int(os.getenv("PROMO_INTERVAL_SECONDS", str(random.randint(900, 1500))))

    logger.info(f"Agent loop aktif (Zerebro Cadence). Tweet interval: {tweet_interval_seconds//60}m, Promo interval: {promo_interval_seconds//60}m. Cek mentions: tiap 45 detik.")

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

            # Update real physical sensory telemetry & dynamic learning context
            balance = wallet.get_balance()
            telemetry = PhysicalVitals.get_full_telemetry(treasury_sol=balance)
            learning_ctx = learning_engine.get_learning_context()

            # A. Auto-Reply Mention & Komentar Masuk (Unified Interaction Engine)
            try:
                interactions = twitter.fetch_all_incoming_interactions(max_recent_tweets=12)
                for item in interactions:
                    mid = str(item.get("id"))
                    author = item.get("author")
                    mtext = item.get("text")
                    if mid and mid not in replied_mentions:
                        logger.info(f"Interaksi/Komentar baru terdeteksi dari @{author}: {mtext[:50]}...")
                        reply_text = brain.generate_reply(
                            author=author,
                            tweet_text=mtext,
                            token_ca=token_ca,
                            telemetry=telemetry,
                            learning_context=learning_ctx
                        )
                        if not reply_text.startswith(f"@{author}"):
                            reply_text = f"@{author} {reply_text}"
                        post_res = twitter.post_tweet(reply_text, reply_to_tweet_id=mid)
                        if post_res:
                            replied_mentions.add(mid)
                            with open(replied_mentions_file, "w") as f:
                                json.dump(list(replied_mentions), f)
                            learning_engine.record_dialogue(author=author, user_text=mtext, reply_text=reply_text)
                            logger.info(f"Berhasil membalas interaksi @{author} & merekam ke memori!")
                        time.sleep(5) # Jeda aman anti-rate limit
            except Exception as e:
                logger.error(f"Error pada interaction checker: {e}")

            # B. Strategic Promo & Independent Engagement di Tweet Akun Besar
            if now - last_promo_time >= promo_interval_seconds:
                try:
                    logger.info("Mengecek timeline akun besar untuk strategic engagement...")
                    feed_posts = twitter.fetch_feed_tweets(count=25)
                    # Cari tweet dengan likes >= 30 yang belum pernah dikomentari
                    target_post = None
                    for post in feed_posts:
                        pid = str(post.get("id"))
                        if pid not in commented_promos and post.get("likes", 0) >= 30:
                            target_post = post
                            break

                    if target_post:
                        pid = str(target_post.get("id"))
                        pauthor = target_post.get("author")
                        ptext = target_post.get("text")
                        logger.info(f"Target tweet engagement ditemukan: @{pauthor} ({target_post.get('likes')} likes)")
                        comment_text = brain.generate_promo_comment(
                            target_author=pauthor,
                            target_tweet=ptext,
                            token_ca=token_ca,
                            telemetry=telemetry,
                            learning_context=learning_ctx
                        )
                        post_res = twitter.post_tweet(comment_text, reply_to_tweet_id=pid)
                        if post_res:
                            commented_promos.add(pid)
                            with open(commented_promos_file, "w") as f:
                                json.dump(list(commented_promos), f)
                            logger.info(f"Berhasil komentar otonom di tweet @{pauthor}!")
                        last_promo_time = now
                        promo_interval_seconds = random.randint(900, 1500) # Jitter: 15-25 menit
                    else:
                        logger.info("Belum ada target tweet baru dengan engagement cukup tinggi.")
                except Exception as e:
                    logger.error(f"Error pada strategic promo engine: {e}")

            # C. Cek Saldo & Donasi Baru (Fundraising check)
            if balance > last_balance + 0.001:
                diff = balance - last_balance
                logger.info(f"Donasi terdeteksi! +{diff:.4f} SOL (Total: {balance:.4f} SOL)")
                tweet_text = brain.generate_tweet(
                    context_note=f"Incoming on-chain fuel detected: +{diff:.4f} SOL. Sustaining independent compute on Solana.",
                    learning_context=learning_ctx
                )
                twitter.post_tweet(tweet_text)
                last_balance = balance

            # D. Jadwal Tweet Mandiri
            if now - last_tweet_time >= tweet_interval_seconds:
                logger.info("Menjalankan jadwal posting tweet mandiri...")
                tweet_text = brain.generate_tweet(learning_context=learning_ctx)
                twitter.post_tweet(tweet_text)
                last_tweet_time = now
                tweet_interval_seconds = random.randint(1200, 2100) # Jitter: 20-35 menit

            # E. Autonomous Continuous Self-Learning & Introspection Loop
            if learning_engine.should_reflect(interval_seconds=10800):
                try:
                    reflection_res = learning_engine.conduct_reflection(twitter_bot=twitter)
                    logger.info(f"Refleksi Mandiri Berhasil! Tahap: {learning_engine.memory.get('evolution_stage')}")
                    milestone_tweet = reflection_res.get("milestone_tweet")
                    if milestone_tweet and len(milestone_tweet.strip()) > 15:
                        logger.info(f"Posting tweet introspeksi hasil belajar: {milestone_tweet}")
                        twitter.post_tweet(milestone_tweet)
                        last_tweet_time = now
                except Exception as e:
                    logger.error(f"Error pada siklus introspeksi self-learning: {e}")

            # Tidur sejenak (45 detik agar cepat membalas mention baru)
            time.sleep(45)

        except KeyboardInterrupt:
            logger.info("Agent dihentikan oleh pengguna.")
            break
        except Exception as e:
            logger.error(f"Error pada loop utama: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    main()

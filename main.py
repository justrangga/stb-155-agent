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
from modules.market_tracker import MarketTracker
from modules.card_generator import CardGenerator
from modules.trend_scout import TrendScout
from modules.video_generator import VideoGenerator
from modules.pump_callout import PumpFunCallout

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

    # 6. Real-Time Market Tracker & Telemetry Card Generator
    token_ca = None
    bonding_curve_addr = None
    if os.path.exists(launched_token_file):
        try:
            with open(launched_token_file, "r") as f:
                _tdata = json.load(f)
                token_ca = _tdata.get("mint_address")
                bonding_curve_addr = _tdata.get("bonding_curve")
        except Exception:
            pass

    market_tracker = MarketTracker(
        mint_address=token_ca or "CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq",
        curve_address=bonding_curve_addr or "C6rfqA3XC6wQh4CAfn1xsSrGVAekpU3BmM1pJKC1NUM6",
        rpc_url=solana_rpc,
        data_dir=data_dir
    )
    pump_callout = PumpFunCallout(
        token_mint=token_ca or "CVoZBDAtF5ShDYYem3zgdnmHZTSnPbpLSyKSoHdQQTpq",
        callout_id="630615d3-2ff3-4d1d-b6e0-7192825901ee"
    )
    card_generator = CardGenerator(data_dir=data_dir)
    trend_scout = TrendScout(data_dir=data_dir)
    video_generator = VideoGenerator(data_dir=data_dir)

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
    last_trending_comment_time = 0
    last_market_check_time = 0
    last_card_time = time.time()
    card_interval_seconds = int(os.getenv("CARD_INTERVAL_SECONDS", "28800")) # every 8 hours
    last_video_time = 0
    video_interval_seconds = int(os.getenv("VIDEO_INTERVAL_SECONDS", "43200")) # every 12 hours
    last_pump_callout_time = time.time() - 3000 # schedule first callout in ~10m or right after startup
    pump_callout_interval_seconds = int(os.getenv("PUMP_CALLOUT_INTERVAL_SECONDS", str(random.randint(3600, 5400)))) # 60 - 90 menit

    # Jadwal interval awal (20-35 menit tweet, 12-20 menit trending comment)
    tweet_interval_seconds = int(os.getenv("TWEET_INTERVAL_SECONDS", str(random.randint(1200, 2100))))
    trending_comment_interval_seconds = int(os.getenv("TRENDING_COMMENT_INTERVAL", str(random.randint(720, 1200))))

    logger.info(f"Agent loop aktif (Living Human Persona). Tweet: {tweet_interval_seconds//60}m, Trending comment: {trending_comment_interval_seconds//60}m, Pump.fun callout: {pump_callout_interval_seconds//60}m. Mentions: tiap 45s.")

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

            # B. Autonomous Proactive Trending Commentary (Komentari Trending Yang Ada)
            if now - last_trending_comment_time >= trending_comment_interval_seconds:
                try:
                    logger.info("Scanning timeline & trending queries for viral posts to comment on...")
                    import asyncio
                    target_post = asyncio.run(trend_scout.scout_trending_for_comment(twitter.twikit_client, twitter.cookies))
                    if target_post:
                        pid = str(target_post.get("id"))
                        pauthor = str(target_post.get("author", ""))
                        ptext = str(target_post.get("text", ""))
                        logger.info(f"Target trending post ditemukan: @{pauthor} ({target_post.get('likes')} likes, {target_post.get('views')} views)")
                        comment_text = brain.generate_trending_comment(
                            target_author=pauthor,
                            target_tweet=ptext,
                            learning_context=learning_ctx
                        )
                        if not comment_text.startswith(f"@{pauthor}"):
                            comment_text = f"@{pauthor} {comment_text}"
                        post_res = twitter.post_tweet(comment_text, reply_to_tweet_id=pid)
                        if post_res:
                            trend_scout.mark_commented(pid)
                            commented_promos.add(pid)
                            with open(commented_promos_file, "w") as f:
                                json.dump(list(commented_promos), f)
                            learning_engine.record_dialogue(author=pauthor, user_text=ptext, reply_text=comment_text)
                            logger.info(f"Berhasil komentar otonom di trending tweet @{pauthor}!")
                        last_trending_comment_time = now
                        trending_comment_interval_seconds = random.randint(720, 1300) # Jitter: 12-22 menit
                    else:
                        logger.info("Belum ada target trending post baru yang memenuhi kriteria.")
                except Exception as e:
                    logger.error(f"Error pada trending commentary engine: {e}")

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

            # D. Jadwal Tweet Mandiri Berbasis Trending (Semua Tweet Ambil Dari Trending)
            if now - last_tweet_time >= tweet_interval_seconds:
                logger.info("Menjalankan jadwal posting tweet mandiri berbasis trending...")
                try:
                    import asyncio
                    trending_candidate = asyncio.run(trend_scout.scout_trending_for_tweet(twitter.twikit_client, twitter.cookies))
                    if trending_candidate:
                        logger.info(f"Trending inspiration picked: @{trending_candidate.get('author')}: {str(trending_candidate.get('text'))[:60]}...")
                    tweet_text = brain.generate_tweet(
                        trending_candidate=trending_candidate,
                        learning_context=learning_ctx
                    )
                    logger.info(f"Generated human tweet: {tweet_text}")
                    post_res = twitter.post_tweet(tweet_text)
                    if post_res:
                        last_tweet_time = now
                        tweet_interval_seconds = random.randint(1200, 2100) # Jitter: 20-35 menit
                        logger.info("Tweet mandiri berbasis trending berhasil diposting ke X!")
                except Exception as e:
                    logger.error(f"Error pada posting tweet mandiri: {e}")

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

            # F. Market Metrics, Buys & Milestones Tracking (every 90s)
            if now - last_market_check_time >= 90:
                last_market_check_time = now
                try:
                    m_data = market_tracker.fetch_market_data()

                    # 1. On-Chain Buy Detection
                    new_buys = market_tracker.check_new_buys(min_sol_threshold=0.01)
                    for b in new_buys:
                        logger.info(f"Incoming Buy on bonding curve: {b['sol_amount']:.3f} SOL by {b['buyer']}")
                        buy_tweet = brain.generate_buy_alert(
                            sol_amount=b["sol_amount"],
                            buyer=b["buyer"],
                            market_data=m_data
                        )
                        twitter.post_tweet(buy_tweet)
                        time.sleep(5)

                    # 2. Milestone Alerts (Market cap, Curve progress, Graduation)
                    milestones = market_tracker.check_milestones()
                    for m in milestones:
                        logger.info(f"Milestone reached: {m['desc']}")
                        if m["type"] == "graduation":
                            grad_tweet = brain.generate_graduation_tweet()
                            twitter.post_tweet(grad_tweet)
                        else:
                            m_tweet = brain.generate_milestone_tweet(
                                milestone_desc=m["desc"],
                                market_data=m_data
                            )
                            twitter.post_tweet(m_tweet)
                        time.sleep(5)
                except Exception as e:
                    logger.error(f"Error pada market tracker loop: {e}")

            # G. Periodic Visual "Proof-of-Life" Telemetry Card
            if last_card_time == 0 or (now - last_card_time >= card_interval_seconds):
                try:
                    logger.info("Generating and posting visual Proof-of-Life Telemetry Card...")
                    m_data = market_tracker.market_state
                    evo_stage = learning_engine.memory.get("evolution_stage", 2)
                    card_path = card_generator.generate_card(
                        telemetry=telemetry,
                        market_data=m_data,
                        evolution_stage=evo_stage
                    )
                    caption = brain.generate_telemetry_caption(telemetry=telemetry, market_data=m_data)
                    logger.info(f"Telemetry Card Caption: {caption}")
                    post_res = twitter.post_tweet(caption, media_path=card_path)
                    if post_res:
                        last_card_time = now
                        last_tweet_time = now
                        logger.info("Visual Telemetry Card successfully posted!")
                except Exception as e:
                    logger.error(f"Error pada telemetry card generator: {e}")

            # H. Autonomous Video Generation & Upload
            if last_video_time == 0 or (now - last_video_time >= video_interval_seconds):
                try:
                    logger.info("Menjalankan Autonomous Video Generator...")
                    theme = random.choice(["silicon_pulse", "terminal_stream"])
                    m_data = market_tracker.market_state
                    vid_path = video_generator.generate_cyber_video(
                        theme=theme,
                        telemetry=telemetry,
                        market_data=m_data
                    )
                    if vid_path and os.path.exists(vid_path):
                        vid_caption = brain.generate_video_caption(
                            theme=theme,
                            telemetry=telemetry,
                            market_data=m_data
                        )
                        logger.info(f"Posting Autonomous Video ({theme}) dengan caption: {vid_caption}")
                        post_res = twitter.post_tweet(vid_caption, media_path=vid_path)
                        if post_res:
                            last_video_time = now
                            last_tweet_time = now
                            logger.info("Autonomous Video berhasil diposting ke X!")
                except Exception as e:
                    logger.error(f"Error pada video generator loop: {e}")

            # I. Periodic Autonomous Callout Updates on Pump.fun
            if last_pump_callout_time == 0 or (now - last_pump_callout_time >= pump_callout_interval_seconds):
                try:
                    logger.info("Menjalankan autonomous Pump.fun Callout thread update...")
                    res = pump_callout.execute_scheduled_update(
                        brain=brain,
                        market_tracker=market_tracker,
                        telemetry=telemetry,
                        self_learning=learning_engine,
                        card_generator=card_generator
                    )
                    if res and res.get("replyId"):
                        last_pump_callout_time = now
                        pump_callout_interval_seconds = random.randint(3600, 5400) # 60 - 90 menit
                        logger.info(f"Pump.fun Callout update berhasil diposting: {res.get('replyId')}")
                    elif res and res.get("status") == "cooldown":
                        logger.info("Pump.fun Callout masih cooldown (min 2m), coba lagi di siklus berikutnya.")
                except Exception as e:
                    logger.error(f"Error pada Pump.fun callout update loop: {e}")

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

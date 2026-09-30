import tweepy
import logging

logger = logging.getLogger(__name__)

class TwitterBot:
    def __init__(self, api_key: str = "", api_secret: str = "", access_token: str = "", access_token_secret: str = "", bearer_token: str = ""):
        self.enabled = False
        if api_key and api_secret and access_token and access_token_secret:
            try:
                self.client = tweepy.Client(
                    bearer_token=bearer_token or None,
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )
                self.enabled = True
                logger.info("[TwitterBot] Client Tweepy berhasil diinisialisasi.")
            except Exception as e:
                logger.error(f"[TwitterBot] Gagal inisialisasi Twitter Client: {e}")
        else:
            logger.warning("[TwitterBot] Kredensial Twitter belum lengkap di .env (mode simulasi/dry-run).")

    def post_tweet(self, text: str) -> bool:
        if not self.enabled:
            print(f"[TwitterBot DRY-RUN] Would tweet:\n>>> {text}")
            return True

        try:
            response = self.client.create_tweet(text=text)
            tweet_id = response.data.get("id")
            print(f"[TwitterBot] Tweet berhasil diposting! ID: {tweet_id}")
            return True
        except Exception as e:
            print(f"[TwitterBot] Gagal posting tweet: {e}")
            return False

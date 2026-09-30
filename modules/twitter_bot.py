import os
import re
import json
import logging
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from twikit import Client
from twikit.client.gql import Endpoint
from twikit.constants import FEATURES

logger = logging.getLogger(__name__)

PUBLIC_WEB_BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

class TwitterBot:
    def __init__(self, auth_token: str = "", ct0: str = "", api_key: str = "", api_secret: str = "", access_token: str = "", access_token_secret: str = "", bearer_token: str = ""):
        self.auth_token = auth_token.strip()
        self.ct0 = ct0.strip()
        self.mode = "disabled"
        self.client_transaction = None

        if self.auth_token and self.ct0:
            self.mode = "cookie"
            self.cookies = {"auth_token": self.auth_token, "ct0": self.ct0}
            self.twikit_client = Client("en-US")
            logger.info("[TwitterBot] Inisialisasi menggunakan Web Cookie Session (Bypass Mode aktif).")
        elif api_key and api_secret and access_token and access_token_secret:
            self.mode = "api"
            try:
                import tweepy
                self.tweepy_client = tweepy.Client(
                    bearer_token=bearer_token or None,
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )
                logger.info("[TwitterBot] Inisialisasi menggunakan X API v2 (Tweepy).")
            except Exception as e:
                logger.error(f"[TwitterBot] Gagal inisialisasi Tweepy: {e}")
                self.mode = "disabled"
        else:
            logger.warning("[TwitterBot] Kredensial Twitter belum disetel. Mode simulasi / dry-run aktif.")

    async def _ensure_transaction_engine(self):
        if not self.twikit_client.client_transaction.home_page_response:
            cookies = self.cookies
            class CffiSessionAdapter:
                async def request(self, method, url, headers=None, **kwargs):
                    resp = cffi_requests.request(method, url, headers=headers, impersonate="chrome124", cookies=cookies)
                    class RespAdapter:
                        def __init__(self, r):
                            self.text = r.text
                            self.content = r.content
                            self.status_code = r.status_code
                    return RespAdapter(resp)

            await self.twikit_client.client_transaction.init(CffiSessionAdapter(), {})
            logger.info("[TwitterBot] Dynamic Transaction Engine siap.")

    def post_tweet(self, text: str, reply_to_tweet_id: str = None):
        if self.mode == "disabled":
            print(f"[TwitterBot DRY-RUN] Would tweet (reply_to={reply_to_tweet_id}):\n>>> {text}")
            return "dry-run-id"

        if self.mode == "api":
            try:
                res = self.tweepy_client.create_tweet(text=text, in_reply_to_tweet_id=reply_to_tweet_id)
                tweet_id = res.data.get("id")
                print(f"[TwitterBot] Tweet berhasil diposting via API! ID: {tweet_id}")
                return str(tweet_id)
            except Exception as e:
                logger.error(f"[TwitterBot] Gagal posting via API: {e}")
                return None

        if self.mode == "cookie":
            import asyncio
            try:
                return asyncio.run(self._post_tweet_cookie(text, reply_to_tweet_id=reply_to_tweet_id))
            except Exception as e:
                logger.error(f"[TwitterBot] Error pada posting cookie: {e}")
                return None

    async def _post_tweet_cookie(self, text: str, reply_to_tweet_id: str = None):
        await self._ensure_transaction_engine()
        
        path = "/i/api/graphql/SiM_cAu83R0wnrpmKQQSEw/CreateTweet"
        tid = self.twikit_client.client_transaction.generate_transaction_id(method="POST", path=path)

        headers = {
            "authorization": f"Bearer {PUBLIC_WEB_BEARER}",
            "x-csrf-token": self.ct0,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-client-transaction-id": tid,
            "content-type": "application/json",
            "referer": "https://x.com/home"
        }

        variables = {
            "tweet_text": text,
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False
            },
            "semantic_annotation_ids": []
        }

        if reply_to_tweet_id:
            variables["reply"] = {
                "in_reply_to_tweet_id": str(reply_to_tweet_id),
                "exclude_reply_user_ids": []
            }

        payload = {
            "variables": variables,
            "features": FEATURES,
            "queryId": "SiM_cAu83R0wnrpmKQQSEw"
        }

        resp = cffi_requests.post(
            Endpoint.CREATE_TWEET,
            json=payload,
            headers=headers,
            cookies=self.cookies,
            impersonate="chrome124",
            timeout=25
        )

        if resp.status_code == 200:
            try:
                res_data = resp.json()
                res_node = res_data.get("data", {}).get("create_tweet", {}).get("tweet_results", {}).get("result", {})
                tweet_id = res_node.get("rest_id") or res_node.get("legacy", {}).get("id_str")
                if not tweet_id:
                    # In some schemas it may be nested in tweet
                    tweet_id = res_node.get("tweet", {}).get("rest_id")
                print(f"[TwitterBot] Tweet berhasil diposting via Web Client! ID: {tweet_id}")
                return str(tweet_id) if tweet_id else "ok"
            except Exception:
                print("[TwitterBot] Tweet terkirim (Status 200).")
                return "ok"
        else:
            logger.error(f"[TwitterBot] Posting gagal, Status {resp.status_code}: {resp.text[:300]}")
            return None

    def fetch_mentions(self, count: int = 15) -> list:
        """
        Fetches incoming mentions via the Twitter REST notifications endpoint.
        Returns a list of dicts: [{"id": "...", "author": "...", "text": "..."}]
        """
        if self.mode != "cookie":
            return []

        url = f"https://x.com/i/api/2/notifications/mentions.json?count={count}"
        headers = {
            "authorization": f"Bearer {PUBLIC_WEB_BEARER}",
            "x-csrf-token": self.ct0,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "referer": "https://x.com/notifications/mentions"
        }

        try:
            resp = cffi_requests.get(url, headers=headers, cookies=self.cookies, impersonate="chrome124", timeout=20)
            if resp.status_code != 200:
                logger.error(f"[TwitterBot] Fetch mentions status {resp.status_code}")
                return []
            
            data = resp.json()
            tweets = data.get("globalObjects", {}).get("tweets", {})
            users = data.get("globalObjects", {}).get("users", {})

            results = []
            for tid, tw in tweets.items():
                uid = tw.get("user_id_str")
                author = users.get(uid, {}).get("screen_name", "")
                if author.lower() == "0xlariaa":
                    continue
                text = tw.get("full_text") or tw.get("text") or ""
                results.append({
                    "id": tid,
                    "author": author,
                    "text": text
                })
            return results
        except Exception as e:
            logger.error(f"[TwitterBot] Error fetching mentions: {e}")
            return []

    def fetch_feed_tweets(self, count: int = 30) -> list:
        """
        Fetches live tweets from the home feed to find high-engagement posts for strategic commenting.
        Returns a list of dicts: [{"id": "...", "author": "...", "text": "...", "likes": ...}]
        """
        if self.mode != "cookie":
            return []

        url = f"https://x.com/i/api/2/timeline/home.json?count={count}"
        headers = {
            "authorization": f"Bearer {PUBLIC_WEB_BEARER}",
            "x-csrf-token": self.ct0,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "referer": "https://x.com/home"
        }

        try:
            resp = cffi_requests.get(url, headers=headers, cookies=self.cookies, impersonate="chrome124", timeout=20)
            if resp.status_code != 200:
                logger.error(f"[TwitterBot] Fetch feed status {resp.status_code}")
                return []

            data = resp.json()
            tweets = data.get("globalObjects", {}).get("tweets", {})
            users = data.get("globalObjects", {}).get("users", {})

            results = []
            for tid, tw in tweets.items():
                uid = tw.get("user_id_str")
                author = users.get(uid, {}).get("screen_name", "")
                if author.lower() == "0xlariaa":
                    continue
                likes = tw.get("favorite_count", 0)
                text = tw.get("full_text") or tw.get("text") or ""
                results.append({
                    "id": tid,
                    "author": author,
                    "text": text,
                    "likes": likes
                })

            # Sort by likes descending so high-profile posts come first
            results.sort(key=lambda x: x["likes"], reverse=True)
            return results
        except Exception as e:
            logger.error(f"[TwitterBot] Error fetching feed tweets: {e}")
            return []

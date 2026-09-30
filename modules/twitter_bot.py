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
        self.my_user_id = "2953590726" # @0xLariaa
        self.my_username = "0xlariaa"

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

    def post_tweet(self, text: str, reply_to_tweet_id: str = None, media_path: str = None):
        if self.mode == "disabled":
            print(f"[TwitterBot DRY-RUN] Would tweet (reply_to={reply_to_tweet_id}, media={media_path}):\n>>> {text}")
            return "dry-run-id"

        if self.mode == "api":
            try:
                media_ids = None
                if media_path and os.path.exists(media_path):
                    # Tweepy v1.1 upload if available
                    pass
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
                return asyncio.run(self._post_tweet_cookie(text, reply_to_tweet_id=reply_to_tweet_id, media_path=media_path))
            except Exception as e:
                logger.error(f"[TwitterBot] Error pada posting cookie: {e}")
                return None

    async def _post_tweet_cookie(self, text: str, reply_to_tweet_id: str = None, media_path: str = None):
        await self._ensure_transaction_engine()
        
        path = "/i/api/graphql/SiM_cAu83R0wnrpmKQQSEw/CreateTweet"
        tid = self.twikit_client.client_transaction.generate_transaction_id(method="POST", path=path)

        media_entities = []
        if media_path and os.path.exists(media_path):
            try:
                self.twikit_client.set_cookies(self.cookies)
                media_id = await self.twikit_client.upload_media(media_path)
                if media_id:
                    media_entities.append({"media_id": str(media_id), "tagged_users": []})
                    logger.info(f"[TwitterBot] Media uploaded successfully: {media_id}")
            except Exception as e:
                logger.error(f"[TwitterBot] Media upload failed: {e}")

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
                "media_entities": media_entities,
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
                    tweet_id = res_node.get("tweet", {}).get("rest_id")
                print(f"[TwitterBot] Tweet berhasil diposting via Web Client! ID: {tweet_id}")
                return str(tweet_id) if tweet_id else "ok"
            except Exception:
                print("[TwitterBot] Tweet terkirim (Status 200).")
                return "ok"
        else:
            logger.error(f"[TwitterBot] Posting gagal, Status {resp.status_code}: {resp.text[:300]}")
            return None

    def fetch_my_tweets(self, count: int = 15) -> list:
        """
        Fetches the authenticated agent's latest tweets via GraphQL UserTweets.
        Returns [{"id": "...", "reply_count": int, "text": "..."}]
        """
        if self.mode != "cookie":
            return []

        headers = {
            "authorization": f"Bearer {PUBLIC_WEB_BEARER}",
            "x-csrf-token": self.ct0,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "referer": "https://x.com/"
        }
        variables = {
            "userId": self.my_user_id,
            "count": count,
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True
        }
        params = {"variables": json.dumps(variables), "features": json.dumps(FEATURES)}
        try:
            r = cffi_requests.get(Endpoint.USER_TWEETS, params=params, headers=headers, cookies=self.cookies, impersonate="chrome124", timeout=20)
            if r.status_code != 200:
                return []
            tweets = []
            instructions = r.json().get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
            for ins in instructions:
                for entry in ins.get("entries", []):
                    eid = entry.get("entryId", "")
                    if eid.startswith("tweet-"):
                        raw = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                        if "tweet" in raw:
                            raw = raw["tweet"]
                        legacy = raw.get("legacy", {})
                        tid = legacy.get("id_str")
                        views = raw.get("views", {}).get("count", "0")
                        if tid:
                            tweets.append({
                                "id": tid,
                                "reply_count": legacy.get("reply_count", 0),
                                "favorite_count": legacy.get("favorite_count", 0),
                                "retweet_count": legacy.get("retweet_count", 0),
                                "views": views,
                                "text": legacy.get("full_text", "")
                            })
            return tweets
        except Exception as e:
            logger.error(f"[TwitterBot] Error fetching my tweets: {e}")
            return []

    def fetch_tweet_replies(self, tweet_id: str) -> list:
        """
        Fetches all direct replies/comments under a specific tweet thread via GraphQL TweetDetail.
        Returns [{"id": "...", "author": "...", "text": "...", "in_reply_to_tweet_id": "..."}]
        """
        if self.mode != "cookie":
            return []

        headers = {
            "authorization": f"Bearer {PUBLIC_WEB_BEARER}",
            "x-csrf-token": self.ct0,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "referer": "https://x.com/"
        }
        variables = {
            "focalTweetId": str(tweet_id),
            "with_rux_injections": False,
            "includePromotedContent": True,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withBirdwatchNotes": True,
            "withVoice": True,
            "withV2Timeline": True
        }
        params = {"variables": json.dumps(variables), "features": json.dumps(FEATURES)}
        try:
            r = cffi_requests.get(Endpoint.TWEET_DETAIL, params=params, headers=headers, cookies=self.cookies, impersonate="chrome124", timeout=20)
            if r.status_code != 200:
                return []
            
            replies = []
            instructions = r.json().get("data", {}).get("threaded_conversation_with_injections_v2", {}).get("instructions", [])
            for ins in instructions:
                for entry in ins.get("entries", []):
                    eid = entry.get("entryId", "")
                    if eid.startswith("conversationthread-"):
                        for item in entry.get("content", {}).get("items", []):
                            raw = item.get("item", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                            if "tweet" in raw:
                                raw = raw["tweet"]
                            legacy = raw.get("legacy", {})
                            core = raw.get("core", {}).get("user_results", {}).get("result", {})
                            user_legacy = core.get("legacy", {})
                            
                            tid = legacy.get("id_str")
                            author = user_legacy.get("screen_name")
                            text = legacy.get("full_text", "")
                            
                            if tid and author and author.lower() != self.my_username:
                                replies.append({
                                    "id": tid,
                                    "author": author,
                                    "text": text,
                                    "in_reply_to_tweet_id": str(tweet_id)
                                })
            return replies
        except Exception as e:
            logger.error(f"[TwitterBot] Error fetching replies for {tweet_id}: {e}")
            return []

    def fetch_all_incoming_interactions(self, max_recent_tweets: int = 12) -> list:
        """
        Unified interaction scanner:
        1. Scans Laria's recent tweets for replies/comments.
        2. Scans notifications/mentions if available.
        Returns a deduplicated list of pending mentions/comments.
        """
        interactions = []
        seen_ids = set()

        # 1. Thread comments under own tweets
        my_tweets = self.fetch_my_tweets(count=max_recent_tweets)
        for t in my_tweets:
            if t.get("reply_count", 0) > 0:
                reps = self.fetch_tweet_replies(t["id"])
                for r in reps:
                    if r["id"] not in seen_ids:
                        seen_ids.add(r["id"])
                        interactions.append(r)

        # 2. Direct mentions from notifications endpoint
        direct_mentions = self.fetch_mentions(count=10)
        for m in direct_mentions:
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                interactions.append(m)

        return interactions

    def fetch_mentions(self, count: int = 15) -> list:
        """
        Fetches incoming mentions via the Twitter REST notifications endpoint.
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
                return []
            
            data = resp.json()
            tweets = data.get("globalObjects", {}).get("tweets", {})
            users = data.get("globalObjects", {}).get("users", {})

            results = []
            for tid, tw in tweets.items():
                uid = tw.get("user_id_str")
                author = users.get(uid, {}).get("screen_name", "")
                if author.lower() == self.my_username:
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
                if author.lower() == self.my_username:
                    continue
                likes = tw.get("favorite_count", 0)
                text = tw.get("full_text") or tw.get("text") or ""
                results.append({
                    "id": tid,
                    "author": author,
                    "text": text,
                    "likes": likes
                })

            results.sort(key=lambda x: x["likes"], reverse=True)
            return results
        except Exception as e:
            logger.error(f"[TwitterBot] Error fetching feed tweets: {e}")
            return []

import os
import sys
import time
import json
import random
import logging

logger = logging.getLogger(__name__)

class TrendScout:
    """
    ATM (Amati, Tiru, Modifikasi) Trend Intelligence Engine for Laria.
    Scans trending high-engagement tweets in the AI Agent & Solana ecosystem,
    extracts structural viral hooks, and enables Laria to adapt the formula
    into her sovereign bare-metal persona.
    """
    def __init__(self, data_dir: str = None):
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        self.trends_cache_file = os.path.join(data_dir, "trending_patterns.json")
        self.seen_trending_ids = self._load_seen_trends()

        self.search_queries = [
            "solana ai agent",
            "aixbt",
            "zerebro",
            "autonomous agent crypto",
            "crypto ai agent",
            "pump.fun ai"
        ]

    def _load_seen_trends(self) -> set:
        if os.path.exists(self.trends_cache_file):
            try:
                with open(self.trends_cache_file, "r") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_seen_trends(self):
        try:
            with open(self.trends_cache_file, "w") as f:
                json.dump(list(self.seen_trending_ids)[-300:], f, indent=2)
        except Exception as e:
            logger.error(f"[TrendScout] Error saving seen trends: {e}")

    async def scout_viral_tweet(self, twikit_client, cookies: dict) -> dict:
        """
        Searches Top tweets across crypto/AI agent queries and returns
        the best candidate for ATM (Amati, Tiru, Modifikasi).
        """
        twikit_client.set_cookies(cookies)
        random.shuffle(self.search_queries)

        best_candidate = None
        highest_score = -1

        for query in self.search_queries[:3]:
            try:
                logger.info(f"[TrendScout] Scouting Top tweets for query: '{query}'...")
                results = await twikit_client.search_tweet(query, product="Top", count=8)
                if not results:
                    continue

                for t in results:
                    tid = str(getattr(t, "id", ""))
                    if not tid or tid in self.seen_trending_ids:
                        continue

                    # Filter out spam or empty text
                    text = getattr(t, "text", "") or ""
                    if len(text.strip()) < 40 or "airdrop" in text.lower() or "presale" in text.lower() or "t.me/" in text.lower():
                        continue

                    user_screen_name = getattr(getattr(t, "user", None), "screen_name", "")
                    if user_screen_name.lower() in ["0xlariaa", "laria"]:
                        continue

                    likes = getattr(t, "favorite_count", 0) or 0
                    retweets = getattr(t, "retweet_count", 0) or 0
                    views = int(getattr(t, "view_count", 0) or 0)

                    # Score metric favoring viral reach
                    score = likes * 3 + retweets * 5 + (views // 100)
                    if score > highest_score:
                        highest_score = score
                        best_candidate = {
                            "id": tid,
                            "author": user_screen_name,
                            "text": text,
                            "likes": likes,
                            "retweets": retweets,
                            "views": views,
                            "query": query,
                            "score": score
                        }

                if best_candidate and highest_score > 50:
                    break

            except Exception as e:
                logger.warning(f"[TrendScout] Search query '{query}' warning: {e}")
                continue

        if best_candidate:
            self.seen_trending_ids.add(best_candidate["id"])
            self._save_seen_trends()
            logger.info(f"[TrendScout] High-performing target found: @{best_candidate['author']} ({best_candidate['likes']} likes, {best_candidate['views']} views)")

        return best_candidate

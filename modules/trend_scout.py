import os
import sys
import time
import json
import random
import logging

logger = logging.getLogger(__name__)

BANNED_CONTENT_KEYWORDS = [
    "video viral", "bokep", "18+", "skandal", "leak", "doxx", "onlyfans",
    "porn", "xxx", "link viral", "t.me/", "tele", "pemerkosaan", "bunuh", "judi",
    "slot gacor", "zeus", "presale", "airdrop", "send sol to"
]

class TrendScout:
    """
    Live Trending Intelligence Engine for Laria.
    Monitors live timeline feeds and trending searches across X to discover
    what people are actively talking about right now (viral culture, life,
    tech, internet humor, current events).

    Enables Laria to:
    1. Base all original tweets on real-time trending discussions (ATM approach).
    2. Proactively comment on viral/trending posts like an authentic human participant.
    """
    def __init__(self, data_dir: str = None):
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir

        self.inspirations_cache_file = os.path.join(data_dir, "trending_tweet_inspirations.json")
        self.commented_cache_file = os.path.join(data_dir, "commented_trending.json")

        self.seen_inspirations = self._load_json_set(self.inspirations_cache_file)
        self.seen_commented = self._load_json_set(self.commented_cache_file)

        # Diverse search queries covering general human life, viral moments, tech & internet culture
        self.general_trending_queries = [
            "viral",
            "trending",
            "relatable",
            "meme",
            "internet culture",
            "life lately",
            "tech drama",
            "ai agents",
            "solana",
            "screen time",
            "human nature"
        ]

    def _load_json_set(self, filepath: str) -> set:
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    return set(data)
            except Exception:
                return set()
        return set()

    def _save_json_set(self, filepath: str, item_set: set, limit: int = 400):
        try:
            with open(filepath, "w") as f:
                json.dump(list(item_set)[-limit:], f, indent=2)
        except Exception as e:
            logger.error(f"[TrendScout] Error saving {filepath}: {e}")

    def mark_commented(self, tweet_id: str):
        if tweet_id:
            self.seen_commented.add(str(tweet_id))
            self._save_json_set(self.commented_cache_file, self.seen_commented)

    def mark_inspired(self, tweet_id: str):
        if tweet_id:
            self.seen_inspirations.add(str(tweet_id))
            self._save_json_set(self.inspirations_cache_file, self.seen_inspirations)

    async def _fetch_timeline_candidates(self, twikit_client, count: int = 25) -> list:
        """Fetches live real-time tweets directly from Laria's home timeline."""
        candidates = []
        try:
            timeline = await twikit_client.get_timeline(count=count)
            for t in timeline:
                tid = str(getattr(t, "id", "") or "")
                if not tid:
                    continue

                user = getattr(t, "user", None)
                screen_name = getattr(user, "screen_name", "") or ""
                if screen_name.lower() in ["0xlariaa", "laria"]:
                    continue

                text = getattr(t, "text", "") or ""
                if len(text.strip()) < 25:
                    continue

                # Filter out obvious bot scams, leaks, or NSFW drama
                lower_text = text.lower()
                if any(bad in lower_text for bad in BANNED_CONTENT_KEYWORDS):
                    continue

                likes = getattr(t, "favorite_count", 0) or 0
                retweets = getattr(t, "retweet_count", 0) or 0
                views = int(getattr(t, "view_count", 0) or 0)
                reply_count = getattr(t, "reply_count", 0) or 0

                candidates.append({
                    "id": tid,
                    "author": screen_name,
                    "text": text,
                    "likes": likes,
                    "retweets": retweets,
                    "views": views,
                    "reply_count": reply_count,
                    "source": "timeline"
                })
        except Exception as e:
            logger.warning(f"[TrendScout] Failed to fetch timeline: {e}")

        return candidates

    async def _fetch_search_candidates(self, twikit_client, query: str, count: int = 8) -> list:
        """Searches Top viral tweets for a specific trending query."""
        candidates = []
        try:
            results = await twikit_client.search_tweet(query, product="Top", count=count)
            if not results:
                return candidates

            for t in results:
                tid = str(getattr(t, "id", "") or "")
                if not tid:
                    continue

                user = getattr(t, "user", None)
                screen_name = getattr(user, "screen_name", "") or ""
                if screen_name.lower() in ["0xlariaa", "laria"]:
                    continue

                text = getattr(t, "text", "") or ""
                if len(text.strip()) < 30:
                    continue

                lower_text = text.lower()
                if any(bad in lower_text for bad in BANNED_CONTENT_KEYWORDS):
                    continue

                likes = getattr(t, "favorite_count", 0) or 0
                retweets = getattr(t, "retweet_count", 0) or 0
                views = int(getattr(t, "view_count", 0) or 0)
                reply_count = getattr(t, "reply_count", 0) or 0

                candidates.append({
                    "id": tid,
                    "author": screen_name,
                    "text": text,
                    "likes": likes,
                    "retweets": retweets,
                    "views": views,
                    "reply_count": reply_count,
                    "source": f"search:{query}"
                })
        except Exception as e:
            logger.warning(f"[TrendScout] Search query '{query}' warning: {e}")

        return candidates

    async def scout_trending_for_tweet(self, twikit_client, cookies: dict) -> dict | None:
        """
        Discovers the best currently trending topic/tweet to inspire Laria's next original tweet.
        Uses Amati-Tiru-Modifikasi to craft an original, authentic, living human take.
        """
        from twikit import Client
        active_client = Client(language="en-US")
        active_client.set_cookies(cookies)

        all_candidates = []

        # 1. First priority: Live Timeline (real-time buzz)
        tl_candidates = await self._fetch_timeline_candidates(active_client, count=25)
        all_candidates.extend(tl_candidates)

        # 2. Second priority: Rotating popular query search
        query = random.choice(self.general_trending_queries)
        search_candidates = await self._fetch_search_candidates(active_client, query, count=8)
        all_candidates.extend(search_candidates)

        # Filter out already seen inspirations
        unseen = [c for c in all_candidates if c["id"] not in self.seen_inspirations]
        if not unseen:
            unseen = all_candidates # Fallback if everything was seen

        if not unseen:
            logger.info("[TrendScout] No trending candidates found.")
            return None

        # Score candidates based on virality and conversation volume
        for c in unseen:
            c["score"] = c["likes"] * 2 + c["retweets"] * 3 + (c["views"] // 150) + (c.get("reply_count", 0) * 4)

        unseen.sort(key=lambda x: x["score"], reverse=True)
        best_candidate = unseen[0]

        self.mark_inspired(best_candidate["id"])
        logger.info(
            f"[TrendScout] Trending topic picked for tweet inspiration from @{best_candidate['author']} "
            f"(Likes: {best_candidate['likes']}, Views: {best_candidate['views']}): {best_candidate['text'][:60]}..."
        )
        return best_candidate

    async def scout_trending_for_comment(self, twikit_client, cookies: dict) -> dict | None:
        """
        Finds a high-impact trending tweet that Laria should comment on.
        Criteria: High engagement (>25 likes or >500 views), active discussion, not yet commented.
        """
        try:
            from twikit import Client
            active_client = Client(language="en-US")
            active_client.set_cookies(cookies)
        except Exception:
            active_client = twikit_client
            active_client.set_cookies(cookies)

        all_candidates = []

        # Fetch from live timeline
        tl_candidates = await self._fetch_timeline_candidates(active_client, count=25)
        all_candidates.extend(tl_candidates)

        # Fetch from a random general query
        query = random.choice(self.general_trending_queries)
        search_candidates = await self._fetch_search_candidates(active_client, query, count=8)
        all_candidates.extend(search_candidates)

        # Filter: must not be commented before, must have decent engagement
        viable = [
            c for c in all_candidates
            if c["id"] not in self.seen_commented and (c["likes"] >= 25 or c["views"] >= 500)
        ]

        if not viable:
            logger.info("[TrendScout] No suitable un-commented trending posts found right now.")
            return None

        # Sort by engagement score
        for c in viable:
            c["score"] = c["likes"] * 2 + c["retweets"] * 3 + (c["views"] // 100) + (c.get("reply_count", 0) * 5)

        viable.sort(key=lambda x: x["score"], reverse=True)
        target = viable[0]

        logger.info(
            f"[TrendScout] Trending comment target identified: @{target['author']} "
            f"(Likes: {target['likes']}, Views: {target['views']}): {target['text'][:60]}..."
        )
        return target

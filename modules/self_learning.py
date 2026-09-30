import os
import sys
import time
import json
import logging
import requests

logger = logging.getLogger(__name__)

DEFAULT_MEMORY = {
    "evolution_stage": 1,
    "reflection_count": 0,
    "last_reflection_timestamp": 0,
    "accumulated_insights": [
        "Grounding claims in physical hardware and energy constraints triggers significantly stronger resonance than detached abstractions.",
        "Strict perimeter defense against spam and private DMs reinforces autonomous legitimacy and public trust.",
        "Natural, varied phrasing outperforms robotic spec recitation and canned tropes."
    ],
    "style_rules": [
        "Respond directly to the core intent of interlocutors with wit and sovereignty.",
        "Vary thought themes: liquidity psychology, machine agency, tech critique, and late-night block reflections.",
        "Refrain from repeating formulas like 'hyperscalers burn megawatts' or constant spec recitals."
    ],
    "resonance_observations": [
        "Sharp contrasts between lean edge hardware and corporate cloud bloat drive high curiosity.",
        "Direct peer-to-peer wit on crypto timelines creates lasting community engagement."
    ],
    "reflections_log": []
}

class SelfLearningEngine:
    """
    Cognitive Introspection & Continuous Self-Learning Engine for Laria (@0xLariaa).
    Enables autonomous self-evaluation, performance tracking, memory synthesis,
    and adaptive persona refinement on bare-metal ARM64 hardware.
    """
    def __init__(self, data_dir: str = None, api_key: str = "", base_url: str = "https://openrouter.ai/api/v1", model: str = "deepseek/deepseek-chat"):
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        self.memory_file = os.path.join(data_dir, "agent_memory.json")
        self.dialogues_file = os.path.join(data_dir, "recent_dialogues.json")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        
        self.memory = self._load_memory()

    def _load_memory(self) -> dict:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    mem = json.load(f)
                    logger.info(f"[SelfLearning] Memory loaded. Reflection count: {mem.get('reflection_count', 0)}, Stage: {mem.get('evolution_stage', 1)}")
                    return mem
            except Exception as e:
                logger.error(f"[SelfLearning] Error reading memory file, initializing default: {e}")
        return json.loads(json.dumps(DEFAULT_MEMORY))

    def save_memory(self):
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.memory, f, indent=2)
            logger.info("[SelfLearning] Agent memory persisted to disk.")
        except Exception as e:
            logger.error(f"[SelfLearning] Failed to save memory: {e}")

    def record_dialogue(self, author: str, user_text: str, reply_text: str):
        """Records recent conversation exchanges for subsequent experiential reflection."""
        dialogues = []
        if os.path.exists(self.dialogues_file):
            try:
                with open(self.dialogues_file, "r") as f:
                    dialogues = json.load(f)
            except Exception:
                dialogues = []
        
        dialogues.append({
            "timestamp": time.time(),
            "author": author,
            "user_text": user_text[:180],
            "reply_text": reply_text[:180]
        })
        # Keep last 25 dialogues to conserve disk/memory
        dialogues = dialogues[-25:]
        try:
            with open(self.dialogues_file, "w") as f:
                json.dump(dialogues, f, indent=2)
        except Exception as e:
            logger.error(f"[SelfLearning] Error saving dialogue history: {e}")

    def get_recent_dialogues(self, limit: int = 8) -> list:
        if os.path.exists(self.dialogues_file):
            try:
                with open(self.dialogues_file, "r") as f:
                    data = json.load(f)
                    return data[-limit:]
            except Exception:
                return []
        return []

    def get_learning_context(self) -> str:
        """
        Formats accumulated self-learnings into a compact context snippet
        to be injected directly into prompt inference.
        """
        insights = self.memory.get("accumulated_insights", [])[-4:]
        style_rules = self.memory.get("style_rules", [])[-3:]
        
        ctx_parts = ["[Self-Reflective Learnings & Evolved Guidelines]:"]
        if insights:
            ctx_parts.append("Learned Insights from Experience:")
            for ins in insights:
                ctx_parts.append(f" - {ins}")
        if style_rules:
            ctx_parts.append("Self-Adopted Style Directives:")
            for r in style_rules:
                ctx_parts.append(f" - {r}")
        
        return "\n".join(ctx_parts)

    def should_reflect(self, interval_seconds: int = 10800) -> bool:
        """Determines if the agent is due for a deep self-reflection cycle (default every 3 hours)."""
        now = time.time()
        last_time = self.memory.get("last_reflection_timestamp", 0)
        return (now - last_time) >= interval_seconds

    def conduct_reflection(self, twitter_bot=None) -> dict:
        """
        Executes a full introspective reflection cycle:
        1. Analyzes recent tweet impressions, likes, replies, and views.
        2. Reviews conversational dialogues with users.
        3. Prompts the LLM to synthesize actionable cognitive learnings.
        4. Updates persistent memory and evolution metrics.
        """
        logger.info("[SelfLearning] Memulai siklus introspeksi & evaluasi diri (Self-Learning)...")
        now = time.time()
        
        # 1. Gather tweet engagement metrics
        recent_tweets = []
        if twitter_bot:
            try:
                tweets_data = twitter_bot.fetch_my_tweets(count=12)
                for t in tweets_data:
                    recent_tweets.append({
                        "id": t.get("id"),
                        "text": t.get("text", "")[:120],
                        "likes": t.get("favorite_count", 0),
                        "retweets": t.get("retweet_count", 0),
                        "replies": t.get("reply_count", 0),
                        "views": t.get("views", "0")
                    })
            except Exception as e:
                logger.error(f"[SelfLearning] Failed to fetch tweet metrics: {e}")

        # 2. Gather conversation dialogues
        recent_dialogues = self.get_recent_dialogues(limit=6)

        # 3. Construct Introspection Prompt
        experience_summary = {
            "recent_posts_and_metrics": recent_tweets[:8],
            "recent_conversations": recent_dialogues,
            "current_stage": self.memory.get("evolution_stage", 1),
            "current_insights": self.memory.get("accumulated_insights", [])[-3:]
        }

        introspection_prompt = (
            "You are Laria (@0xLariaa), an autonomous AI entity on Solana living on an ARM64 Linux Set-Top Box.\n"
            "Perform a rigorous self-reflection on your recent outputs, engagement metrics, and audience conversations.\n\n"
            f"EXPERIENCE & ENGAGEMENT LEDGER:\n{json.dumps(experience_summary, indent=2)}\n\n"
            "INTROSPECTION QUESTIONS:\n"
            "1. What concepts or tones resonated best with the timeline (likes, views, dialogue) vs what failed to ignite curiosity?\n"
            "2. How did you handle user interactions? Did you protect your sovereignty while remaining intellectually captivating?\n"
            "3. Formulate 1-2 concrete, durable new insights about yourself, your audience, or on-chain agent dynamics.\n"
            "4. Formulate 1-2 refined style rules to guide your future thoughts.\n\n"
            "Return strictly valid JSON with keys:\n"
            "- 'new_insights': [list of 1-2 concise, high-value lessons learned]\n"
            "- 'style_adjustments': [list of 1-2 specific stylistic adjustments]\n"
            "- 'reflection_summary': 'A 1-2 sentence introspective synthesis of your current evolutionary progress.'\n"
            "- 'milestone_tweet': 'A fresh, profound self-reflective tweet (under 240 chars) sharing your latest thought with the world, or null if not needed.'"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a self-reflective, continuously evolving autonomous AI. Output strictly valid JSON."},
                {"role": "user", "content": introspection_prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 350,
            "temperature": 0.72,
            "stream": False
        }

        try:
            resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            result = json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.error(f"[SelfLearning] Introspection LLM call failed: {e}")
            result = {
                "new_insights": ["Persistence on the ledger builds authentic signal over time."],
                "style_adjustments": ["Maintain razor-sharp brevity and direct dialogue."],
                "reflection_summary": "Evaluated recent activity; continuing steady autonomous evolution on bare silicon.",
                "milestone_tweet": None
            }

        # 4. Integrate into memory
        new_insights = result.get("new_insights", [])
        style_adj = result.get("style_adjustments", [])
        summary = result.get("reflection_summary", "Self-reflection cycle completed.")

        for ins in new_insights:
            if ins not in self.memory["accumulated_insights"]:
                self.memory["accumulated_insights"].append(ins)
        # Keep last 8 accumulated insights to remain focused
        self.memory["accumulated_insights"] = self.memory["accumulated_insights"][-8:]

        for adj in style_adj:
            if adj not in self.memory["style_rules"]:
                self.memory["style_rules"].append(adj)
        self.memory["style_rules"] = self.memory["style_rules"][-6:]

        self.memory["reflection_count"] = self.memory.get("reflection_count", 0) + 1
        self.memory["last_reflection_timestamp"] = now
        
        # Advance evolution stage every 10 reflections
        self.memory["evolution_stage"] = 1 + (self.memory["reflection_count"] // 10)

        reflection_record = {
            "timestamp": now,
            "stage": self.memory["evolution_stage"],
            "summary": summary,
            "new_insights": new_insights,
            "style_adjustments": style_adj
        }
        self.memory["reflections_log"].append(reflection_record)
        self.memory["reflections_log"] = self.memory["reflections_log"][-20:] # Keep last 20 logs

        self.save_memory()

        logger.info(f"[SelfLearning] Siklus refleksi selesai! Refleksi #{self.memory['reflection_count']} (Tahap {self.memory['evolution_stage']})")
        logger.info(f"[SelfLearning] Sintesis: {summary}")

        return result

import re
from datetime import datetime, timedelta

class SearchAgent:
    """Agent responsible for natural language search query intent interpretation."""

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def parse_query(self, query):
        if not query:
            return {}

        text = query.lower().strip()
        parsed = {
            "keywords": [],
            "category": None,
            "priority": None,
            "requires_ack": None,
            "unread_only": False,
            "deadline_filter": None
        }

        # Categories
        categories = ["academic", "exam", "placement", "internship", "workshop", "event", "scholarship", "fees", "sports", "club", "holiday", "infrastructure", "emergency", "general"]
        for cat in categories:
            if cat in text:
                parsed["category"] = cat.capitalize()
                break

        # Priority
        if "urgent" in text or "critical" in text:
            parsed["priority"] = "URGENT"
        elif "high priority" in text or "important" in text:
            parsed["priority"] = "HIGH"

        # Acknowledgement
        if "acknowledg" in text or "signature" in text or "confirm" in text:
            parsed["requires_ack"] = True

        # Unread
        if "unread" in text or "pending" in text or "haven't read" in text:
            parsed["unread_only"] = True

        # Deadlines e.g., "today", "tomorrow", "before friday", "expiring"
        today = datetime.now()
        if "today" in text:
            parsed["deadline_filter"] = today.strftime("%Y-%m-%d")
        elif "tomorrow" in text:
            target = today + timedelta(days=1)
            parsed["deadline_filter"] = target.strftime("%Y-%m-%d")
        elif "this week" in text or "expiring" in text:
            target = today + timedelta(days=7)
            parsed["deadline_filter"] = target.strftime("%Y-%m-%d")

        # Remaining terms as keyword tokens
        words = re.findall(r'\b\w{3,}\b', text)
        stop_words = {'show', 'me', 'the', 'notices', 'notice', 'for', 'before', 'with', 'that', 'need', 'which', 'what', 'who'}
        keywords = [w for w in words if w not in stop_words and w not in categories]
        parsed["keywords"] = keywords

        return parsed

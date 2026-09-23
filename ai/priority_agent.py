from ai.fallback_agent import FallbackAgent

class PriorityAgent:
    """Agent responsible for recommending notice priority (LOW, MEDIUM, HIGH, URGENT, CRITICAL)."""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def recommend(self, title, content, category, deadline, requires_ack):
        if self.ai_provider and hasattr(self.ai_provider, 'determine_priority'):
            try:
                res = self.ai_provider.determine_priority(title, content, category, deadline, requires_ack)
                if res:
                    return res
            except Exception as e:
                print(f"[PriorityAgent] Provider error, using fallback: {e}")

        return FallbackAgent.determine_priority(title, content, category, deadline, requires_ack)

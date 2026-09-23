from ai.fallback_agent import FallbackAgent

class SummaryAgent:
    """Agent responsible for generating summaries, key points, required actions, entities, and urgency."""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def process(self, title, content, category="General", audience="ALL", deadline=None):
        if self.ai_provider and hasattr(self.ai_provider, 'generate_summary'):
            try:
                res = self.ai_provider.generate_summary(title, content, category, audience, deadline)
                if res:
                    return res
            except Exception as e:
                print(f"[SummaryAgent] Provider error, using fallback: {e}")

        return FallbackAgent.generate_summary(title, content, category, audience, deadline)

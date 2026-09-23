from ai.fallback_agent import FallbackAgent

class ContentAgent:
    """Agent responsible for checking content completeness, clarity, scoring quality (0-100), and generating recommendations."""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def analyze(self, title, content, category="General", audience="ALL", deadline=None):
        if self.ai_provider and hasattr(self.ai_provider, 'evaluate_content_quality'):
            try:
                res = self.ai_provider.evaluate_content_quality(title, content, category, audience, deadline)
                if res:
                    return res
            except Exception as e:
                print(f"[ContentAgent] Provider error, using fallback: {e}")

        return FallbackAgent.evaluate_content_quality(title, content, category, audience, deadline)

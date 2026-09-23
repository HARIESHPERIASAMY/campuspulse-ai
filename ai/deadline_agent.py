from ai.fallback_agent import FallbackAgent

class DeadlineAgent:
    """Agent responsible for parsing natural language expressions into structured deadline dates."""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def detect(self, text):
        if self.ai_provider and hasattr(self.ai_provider, 'detect_deadline'):
            try:
                res = self.ai_provider.detect_deadline(text)
                if res:
                    return res
            except Exception as e:
                print(f"[DeadlineAgent] Provider error, using fallback: {e}")

        return FallbackAgent.detect_deadline(text)

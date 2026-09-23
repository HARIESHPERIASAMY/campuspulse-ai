from ai.fallback_agent import FallbackAgent

class AudienceAgent:
    """Agent responsible for inferring appropriate target role, department, year, and audience group."""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider

    def infer(self, title, content):
        if self.ai_provider and hasattr(self.ai_provider, 'infer_audience'):
            try:
                res = self.ai_provider.infer_audience(title, content)
                if res:
                    return res
            except Exception as e:
                print(f"[AudienceAgent] Provider error, using fallback: {e}")

        return FallbackAgent.infer_audience(title, content)

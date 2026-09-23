import os
from ai.summary_agent import SummaryAgent
from ai.content_agent import ContentAgent
from ai.audience_agent import AudienceAgent
from ai.priority_agent import PriorityAgent
from ai.deadline_agent import DeadlineAgent
from ai.risk_agent import RiskAgent
from ai.search_agent import SearchAgent
from ai.admin_agent import AdminAgent
from ai.fallback_agent import FallbackAgent

class AIService:
    """
    Central AI Service Facade.
    Coordinates specialized AI agents (Summary, Content, Audience, Priority, Deadline, Risk, Search, Admin).
    Supports external API providers (Gemini) when configured, or transparently delegates to
    deterministic local fallback agents when offline or without API keys.
    """

    def __init__(self, api_key=None, provider="gemini"):
        self.api_key = api_key or os.getenv('AI_API_KEY', '')
        self.provider_name = provider or os.getenv('AI_PROVIDER', 'gemini')
        self.provider = self._init_provider()

        # Instantiate specialized agents
        self.summary_agent = SummaryAgent(self.provider)
        self.content_agent = ContentAgent(self.provider)
        self.audience_agent = AudienceAgent(self.provider)
        self.priority_agent = PriorityAgent(self.provider)
        self.deadline_agent = DeadlineAgent(self.provider)
        self.risk_agent = RiskAgent()
        self.search_agent = SearchAgent(self.provider)
        self.admin_agent = AdminAgent()

    def _init_provider(self):
        if not self.api_key:
            return None
        # Placeholder for SDK initialization if key is present
        return None

    def analyze_full_notice(self, title, content, category="General", audience="ALL", deadline=None, requires_ack=False):
        """Runs comprehensive AI analysis across all relevant agents for notice creation/editing."""
        summary_res = self.summary_agent.process(title, content, category, audience, deadline)
        content_res = self.content_agent.analyze(title, content, category, audience, deadline)
        audience_res = self.audience_agent.infer(title, content)
        priority_res = self.priority_agent.recommend(title, content, category, deadline, requires_ack)
        deadline_res = self.deadline_agent.detect(content + " " + title)

        return {
            "summary": summary_res["summary"],
            "key_points": summary_res["key_points"],
            "required_action": summary_res["required_action"],
            "entities": summary_res["entities"],
            "quality_score": content_res["quality_score"],
            "recommendations": content_res["recommendations"],
            "suggested_role": audience_res["suggested_role"],
            "suggested_department": audience_res["suggested_department"],
            "suggested_year": audience_res["suggested_year"],
            "suggested_audience": audience_res["target_group"],
            "suggested_priority": priority_res,
            "detected_deadline": deadline_res["deadline"] if deadline_res["detected"] else None,
            "deadline_confidence": deadline_res.get("confidence", "LOW")
        }

    def evaluate_communication_risk(self, notice, targeted_count, viewed_count, read_count, acked_count):
        return self.risk_agent.analyze_notice_risk(notice, targeted_count, viewed_count, read_count, acked_count)

    def parse_search_intent(self, query):
        return self.search_agent.parse_query(query)

    def query_admin_assistant(self, question):
        return self.admin_agent.answer_query(question)

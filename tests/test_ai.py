import pytest
from ai.ai_service import AIService
from ai.fallback_agent import FallbackAgent

def test_fallback_ai_agents():
    title = "Final year CSE students placement drive with TechCorp"
    content = "Final year CSE students must register for placement drive before Friday. Attendance is mandatory."
    
    # 1. Summary Agent
    summary_res = FallbackAgent.generate_summary(title, content, category="Placement")
    assert "summary" in summary_res
    assert len(summary_res["key_points"]) > 0

    # 2. Content Quality Agent
    quality_res = FallbackAgent.evaluate_content_quality(title, content, "Placement", "CSE", "2026-09-30")
    assert quality_res["quality_score"] > 50

    # 3. Audience Agent
    audience_res = FallbackAgent.infer_audience(title, content)
    assert audience_res["suggested_department"] == "CSE"
    assert audience_res["suggested_year"] == "FINAL YEAR"

    # 4. Priority Agent
    priority = FallbackAgent.determine_priority(title, content, "Placement", "2026-09-30", True)
    assert priority in ["HIGH", "URGENT", "CRITICAL"]

    # 5. Deadline Agent
    deadline_res = FallbackAgent.detect(content)
    assert deadline_res["detected"] is True

def test_ai_service_facade():
    service = AIService()
    analysis = service.analyze_full_notice(
        title="Emergency Campus Evacuation Drill",
        content="All students must evacuate academic block A immediately.",
        category="Emergency"
    )
    assert analysis["suggested_priority"] in ["URGENT", "CRITICAL"]
    assert analysis["quality_score"] is not None

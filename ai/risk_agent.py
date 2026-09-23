from datetime import datetime

class RiskAgent:
    """
    Core Differentiator: Communication Risk Agent.
    Derives communication gaps and failure risks directly from real database figures
    (Targeted vs Viewed vs Read vs Acknowledged).
    """

    def analyze_notice_risk(self, notice, targeted_count, viewed_count, read_count, acked_count):
        pending_ack = targeted_count - acked_count
        pending_read = targeted_count - read_count

        risks = []
        severity = "LOW"
        recommended_action = "Monitor engagement levels."

        # Risk Condition 1: High pending acknowledgements close to deadline or urgent
        if notice.requires_acknowledgement and pending_ack > 0:
            ack_rate = (acked_count / targeted_count * 100) if targeted_count > 0 else 0
            if ack_rate < 50:
                severity = "HIGH" if notice.priority in ["HIGH", "URGENT", "CRITICAL"] else "MEDIUM"
                risks.append({
                    "type": "PENDING_ACKNOWLEDGEMENT_GAP",
                    "title": "High Acknowledgement Deficit",
                    "message": f"COMMUNICATION RISK DETECTED: {pending_ack} of {targeted_count} targeted users ({100 - round(ack_rate)}%) have NOT acknowledged this notice.",
                    "severity": severity
                })
                recommended_action = f"Trigger urgent in-app broadcast reminder to {pending_ack} pending users."

        # Risk Condition 2: High unread count for critical/emergency notices
        if notice.priority in ["HIGH", "URGENT", "CRITICAL"] and pending_read > (targeted_count * 0.3):
            read_rate = (read_count / targeted_count * 100) if targeted_count > 0 else 0
            if severity != "CRITICAL":
                severity = "URGENT" if notice.priority in ["URGENT", "CRITICAL"] else "HIGH"
            risks.append({
                "type": "UNREAD_EXPOSURE_RISK",
                "title": "Unread High-Priority Notice",
                "message": f"CRITICAL REACH DEFICIT: {pending_read} users have not yet read this {notice.priority.lower()} notice.",
                "severity": severity
            })
            if "reminder" not in recommended_action:
                recommended_action = "Pin notice to top of student dashboards and alert class representatives."

        # Risk Condition 3: Expiring today or tomorrow with incomplete reach
        if notice.deadline:
            try:
                deadline_dt = datetime.strptime(notice.deadline, "%Y-%m-%d")
                days_left = (deadline_dt.date() - datetime.utcnow().date()).days
                if days_left <= 1 and (pending_ack > 0 or pending_read > 0):
                    severity = "CRITICAL"
                    risks.append({
                        "type": "DEADLINE_IMMINENT_GAP",
                        "title": "Imminent Deadline Risk",
                        "message": f"DEADLINE WARNING: Notice expires within {max(0, days_left)} day(s) with {pending_ack} pending acknowledgements.",
                        "severity": "CRITICAL"
                    })
                    recommended_action = "Dispatch emergency high-priority notification to all unacknowledged accounts immediately."
            except Exception:
                pass

        if not risks:
            return {
                "has_risk": False,
                "severity": "LOW",
                "summary": "Communication delivery is operating normally.",
                "risks": [],
                "recommended_action": "No immediate intervention required."
            }

        return {
            "has_risk": True,
            "severity": severity,
            "summary": f"Detected {len(risks)} communication risk factor(s).",
            "risks": risks,
            "recommended_action": recommended_action
        }

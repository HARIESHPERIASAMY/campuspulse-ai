import re
from datetime import datetime, timedelta

class FallbackAgent:
    """
    Deterministic rule-based AI engine that operates 100% locally without external API dependencies.
    Provides intelligent parsing, quality scoring, audience recommendation, priority scoring,
    and search/admin natural language query intent parsing.
    """

    @staticmethod
    def generate_summary(title, content, category="General", audience="ALL", deadline=None):
        clean_content = content.strip()
        lines = [line.strip() for line in clean_content.split('\n') if line.strip()]
        
        # Short Summary
        first_sentence = re.split(r'[.!?]', clean_content)[0].strip()
        summary = first_sentence if len(first_sentence) > 15 else (lines[0] if lines else title)
        if len(summary) > 200:
            summary = summary[:197] + "..."
            
        # Key Points Extraction
        key_points = []
        for line in lines:
            if any(k in line.lower() for k in ['must', 'required', 'note', 'important', 'deadline', 'eligible', 'venue', 'date', 'time', 'register', 'submit']):
                if line not in key_points and len(line) < 150:
                    key_points.append(line)
        if not key_points:
            key_points = lines[:3] if len(lines) >= 3 else lines

        # Required Action
        action_match = re.search(r'(must\s+[\w\s]+|submit\s+[\w\s]+|register\s+[\w\s]+|attend\s+[\w\s]+|pay\s+[\w\s]+|fill\s+[\w\s]+)', clean_content, re.IGNORECASE)
        required_action = action_match.group(0).strip() if action_match else "Review notice details and comply accordingly."

        # Entities
        entities = []
        dept_match = re.findall(r'\b(CSE|ECE|MECH|CIVIL|EEE|IT|AI|DS|MBA|MCA)\b', clean_content, re.IGNORECASE)
        if dept_match:
            entities.extend([f"Department: {d.upper()}" for d in set(dept_match)])
        date_match = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b', clean_content, re.IGNORECASE)
        if date_match:
            entities.extend([f"Date: {d}" for d in set(date_match)])

        return {
            "summary": summary,
            "key_points": key_points[:4],
            "required_action": required_action,
            "entities": entities,
            "detected_urgency": "HIGH" if any(w in clean_content.lower() for w in ['urgent', 'immediately', 'critical', 'mandatory']) else "MEDIUM"
        }

    @staticmethod
    def evaluate_content_quality(title, content, category, audience, deadline):
        score = 100
        recommendations = []

        if not title or len(title.strip()) < 10:
            score -= 20
            recommendations.append("Title is too short or missing. Provide a descriptive title of at least 10 characters.")

        if not content or len(content.strip()) < 30:
            score -= 30
            recommendations.append("Notice content is very sparse. Elaborate on requirements, schedule, or instructions.")

        if audience == "ALL" or not audience:
            score -= 5
            recommendations.append("Audience is set to 'ALL'. Consider specifying particular departments or student years for targeted delivery.")

        if not deadline and any(w in (title + " " + content).lower() for w in ['register', 'submit', 'application', 'fee', 'exam', 'drive', 'due']):
            score -= 15
            recommendations.append("Notice implies an action or submission but lacks an explicit deadline date.")

        if not re.search(r'\b(must|should|register|contact|visit|submit|attend|pay)\b', content, re.IGNORECASE):
            score -= 10
            recommendations.append("Action requirement is unclear. Explicitly state what recipient steps are required.")

        if score < 0:
            score = 0

        return {
            "quality_score": score,
            "recommendations": recommendations if recommendations else ["Content is clear, well-structured, and ready for publication."]
        }

    @staticmethod
    def infer_audience(title, content):
        text = (title + " " + content).lower()
        role = "STUDENT"
        if "faculty" in text or "staff" in text or "professor" in text:
            role = "FACULTY"
            
        dept = "ALL"
        for d in ["CSE", "ECE", "MECH", "CIVIL", "EEE", "IT", "AI", "DS"]:
            if re.search(r'\b' + d.lower() + r'\b', text):
                dept = d
                break
                
        year = "ALL"
        if "final year" in text or "4th year" in text or "8th sem" in text:
            year = "FINAL YEAR"
        elif "third year" in text or "3rd year" in text or "6th sem" in text:
            year = "THIRD YEAR"
        elif "second year" in text or "2nd year" in text or "4th sem" in text:
            year = "SECOND YEAR"
        elif "first year" in text or "1st year" in text or "freshman" in text:
            year = "FIRST YEAR"

        suggested_group = f"{dept} {year} {role}S".replace("ALL ALL", "ALL CAMPUS").strip()

        return {
            "suggested_role": role,
            "suggested_department": dept,
            "suggested_year": year,
            "target_group": suggested_group
        }

    @staticmethod
    def determine_priority(title, content, category, deadline, requires_ack):
        text = (title + " " + content).lower()
        
        if category.lower() == "emergency" or "emergency" in text or "evacuation" in text or "suspended" in text:
            return "CRITICAL"
        if "urgent" in text or "immediately" in text or "last date" in text or "today" in text:
            return "URGENT"
        if requires_ack or category.lower() in ["placement", "exam", "fees"] or "mandatory" in text or "deadline" in text:
            return "HIGH"
        if category.lower() in ["academic", "workshop", "scholarship"]:
            return "MEDIUM"
            
        return "LOW"

    @staticmethod
    def detect_deadline(text):
        if not text:
            return {"detected": False, "deadline": None, "confidence": "NONE"}

        text_lower = text.lower()
        today = datetime.now()

        if "today" in text_lower or "by end of day" in text_lower:
            return {"detected": True, "deadline": today.strftime("%Y-%m-%d"), "confidence": "HIGH"}
        if "tomorrow" in text_lower:
            target = today + timedelta(days=1)
            return {"detected": True, "deadline": target.strftime("%Y-%m-%d"), "confidence": "HIGH"}
            
        # Match explicit dates e.g. 2026-09-30 or 30/09/2026 or 30 Sept 2026
        match_iso = re.search(r'\b\d{4}-\d{2}-\d{2}\b', text)
        if match_iso:
            return {"detected": True, "deadline": match_iso.group(0), "confidence": "HIGH"}

        match_slash = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b', text)
        if match_slash:
            day, month, year = match_slash.groups()
            if len(year) == 2:
                year = "20" + year
            try:
                formatted = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                return {"detected": True, "deadline": formatted, "confidence": "HIGH"}
            except ValueError:
                pass

        # Days of week e.g. "by Friday" or "before Friday"
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for idx, day_name in enumerate(weekdays):
            if f"this {day_name}" in text_lower or f"by {day_name}" in text_lower or f"next {day_name}" in text_lower or f"before {day_name}" in text_lower or day_name in text_lower:
                current_day = today.weekday()
                days_ahead = idx - current_day
                if days_ahead <= 0:
                    days_ahead += 7
                target = today + timedelta(days=days_ahead)
                return {"detected": True, "deadline": target.strftime("%Y-%m-%d"), "confidence": "MEDIUM"}


        return {"detected": False, "deadline": None, "confidence": "LOW"}

    @staticmethod
    def detect(text):
        return FallbackAgent.detect_deadline(text)


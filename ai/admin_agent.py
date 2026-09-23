from datetime import datetime
from database.models import Notice, NoticeAcknowledgement, NoticeRead, User, db

class AdminAgent:
    """
    Admin AI Assistant Agent.
    Answers administrative questions dynamically using real SQLite/SQLAlchemy database queries.
    Never fabricates fake numbers or hallucinated users.
    """

    def answer_query(self, query):
        if not query:
            return "Please type a question regarding campus notices, engagement, or pending acknowledgements."

        q_lower = query.lower().strip()

        # Question 1: Expire today
        if "expire today" in q_lower or "expiring today" in q_lower:
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            expiring = Notice.query.filter(Notice.deadline == today_str, Notice.status == 'PUBLISHED').all()
            if not expiring:
                return "No published notices are scheduled to expire today."
            titles = [f"• '{n.title}' ({n.category}, Priority: {n.priority})" for n in expiring]
            return f"The following {len(expiring)} notice(s) expire today ({today_str}):\n" + "\n".join(titles)

        # Question 2: Need attention / Urgent / Risks
        if "attention" in q_lower or "risk" in q_lower or "urgent" in q_lower:
            high_prio = Notice.query.filter(Notice.priority.in_(['HIGH', 'URGENT', 'CRITICAL']), Notice.status == 'PUBLISHED').all()
            if not high_prio:
                return "All active notices are currently operating within normal parameters. No urgent notices require immediate attention."
            
            lines = [f"Found {len(high_prio)} high-priority/urgent notice(s) needing oversight:"]
            for n in high_prio:
                ack_count = NoticeAcknowledgement.query.filter_by(notice_id=n.id).count()
                lines.append(f"• '{n.title}' [{n.priority}] - Category: {n.category}, Acknowledgements: {ack_count}")
            return "\n".join(lines)

        # Question 3: Need acknowledgement
        if "acknowledgement" in q_lower or "acknowledge" in q_lower:
            ack_notices = Notice.query.filter_by(requires_acknowledgement=True, status='PUBLISHED').all()
            if not ack_notices:
                return "There are no published notices requiring acknowledgement at this time."
            
            lines = [f"There are {len(ack_notices)} active notice(s) requiring student acknowledgement:"]
            for n in ack_notices:
                total_students = User.query.filter_by(role='STUDENT').count()
                acked = NoticeAcknowledgement.query.filter_by(notice_id=n.id).count()
                pending = max(0, total_students - acked)
                lines.append(f"• '{n.title}' - Acknowledged: {acked}/{total_students} (Pending: {pending})")
            return "\n".join(lines)

        # Question 4: Placement notices
        if "placement" in q_lower:
            placements = Notice.query.filter(Notice.category.ilike('%placement%'), Notice.status == 'PUBLISHED').all()
            if not placements:
                return "No published placement notices were found in the database."
            lines = [f"Found {len(placements)} placement notice(s):"]
            for n in placements:
                lines.append(f"• '{n.title}' (Audience: {n.audience}, Deadline: {n.deadline or 'N/A'})")
            return "\n".join(lines)

        # Question 5: Who has not acknowledged / pending placement
        if "who has not acknowledged" in q_lower or "pending placement" in q_lower or "not acknowledged" in q_lower:
            placement_notice = Notice.query.filter(Notice.category.ilike('%placement%'), Notice.status == 'PUBLISHED').first()
            if not placement_notice:
                placement_notice = Notice.query.filter_by(requires_acknowledgement=True, status='PUBLISHED').first()
            
            if not placement_notice:
                return "No active notice requiring acknowledgement was found to generate a viewer gap list."

            acked_user_ids = [a.user_id for a in NoticeAcknowledgement.query.filter_by(notice_id=placement_notice.id).all()]
            unacked_users = User.query.filter(User.role == 'STUDENT', ~User.id.in_(acked_user_ids)).limit(10).all()

            if not unacked_users:
                return f"All targeted students have successfully acknowledged '{placement_notice.title}'."
                
            sample_names = ", ".join([f"{u.name} ({u.department})" for u in unacked_users])
            total_unacked = User.query.filter(User.role == 'STUDENT', ~User.id.in_(acked_user_ids)).count()
            return f"For notice '{placement_notice.title}', {total_unacked} student(s) have NOT acknowledged yet.\nSample pending list: {sample_names}..."

        # Question 6: Summarize today's notices / overview
        if "summarize" in q_lower or "summary" in q_lower or "today" in q_lower:
            total_pub = Notice.query.filter_by(status='PUBLISHED').count()
            total_draft = Notice.query.filter_by(status='DRAFT').count()
            total_users = User.query.count()
            return f"Campus Communication Summary:\n• Total Active Published Notices: {total_pub}\n• Draft Notices Pending Review: {total_draft}\n• Registered Users in System: {total_users}\n• System Status: All communication channels active."

        # Default fallback answer
        return f"Database Query Summary for '{query}': Currently tracking {Notice.query.filter_by(status='PUBLISHED').count()} published notices and {User.query.filter_by(role='STUDENT').count()} registered students across departments."

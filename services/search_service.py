from database.models import Notice, NoticeRead, db
from ai.ai_service import AIService

class SearchService:
    """Service handling multi-filter and AI-assisted natural language notice search queries."""

    @staticmethod
    def search_notices(query_text="", category=None, priority=None, department=None, year=None, status="PUBLISHED", current_user=None):
        query = Notice.query

        if status:
            query = query.filter_by(status=status)

        # 1. Natural Language Intent Parsing via AI Search Agent
        ai_intent = {}
        if query_text:
            ai_service = AIService()
            ai_intent = ai_service.parse_search_intent(query_text)

        # Combine explicit UI filters with AI parsed filters
        target_cat = category or ai_intent.get('category')
        target_prio = priority or ai_intent.get('priority')
        requires_ack = ai_intent.get('requires_ack')
        deadline_filter = ai_intent.get('deadline_filter')

        if target_cat and target_cat != 'ALL':
            query = query.filter(Notice.category.ilike(f"%{target_cat}%"))

        if target_prio and target_prio != 'ALL':
            query = query.filter_by(priority=target_prio)

        if department and department != 'ALL':
            query = query.filter((Notice.department == department) | (Notice.department == 'ALL'))

        if year and year != 'ALL':
            query = query.filter((Notice.year == year) | (Notice.year == 'ALL'))

        if requires_ack:
            query = query.filter_by(requires_acknowledgement=True)

        if deadline_filter:
            query = query.filter(Notice.deadline <= deadline_filter)

        # Keyword matching on Title, Content, and Key Points
        if query_text:
            keywords = ai_intent.get('keywords', [query_text.strip()])
            for kw in keywords:
                pattern = f"%{kw}%"
                query = query.filter(
                    (Notice.title.ilike(pattern)) |
                    (Notice.content.ilike(pattern)) |
                    (Notice.key_points.ilike(pattern)) |
                    (Notice.category.ilike(pattern))
                )

        notices = query.order_by(Notice.created_at.desc()).all()

        # Format results with user interaction status if user supplied
        results = []
        user_read_ids = set()
        if current_user:
            user_read_ids = {r.notice_id for r in NoticeRead.query.filter_by(user_id=current_user.id).all()}

        for n in notices:
            n_dict = n.to_dict()
            n_dict['is_read'] = (n.id in user_read_ids) if current_user else False
            results.append(n_dict)

        return {
            'results': results,
            'count': len(results),
            'ai_intent': ai_intent
        }

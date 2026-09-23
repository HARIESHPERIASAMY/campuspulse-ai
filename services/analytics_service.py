from database.models import Notice, NoticeRead, NoticeAcknowledgement, NoticeBookmark, User, QRScan, db
from ai.risk_agent import RiskAgent

class AnalyticsService:
    """Service providing communication funnel analytics, effectiveness scores, viewer details, and risk indicators."""

    @staticmethod
    def get_dashboard_kpis():
        total_notices = Notice.query.count()
        published_notices = Notice.query.filter_by(status='PUBLISHED').count()
        draft_notices = Notice.query.filter_by(status='DRAFT').count()
        urgent_notices = Notice.query.filter(Notice.priority.in_(['URGENT', 'CRITICAL']), Notice.status == 'PUBLISHED').count()
        
        total_students = User.query.filter_by(role='STUDENT').count()
        total_reads = NoticeRead.query.count()
        total_acks = NoticeAcknowledgement.query.count()
        
        return {
            'total_notices': total_notices,
            'published_notices': published_notices,
            'draft_notices': draft_notices,
            'urgent_notices': urgent_notices,
            'total_students': total_students,
            'total_reads': total_reads,
            'total_acknowledgements': total_acks
        }

    @staticmethod
    def get_notice_analytics(notice_id):
        notice = Notice.query.get(notice_id)
        if not notice:
            return None

        # Determine targeted users based on department & year
        query = User.query.filter_by(role='STUDENT')
        if notice.department and notice.department != 'ALL':
            query = query.filter((User.department == notice.department) | (User.department == 'ALL'))
        if notice.year and notice.year != 'ALL':
            query = query.filter((User.year == notice.year) | (User.year == 'ALL'))
            
        targeted_users = query.all()
        targeted_count = len(targeted_users)

        reads = NoticeRead.query.filter_by(notice_id=notice_id).all()
        read_user_ids = {r.user_id for r in reads}
        viewed_count = len(read_user_ids)
        total_views = sum(r.view_count for r in reads) if reads else 0

        acks = NoticeAcknowledgement.query.filter_by(notice_id=notice_id).all()
        acked_user_ids = {a.user_id for a in acks}
        acked_count = len(acked_user_ids)
        pending_ack_count = max(0, targeted_count - acked_count)

        bookmarks_count = NoticeBookmark.query.filter_by(notice_id=notice_id).count()
        qr_scans_count = QRScan.query.filter_by(notice_id=notice_id).count()

        # Metrics rates
        view_rate = round((viewed_count / targeted_count * 100), 1) if targeted_count > 0 else 0.0
        read_rate = view_rate # In single-page web read tracking, viewing = reading initial view
        ack_rate = round((acked_count / targeted_count * 100), 1) if targeted_count > 0 else 0.0

        # Communication Effectiveness Score (Weighted metric)
        if notice.requires_acknowledgement:
            effectiveness_score = round((view_rate * 0.3) + (read_rate * 0.3) + (ack_rate * 0.4), 1)
        else:
            effectiveness_score = round((view_rate * 0.5) + (read_rate * 0.5), 1)

        # Risk Analysis
        risk_agent = RiskAgent()
        risk_assessment = risk_agent.analyze_notice_risk(notice, targeted_count, viewed_count, viewed_count, acked_count)

        return {
            'notice_id': notice.id,
            'title': notice.title,
            'priority': notice.priority,
            'category': notice.category,
            'requires_acknowledgement': notice.requires_acknowledgement,
            'targeted_count': targeted_count,
            'viewed_count': viewed_count,
            'total_views': total_views,
            'read_count': viewed_count,
            'acked_count': acked_count,
            'pending_ack_count': pending_ack_count,
            'bookmarks_count': bookmarks_count,
            'qr_scans_count': qr_scans_count,
            'view_rate': view_rate,
            'read_rate': read_rate,
            'ack_rate': ack_rate,
            'effectiveness_score': effectiveness_score,
            'risk_assessment': risk_assessment
        }

    @staticmethod
    def get_viewer_details(notice_id):
        notice = Notice.query.get(notice_id)
        if not notice:
            return None

        # Target list
        query = User.query.filter_by(role='STUDENT')
        if notice.department and notice.department != 'ALL':
            query = query.filter((User.department == notice.department) | (User.department == 'ALL'))
        if notice.year and notice.year != 'ALL':
            query = query.filter((User.year == notice.year) | (User.year == 'ALL'))
            
        targeted_students = query.order_by(User.name).all()

        reads_map = {r.user_id: r for r in NoticeRead.query.filter_by(notice_id=notice_id).all()}
        acks_map = {a.user_id: a for a in NoticeAcknowledgement.query.filter_by(notice_id=notice_id).all()}

        viewers = []
        for s in targeted_students:
            read = reads_map.get(s.id)
            ack = acks_map.get(s.id)

            if ack:
                status = 'ACKNOWLEDGED'
            elif read:
                status = 'READ'
            else:
                status = 'PENDING'

            viewers.append({
                'user_id': s.id,
                'name': s.name,
                'email': s.email,
                'department': s.department,
                'year': s.year,
                'status': status,
                'first_read_at': read.first_read_at.strftime("%Y-%m-%d %H:%M") if read else None,
                'view_count': read.view_count if read else 0,
                'acknowledged_at': ack.acknowledged_at.strftime("%Y-%m-%d %H:%M") if ack else None
            })

        return {
            'notice': notice.to_dict(),
            'total_targeted': len(targeted_students),
            'total_viewed': len(reads_map),
            'total_acked': len(acks_map),
            'total_pending': len(targeted_students) - len(acks_map),
            'viewers': viewers
        }

    @staticmethod
    def get_aggregate_funnel():
        published = Notice.query.filter_by(status='PUBLISHED').all()
        total_targeted = 0
        total_viewed = 0
        total_read = 0
        total_acked = 0

        for n in published:
            stats = AnalyticsService.get_notice_analytics(n.id)
            if stats:
                total_targeted += stats['targeted_count']
                total_viewed += stats['viewed_count']
                total_read += stats['read_count']
                total_acked += stats['acked_count']

        return {
            'targeted': total_targeted,
            'viewed': total_viewed,
            'read': total_read,
            'acknowledged': total_acked
        }

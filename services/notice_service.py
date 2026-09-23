import json
from datetime import datetime
from database.models import Notice, NoticeRead, NoticeAcknowledgement, NoticeBookmark, Notification, User, AIAnalysis, db
from services.auth_service import AuthService
from services.qr_service import QRService

class NoticeService:
    """Service handling notice lifecycle (CRUD, Publish, Archive), student feeds, read tracking, acknowledgements, and bookmarks."""

    @staticmethod
    def create_notice(creator_id, title, content, category, audience, department, year, priority, deadline, expiry_date, requires_ack, status='DRAFT', ai_data=None):
        notice = Notice(
            title=title.strip(),
            content=content.strip(),
            category=category,
            audience=audience,
            department=department,
            year=year,
            priority=priority,
            deadline=deadline if deadline else None,
            expiry_date=expiry_date if expiry_date else None,
            requires_acknowledgement=bool(requires_ack),
            status=status,
            created_by=creator_id
        )

        if ai_data:
            notice.summary = ai_data.get('summary')
            if isinstance(ai_data.get('key_points'), list):
                notice.key_points = json.dumps(ai_data.get('key_points'))
            else:
                notice.key_points = ai_data.get('key_points')

        db.session.add(notice)
        db.session.commit()

        # Save AI Analysis record if provided
        if ai_data:
            analysis = AIAnalysis(
                notice_id=notice.id,
                summary=ai_data.get('summary'),
                key_points=json.dumps(ai_data.get('key_points')) if isinstance(ai_data.get('key_points'), list) else ai_data.get('key_points'),
                suggested_category=ai_data.get('suggested_category', category),
                suggested_audience=ai_data.get('suggested_audience', audience),
                suggested_priority=ai_data.get('suggested_priority', priority),
                detected_deadline=ai_data.get('detected_deadline', deadline),
                quality_score=ai_data.get('quality_score', 100),
                recommendations=json.dumps(ai_data.get('recommendations')) if isinstance(ai_data.get('recommendations'), list) else ai_data.get('recommendations')
            )
            db.session.add(analysis)
            db.session.commit()

        AuthService.log_audit(creator_id, 'CREATE_NOTICE', notice_id=notice.id, details=f"Created notice '{title}' ({status})")

        if status == 'PUBLISHED':
            NoticeService.post_publish_tasks(notice)

        return notice

    @staticmethod
    def publish_notice(notice_id, admin_id):
        notice = Notice.query.get(notice_id)
        if not notice:
            return None
            
        notice.status = 'PUBLISHED'
        notice.updated_at = datetime.utcnow()
        db.session.commit()

        NoticeService.post_publish_tasks(notice)
        AuthService.log_audit(admin_id, 'PUBLISH_NOTICE', notice_id=notice.id, details=f"Published notice '{notice.title}'")
        return notice

    @staticmethod
    def post_publish_tasks(notice):
        """Generates QR code and dispatches in-app notifications to targeted audience."""
        # 1. Generate QR Code
        QRService.generate_notice_qr(notice.id)

        # 2. Identify Targeted Users & Dispatch Notifications
        query = User.query
        if notice.department and notice.department != 'ALL':
            query = query.filter((User.department == notice.department) | (User.department == 'ALL'))
        if notice.year and notice.year != 'ALL':
            query = query.filter((User.year == notice.year) | (User.year == 'ALL'))
            
        target_users = query.all()

        notif_type = 'EMERGENCY' if notice.priority == 'CRITICAL' else ('URGENT' if notice.priority == 'URGENT' else 'NEW_NOTICE')
        message = f"[{notice.category.upper()}] {notice.title}"
        if notice.priority in ['HIGH', 'URGENT', 'CRITICAL']:
            message = f"🚨 {notice.priority}: {notice.title}"

        for u in target_users:
            notif = Notification(
                user_id=u.id,
                notice_id=notice.id,
                message=message,
                type=notif_type
            )
            db.session.add(notif)
        db.session.commit()

    @staticmethod
    def get_personalized_student_feed(user):
        """Retrieves and prioritizes notices tailored to student department, year, deadline, priority, and unread status."""
        query = Notice.query.filter_by(status='PUBLISHED')

        notices = query.all()
        user_read_ids = {r.notice_id for r in NoticeRead.query.filter_by(user_id=user.id).all()}
        user_acked_ids = {a.notice_id for a in NoticeAcknowledgement.query.filter_by(user_id=user.id).all()}
        user_bookmarked_ids = {b.notice_id for b in NoticeBookmark.query.filter_by(user_id=user.id).all()}

        feed = {
            'important_for_you': [],
            'urgent': [],
            'upcoming_deadlines': [],
            'recent': [],
            'unread': [],
            'bookmarked': []
        }

        priority_order = {'CRITICAL': 5, 'URGENT': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}

        for n in notices:
            # Check target audience match
            dept_match = (n.department == 'ALL' or user.department == 'ALL' or n.department == user.department)
            year_match = (n.year == 'ALL' or user.year == 'ALL' or n.year == user.year)

            if not (dept_match and year_match):
                continue

            n_dict = n.to_dict()
            n_dict['is_read'] = (n.id in user_read_ids)
            n_dict['is_acknowledged'] = (n.id in user_acked_ids)
            n_dict['is_bookmarked'] = (n.id in user_bookmarked_ids)

            # Categorize into feed sections
            if n.priority in ['CRITICAL', 'URGENT']:
                feed['urgent'].append(n_dict)

            if n.deadline:
                feed['upcoming_deadlines'].append(n_dict)

            if not n_dict['is_read']:
                feed['unread'].append(n_dict)

            if n_dict['is_bookmarked']:
                feed['bookmarked'].append(n_dict)

            if (n.priority in ['HIGH', 'URGENT', 'CRITICAL'] or n.requires_acknowledgement) and dept_match:
                feed['important_for_you'].append(n_dict)

            feed['recent'].append(n_dict)

        # Sort feeds
        feed['urgent'].sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        feed['recent'].sort(key=lambda x: x['created_at'] or '', reverse=True)
        feed['important_for_you'].sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)

        return feed

    @staticmethod
    def track_notice_read(notice_id, user_id):
        """Records notice read event. Updates view_count & timestamps without duplicating unique reads."""
        read = NoticeRead.query.filter_by(notice_id=notice_id, user_id=user_id).first()
        now = datetime.utcnow()
        if read:
            read.last_read_at = now
            read.view_count += 1
        else:
            read = NoticeRead(
                notice_id=notice_id,
                user_id=user_id,
                first_read_at=now,
                last_read_at=now,
                view_count=1
            )
            db.session.add(read)
            AuthService.log_audit(user_id, 'READ_NOTICE', notice_id=notice_id, details="User read notice")

        db.session.commit()
        return read

    @staticmethod
    def acknowledge_notice(notice_id, user_id):
        """Records student acknowledgement."""
        ack = NoticeAcknowledgement.query.filter_by(notice_id=notice_id, user_id=user_id).first()
        if not ack:
            ack = NoticeAcknowledgement(
                notice_id=notice_id,
                user_id=user_id,
                acknowledged_at=datetime.utcnow()
            )
            db.session.add(ack)
            db.session.commit()
            AuthService.log_audit(user_id, 'ACKNOWLEDGE_NOTICE', notice_id=notice_id, details="User acknowledged notice")
        return ack

    @staticmethod
    def toggle_bookmark(notice_id, user_id):
        """Toggles notice bookmark state."""
        bookmark = NoticeBookmark.query.filter_by(notice_id=notice_id, user_id=user_id).first()
        if bookmark:
            db.session.delete(bookmark)
            db.session.commit()
            AuthService.log_audit(user_id, 'BOOKMARK_NOTICE', notice_id=notice_id, details="Removed bookmark")
            return False
        else:
            bookmark = NoticeBookmark(notice_id=notice_id, user_id=user_id)
            db.session.add(bookmark)
            db.session.commit()
            AuthService.log_audit(user_id, 'BOOKMARK_NOTICE', notice_id=notice_id, details="Added bookmark")
            return True

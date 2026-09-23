import pytest
from app import create_app
from database.models import db, User, Notice
from services.notice_service import NoticeService
from services.analytics_service import AnalyticsService

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        admin = User(name='Admin', email='admin@test.com', role='ADMIN')
        admin.set_password('pass')
        student1 = User(name='Student 1', email='student1@test.com', role='STUDENT', department='CSE', year='FINAL YEAR')
        student1.set_password('pass')
        student2 = User(name='Student 2', email='student2@test.com', role='STUDENT', department='CSE', year='FINAL YEAR')
        student2.set_password('pass')
        db.session.add_all([admin, student1, student2])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

def test_communication_funnel_and_effectiveness(app):
    with app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        student1 = User.query.filter_by(email='student1@test.com').first()

        notice = NoticeService.create_notice(
            creator_id=admin.id,
            title='Campus Placement Registration',
            content='Register immediately.',
            category='Placement',
            audience='CSE FINAL YEAR',
            department='CSE',
            year='FINAL YEAR',
            priority='HIGH',
            deadline='2026-09-30',
            expiry_date=None,
            requires_ack=True,
            status='PUBLISHED'
        )

        NoticeService.track_notice_read(notice.id, user_id=student1.id)
        NoticeService.acknowledge_notice(notice.id, user_id=student1.id)

        stats = AnalyticsService.get_notice_analytics(notice.id)
        assert stats['targeted_count'] == 2
        assert stats['viewed_count'] == 1
        assert stats['acked_count'] == 1
        assert stats['pending_ack_count'] == 1
        assert stats['effectiveness_score'] > 0

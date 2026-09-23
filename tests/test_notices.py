import pytest
from app import create_app
from database.models import db, User, Notice, NoticeRead, NoticeAcknowledgement
from services.notice_service import NoticeService

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        admin = User(name='Admin', email='admin@test.com', role='ADMIN')
        admin.set_password('pass')
        student = User(name='Student', email='student@test.com', role='STUDENT', department='CSE')
        student.set_password('pass')
        db.session.add_all([admin, student])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

def test_notice_creation_and_publishing(app):
    with app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        notice = NoticeService.create_notice(
            creator_id=admin.id,
            title='Test Placement Drive',
            content='Must register for placement drive by tomorrow.',
            category='Placement',
            audience='CSE FINAL YEAR',
            department='CSE',
            year='FINAL YEAR',
            priority='HIGH',
            deadline='2026-09-30',
            expiry_date=None,
            requires_ack=True,
            status='DRAFT'
        )
        assert notice.id is not None
        assert notice.status == 'DRAFT'

        published = NoticeService.publish_notice(notice.id, admin_id=admin.id)
        assert published.status == 'PUBLISHED'

def test_read_tracking_and_acknowledgement(app):
    with app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        student = User.query.filter_by(email='student@test.com').first()

        notice = NoticeService.create_notice(
            creator_id=admin.id,
            title='Test Mandatory Notice',
            content='Please review instructions.',
            category='General',
            audience='ALL',
            department='ALL',
            year='ALL',
            priority='MEDIUM',
            deadline=None,
            expiry_date=None,
            requires_ack=True,
            status='PUBLISHED'
        )

        read = NoticeService.track_notice_read(notice.id, user_id=student.id)
        assert read.view_count == 1

        # Second view increments view_count without duplicate user read entry
        read2 = NoticeService.track_notice_read(notice.id, user_id=student.id)
        assert read2.view_count == 2
        assert NoticeRead.query.filter_by(notice_id=notice.id, user_id=student.id).count() == 1

        # Acknowledgement
        ack = NoticeService.acknowledge_notice(notice.id, user_id=student.id)
        assert ack.id is not None
        assert NoticeAcknowledgement.query.filter_by(notice_id=notice.id, user_id=student.id).count() == 1

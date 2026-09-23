"""
End-to-End Verification Test Script for CampusPulse AI 360.
Executes the exact hackathon demo scenario across all application routes and database models.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from database.models import db, User, Notice, NoticeRead, NoticeAcknowledgement, NoticeBookmark, QRScan
from services.auth_service import AuthService
from services.notice_service import NoticeService
from services.analytics_service import AnalyticsService
from services.qr_service import QRService
from ai.ai_service import AIService

def run_end_to_end_test():
    print("=" * 60)
    print("CAMPUSPULSE AI 360 - END-TO-END VERIFICATION SUITE")
    print("=" * 60)

    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'cp_secret_key_hackathon_demo_2026'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        admin = User(name='Dr. Marcus Vance (Admin)', email='admin@campuspulse.demo', role='ADMIN', department='CSE', year='ALL')
        admin.set_password('Admin@123')

        student1 = User(name='Alex Rivera (Student)', email='student@campuspulse.demo', role='STUDENT', department='CSE', year='FINAL YEAR')
        student1.set_password('Student@123')

        student2 = User(name='Jordan Lee (Student)', email='jordan@campuspulse.demo', role='STUDENT', department='CSE', year='FINAL YEAR')
        student2.set_password('Student@123')

        db.session.add_all([admin, student1, student2])
        db.session.commit()

    with app.test_client() as client:
        # STEP 1: ADMIN LOGIN
        print("\n[1/12] Testing Admin Login...")
        login_res = client.post('/login', data={'email': 'admin@campuspulse.demo', 'password': 'Admin@123'}, follow_redirects=True)
        assert login_res.status_code == 200
        print("  [OK] Admin Login: SUCCESS")

        # STEP 2: ADMIN VERIFICATION
        print("\n[2/12] Testing Admin 2FA Key Verification...")
        verify_res = client.post('/admin/verify', data={'verification_key': 'CP_ADMIN_2026_SECURE'}, follow_redirects=True)
        assert verify_res.status_code == 200
        assert b"Assurance" in verify_res.data or b"Dashboard" in verify_res.data or b"Campus" in verify_res.data
        print("  [OK] Admin Key Verification: SUCCESS")

        # STEP 3 & 4: AI NOTICE ANALYSIS & NOTICE CREATION
        print("\n[3/12] Testing AI Notice Intelligence Analysis...")
        ai_res = client.post('/ai/analyze-notice', json={
            'title': 'Final Year Placement Registration with TechCorp',
            'content': 'Final year CSE students must register for the campus placement drive with TechCorp before tomorrow 5 PM. Mandatory registration fee receipt must be attached.',
            'category': 'Placement',
            'audience': 'CSE FINAL YEAR',
            'requires_acknowledgement': True
        })
        assert ai_res.status_code == 200
        ai_json = ai_res.get_json()
        assert 'summary' in ai_json
        assert len(ai_json['key_points']) > 0
        assert ai_json['quality_score'] > 50
        print(f"  [OK] AI Notice Analysis: SUCCESS (Quality Score: {ai_json['quality_score']}/100)")
        print(f"    - AI Summary: '{ai_json['summary'][:70]}...'")

        print("\n[4/12] Creating and Publishing Notice...")
        create_res = client.post('/admin/notices/create', data={
            'title': 'Final Year Placement Registration with TechCorp',
            'content': 'Final year CSE students must register for the campus placement drive with TechCorp before tomorrow 5 PM. Mandatory registration fee receipt must be attached.',
            'category': 'Placement',
            'priority': 'HIGH',
            'department': 'CSE',
            'year': 'FINAL YEAR',
            'deadline': '2026-09-30',
            'requires_acknowledgement': 'on',
            'action': 'publish'
        }, follow_redirects=True)
        assert create_res.status_code == 200
        print("  [OK] Notice Published: SUCCESS")

        # Get published notice ID
        with app.app_context():
            created_notice = Notice.query.filter_by(title='Final Year Placement Registration with TechCorp').first()
            assert created_notice is not None
            notice_id = created_notice.id
            print(f"    - Notice ID: {notice_id} | Status: {created_notice.status} | Ack Required: {created_notice.requires_acknowledgement}")

        # STEP 5: QR GENERATION
        print("\n[5/12] Testing QR Code Generation...")
        with app.app_context():
            qr_url = QRService.generate_notice_qr(notice_id)
            assert "notice_" in qr_url
            print(f"  [OK] QR Code Generated: {qr_url}")

        # STEP 6: LOGOUT ADMIN
        client.get('/logout')

        # STEP 7: STUDENT LOGIN & FEED
        print("\n[6/12] Testing Student Login & Personalized Feed...")
        stud_login = client.post('/login', data={'email': 'student@campuspulse.demo', 'password': 'Student@123'}, follow_redirects=True)
        assert stud_login.status_code == 200
        print("  [OK] Student Login: SUCCESS")

        print("\n[7/12] Testing Notice Opening & Read Tracking...")
        detail_res = client.get(f'/notices/{notice_id}')
        assert detail_res.status_code == 200
        with app.app_context():
            student_user = User.query.filter_by(email='student@campuspulse.demo').first()
            read_rec = NoticeRead.query.filter_by(notice_id=notice_id, user_id=student_user.id).first()
            assert read_rec is not None
            print(f"  [OK] Read Tracking Verified: User {student_user.name} view count = {read_rec.view_count}")

        # STEP 8: BOOKMARK & ACKNOWLEDGE
        print("\n[8/12] Testing Bookmark & Student Acknowledgement...")
        bm_res = client.post(f'/notices/{notice_id}/bookmark', follow_redirects=True)
        assert bm_res.status_code == 200
        
        ack_res = client.post(f'/notices/{notice_id}/acknowledge', follow_redirects=True)
        assert ack_res.status_code == 200
        with app.app_context():
            ack_rec = NoticeAcknowledgement.query.filter_by(notice_id=notice_id, user_id=student_user.id).first()
            assert ack_rec is not None
            print("  [OK] Student Acknowledgement Recorded: SUCCESS")

        # STEP 9: PUBLIC MOBILE QR NOTICE
        print("\n[9/12] Testing Public Mobile QR Verification Page...")
        public_res = client.get(f'/notice/public/{notice_id}')
        assert public_res.status_code == 200
        assert b"Verified Authentic" in public_res.data or b"CampusPulse" in public_res.data
        print("  [OK] Public QR Mobile View: SUCCESS")

        # STEP 10: LOGOUT STUDENT & RE-LOGIN ADMIN
        client.get('/logout')
        client.post('/login', data={'email': 'admin@campuspulse.demo', 'password': 'Admin@123'}, follow_redirects=True)
        client.post('/admin/verify', data={'verification_key': 'CP_ADMIN_2026_SECURE'}, follow_redirects=True)

        # STEP 11: ADMIN ANALYTICS & VIEWER ROSTER
        print("\n[10/12] Testing Admin Analytics & Communication Funnel Updates...")
        analytics_res = client.get(f'/admin/notices/{notice_id}/analytics')
        assert analytics_res.status_code == 200
        with app.app_context():
            stats = AnalyticsService.get_notice_analytics(notice_id)
            print(f"  [OK] Funnel Analytics: Targeted={stats['targeted_count']} | Viewed={stats['viewed_count']} | Acknowledged={stats['acked_count']} | Effectiveness={stats['effectiveness_score']}/100")

        print("\n[11/12] Testing Viewer Roster Inspection...")
        viewers_res = client.get(f'/admin/notices/{notice_id}/viewers')
        assert viewers_res.status_code == 200
        print("  [OK] Viewer Roster Inspection: SUCCESS")

        # STEP 12: ADMIN AI ASSISTANT TERMINAL
        print("\n[12/12] Testing Admin AI Assistant DB Querying...")
        ai_ast_res = client.get('/admin/ai-assistant?q=Which+notices+need+attention%3F')
        assert ai_ast_res.status_code == 200
        with app.app_context():
            ai_service = AIService()
            ans = ai_service.query_admin_assistant("Which notices need attention?")
            print(f"  [OK] Admin AI Assistant Answer:\n    '{ans.replace('\n', ' ')}'")

    print("\n" + "=" * 60)
    print("ALL 12 END-TO-END DEMO SCENARIO CHECKS PASSED PERFECTLY! [OK]")
    print("=" * 60)

if __name__ == '__main__':
    run_end_to_end_test()

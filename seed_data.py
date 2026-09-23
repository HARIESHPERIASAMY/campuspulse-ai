import os
import csv
from datetime import datetime
from app import create_app
from database.models import db, User, Notice, NoticeRead, NoticeAcknowledgement, NoticeBookmark, Notification, AuditLog, AIAnalysis
from services.notice_service import NoticeService
from services.qr_service import QRService
from ai.ai_service import AIService
from generate_dataset import generate_synthetic_dataset

def seed_database():
    """Seeds database with demo users, synthetic notices, engagement data, notifications, and pre-generated QR codes."""
    app = create_app()

    with app.app_context():
        print("Resetting database tables...")
        db.drop_all()
        db.create_all()

        print("Creating demo users...")
        demo_users = [
            {'name': 'Dr. Marcus Vance (Admin)', 'email': 'admin@campuspulse.demo', 'role': 'ADMIN', 'dept': 'CSE', 'year': 'ALL', 'pass': 'Admin@123'},
            {'name': 'Alex Rivera (Student)', 'email': 'student@campuspulse.demo', 'role': 'STUDENT', 'dept': 'CSE', 'year': 'FINAL YEAR', 'pass': 'Student@123'},
            {'name': 'Prof. Sarah Jenkins', 'email': 'faculty@campuspulse.demo', 'role': 'FACULTY', 'dept': 'ECE', 'year': 'ALL', 'pass': 'Faculty@123'},
            {'name': 'David Miller (Dean Office)', 'email': 'staff@campuspulse.demo', 'role': 'STAFF', 'dept': 'ALL', 'year': 'ALL', 'pass': 'Staff@123'},
        ]

        user_objects = {}
        for u in demo_users:
            user = User(
                name=u['name'],
                email=u['email'],
                role=u['role'],
                department=u['dept'],
                year=u['year']
            )
            user.set_password(u['pass'])
            db.session.add(user)
            db.session.commit()
            user_objects[u['email']] = user

        # Create 50 synthetic student accounts matching CSV user IDs (IDs 5 to 54)
        depts = ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE', 'IT', 'AI', 'DS']
        years = ['FIRST YEAR', 'SECOND YEAR', 'THIRD YEAR', 'FINAL YEAR']
        for i in range(5, 55):
            student = User(
                id=i,
                name=f"Student User {i}",
                email=f"student{i}@campuspulse.demo",
                role="STUDENT",
                department=depts[i % len(depts)],
                year=years[i % len(years)]
            )
            student.set_password("Student@123")
            db.session.add(student)
        db.session.commit()
        print("Created core demo accounts and 50 student user profiles.")

        # Ensure synthetic dataset CSV files exist
        if not os.path.exists('data/campuspulse_notices.csv') or not os.path.exists('data/campuspulse_engagement.csv'):
            print("Synthetic dataset missing. Running generator...")
            generate_synthetic_dataset()

        # Load Notices from CSV
        print("Seeding notices from synthetic dataset...")
        ai_service = AIService()
        admin_user = user_objects['admin@campuspulse.demo']

        notice_id_map = {}

        with open('data/campuspulse_notices.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                requires_ack = (row['requires_acknowledgement'].upper() == 'TRUE')
                
                # Perform AI Analysis for notice intelligence
                ai_data = ai_service.analyze_full_notice(
                    title=row['title'],
                    content=row['content'],
                    category=row['category'],
                    audience=row['audience'],
                    deadline=row['deadline'],
                    requires_ack=requires_ack
                )

                notice = NoticeService.create_notice(
                    creator_id=admin_user.id,
                    title=row['title'],
                    content=row['content'],
                    category=row['category'],
                    audience=row['audience'],
                    department=row['department'],
                    year=row['year'],
                    priority=row['priority'],
                    deadline=row['deadline'] if row['deadline'] else None,
                    expiry_date=row['expiry_date'] if row['expiry_date'] else None,
                    requires_ack=requires_ack,
                    status=row['status'],
                    ai_data=ai_data
                )
                notice_id_map[int(row['notice_id'])] = notice.id

        print(f"Seeded {len(notice_id_map)} notices with AI intelligence.")

        # Load Engagement from CSV
        print("Seeding student engagement records from dataset...")
        with open('data/campuspulse_engagement.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_n_id = int(row['notice_id'])
                u_id = int(row['user_id'])
                
                real_n_id = notice_id_map.get(raw_n_id)
                if not real_n_id:
                    continue

                if row['viewed'].upper() == 'TRUE':
                    v_time = datetime.strptime(row['viewed_at'], '%Y-%m-%d %H:%M') if row['viewed_at'] else datetime.utcnow()
                    read = NoticeRead(
                        notice_id=real_n_id,
                        user_id=u_id,
                        first_read_at=v_time,
                        last_read_at=v_time,
                        view_count=1
                    )
                    db.session.add(read)

                if row['acknowledged'].upper() == 'TRUE':
                    a_time = datetime.strptime(row['acknowledged_at'], '%Y-%m-%d %H:%M') if row['acknowledged_at'] else datetime.utcnow()
                    ack = NoticeAcknowledgement(
                        notice_id=real_n_id,
                        user_id=u_id,
                        acknowledged_at=a_time
                    )
                    db.session.add(ack)

                if row['bookmarked'].upper() == 'TRUE':
                    bm = NoticeBookmark(
                        notice_id=real_n_id,
                        user_id=u_id
                    )
                    db.session.add(bm)

        db.session.commit()
        print("Seeded student read, acknowledgement, and bookmark records.")

        # Ensure demo student 'student@campuspulse.demo' has explicit engagement on key notice
        demo_student = user_objects['student@campuspulse.demo']
        first_published = Notice.query.filter_by(status='PUBLISHED').first()
        if first_published:
            NoticeService.track_notice_read(first_published.id, demo_student.id)
            NoticeService.acknowledge_notice(first_published.id, demo_student.id)
            NoticeService.toggle_bookmark(first_published.id, demo_student.id)

        print("Database successfully seeded and ready for hackathon demonstration!")

if __name__ == '__main__':
    seed_database()

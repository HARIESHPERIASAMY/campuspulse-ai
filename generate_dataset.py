import os
import csv
import random
from datetime import datetime, timedelta

def generate_synthetic_dataset():
    """Generates synthetic reproducible dataset files: campuspulse_notices.csv (200+ records) and campuspulse_engagement.csv (1000+ records)."""
    os.makedirs('data', exist_ok=True)

    random.seed(42) # Reproducible synthetic generation

    categories = ['Academic', 'Exam', 'Placement', 'Internship', 'Workshop', 'Event', 'Scholarship', 'Fees', 'Sports', 'Club', 'Holiday', 'Infrastructure', 'Emergency', 'General']
    departments = ['CSE', 'ECE', 'MECH', 'CIVIL', 'EEE', 'IT', 'AI', 'DS', 'ALL']
    years = ['FIRST YEAR', 'SECOND YEAR', 'THIRD YEAR', 'FINAL YEAR', 'ALL']
    priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL']
    statuses = ['PUBLISHED', 'PUBLISHED', 'PUBLISHED', 'DRAFT', 'ARCHIVED']

    titles_templates = [
        "Final Year {dept} Placement Drive with TechCorp",
        "Submission of {dept} Semester Project Reports",
        "Mandatory Workshop on Artificial Intelligence for {year} Students",
        "Mid-Term Examination Schedule Released for {dept}",
        "Merit Scholarship Applications Open for {year}",
        "Tuition Fee Payment Deadline Notice",
        "Annual Inter-Departmental Sports Meet Registration",
        "Emergency Maintenance: Power Shutdown in Academic Block B",
        "Guest Lecture on Quantum Computing by Dr. Aris Thorne",
        "Campus Hackathon 2026 Registration Details",
        "Internship Opportunities at Global Tech Labs for {dept}",
        "Library Book Return & Fine Waiver Week",
        "Hostel Mess Committee Meeting Notice",
        "National Level Technical Symposium '{dept} TechPulse 2026'",
        "Notice Regarding Attendance Shortage Rules",
        "IEEE Student Chapter Recruitment Drive",
        "Code of Conduct and Anti-Ragging Mandatory Briefing",
        "Campus Placement Aptitude Training Series",
        "Laboratory Exam Schedule for {dept} {year}",
        "Holiday Announcement: Founder's Day Celebration"
    ]

    base_date = datetime(2026, 9, 1)

    notices = []
    print("Generating 200 synthetic notices...")
    for i in range(1, 205):
        category = random.choice(categories)
        dept = random.choice(departments)
        year = random.choice(years)
        priority = 'CRITICAL' if category == 'Emergency' else random.choice(priorities)
        status = random.choice(statuses)

        template = random.choice(titles_templates)
        title = template.format(dept=dept, year=year)

        days_offset = random.randint(0, 20)
        pub_date = base_date + timedelta(days=days_offset)
        deadline_date = pub_date + timedelta(days=random.randint(2, 14)) if random.random() > 0.3 else None
        expiry_date = (deadline_date + timedelta(days=5)) if deadline_date else (pub_date + timedelta(days=30))

        requires_ack = True if priority in ['HIGH', 'URGENT', 'CRITICAL'] or category in ['Placement', 'Exam', 'Fees'] else random.choice([True, False])

        content = (
            f"Official Notification from Greenfield Institute of Technology.\n\n"
            f"This notice serves to inform all eligible students from {dept} ({year}) regarding '{title}'. "
            f"All concerned individuals must review the guidelines carefully. "
            f"Failure to adhere to the given instructions by {deadline_date.strftime('%Y-%m-%d') if deadline_date else 'the stipulated deadline'} "
            f"may result in administrative restrictions or forfeiture of opportunity.\n\n"
            f"Key Requirements:\n"
            f"1. Complete the mandatory registration form prior to the deadline.\n"
            f"2. Maintain an updated academic profile with the department coordinator.\n"
            f"3. Submit all required documentation directly to the department office.\n\n"
            f"For further inquiries, contact your respective department head or faculty coordinator."
        )

        notices.append({
            'notice_id': i,
            'title': title,
            'content': content,
            'category': category,
            'audience': f"{dept} {year}",
            'department': dept,
            'year': year,
            'priority': priority,
            'publication_date': pub_date.strftime('%Y-%m-%d %H:%M'),
            'deadline': deadline_date.strftime('%Y-%m-%d') if deadline_date else '',
            'expiry_date': expiry_date.strftime('%Y-%m-%d'),
            'requires_acknowledgement': 'TRUE' if requires_ack else 'FALSE',
            'status': status
        })

    # Write notices CSV
    notices_file = os.path.join('data', 'campuspulse_notices.csv')
    with open(notices_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(notices[0].keys()))
        writer.writeheader()
        writer.writerows(notices)
    print(f"Saved {len(notices)} notices to {notices_file}")

    # Generate Engagement CSV
    print("Generating 1000+ synthetic engagement records...")
    engagement = []
    user_ids = list(range(5, 55)) # 50 student user IDs
    published_notice_ids = [n['notice_id'] for n in notices if n['status'] == 'PUBLISHED']

    for n_id in published_notice_ids:
        # Each published notice gets engagement from 15-30 students
        sample_users = random.sample(user_ids, random.randint(15, 30))
        notice_obj = next(n for n in notices if n['notice_id'] == n_id)

        for u_id in sample_users:
            viewed = random.random() > 0.1 # 90% view rate
            viewed_at = ''
            acknowledged = False
            acknowledged_at = ''

            if viewed:
                v_dt = base_date + timedelta(days=random.randint(1, 15), hours=random.randint(8, 18))
                viewed_at = v_dt.strftime('%Y-%m-%d %H:%M')

                if notice_obj['requires_acknowledgement'] == 'TRUE':
                    acknowledged = random.random() > 0.35 # 65% ack rate
                    if acknowledged:
                        a_dt = v_dt + timedelta(minutes=random.randint(5, 120))
                        acknowledged_at = a_dt.strftime('%Y-%m-%d %H:%M')

            bookmarked = random.random() > 0.8
            qr_scanned = random.random() > 0.75

            engagement.append({
                'notice_id': n_id,
                'user_id': u_id,
                'viewed': 'TRUE' if viewed else 'FALSE',
                'viewed_at': viewed_at,
                'acknowledged': 'TRUE' if acknowledged else 'FALSE',
                'acknowledged_at': acknowledged_at,
                'bookmarked': 'TRUE' if bookmarked else 'FALSE',
                'qr_scanned': 'TRUE' if qr_scanned else 'FALSE'
            })

    engagement_file = os.path.join('data', 'campuspulse_engagement.csv')
    with open(engagement_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(engagement[0].keys()))
        writer.writeheader()
        writer.writerows(engagement)
    print(f"Saved {len(engagement)} engagement records to {engagement_file}")

if __name__ == '__main__':
    generate_synthetic_dataset()

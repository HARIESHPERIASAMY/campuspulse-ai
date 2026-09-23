from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='STUDENT') # ADMIN, FACULTY, STAFF, STUDENT
    department = db.Column(db.String(50), nullable=True) # e.g., CSE, ECE, MECH, CIVIL, ALL
    year = db.Column(db.String(20), nullable=True) # e.g., FIRST YEAR, SECOND YEAR, THIRD YEAR, FINAL YEAR, ALL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    notices_created = db.relationship('Notice', backref='author', lazy=True)
    reads = db.relationship('NoticeRead', backref='user', lazy=True, cascade='all, delete-orphan')
    acknowledgements = db.relationship('NoticeAcknowledgement', backref='user', lazy=True, cascade='all, delete-orphan')
    bookmarks = db.relationship('NoticeBookmark', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'department': self.department,
            'year': self.year,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Notice(db.Model):
    __tablename__ = 'notices'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    key_points = db.Column(db.Text, nullable=True) # JSON list or bulleted text
    category = db.Column(db.String(50), nullable=False, default='General')
    audience = db.Column(db.String(100), nullable=False, default='ALL')
    department = db.Column(db.String(50), nullable=False, default='ALL')
    year = db.Column(db.String(50), nullable=False, default='ALL')
    priority = db.Column(db.String(20), nullable=False, default='MEDIUM') # LOW, MEDIUM, HIGH, URGENT, CRITICAL
    deadline = db.Column(db.String(50), nullable=True) # String date representation or ISO
    expiry_date = db.Column(db.String(50), nullable=True)
    requires_acknowledgement = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), nullable=False, default='DRAFT') # DRAFT, PUBLISHED, ARCHIVED, EXPIRED
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reads = db.relationship('NoticeRead', backref='notice', lazy=True, cascade='all, delete-orphan')
    acknowledgements = db.relationship('NoticeAcknowledgement', backref='notice', lazy=True, cascade='all, delete-orphan')
    bookmarks = db.relationship('NoticeBookmark', backref='notice', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='notice', lazy=True, cascade='all, delete-orphan')
    qr_scans = db.relationship('QRScan', backref='notice', lazy=True, cascade='all, delete-orphan')
    ai_analysis = db.relationship('AIAnalysis', backref='notice', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'key_points': self.key_points,
            'category': self.category,
            'audience': self.audience,
            'department': self.department,
            'year': self.year,
            'priority': self.priority,
            'deadline': self.deadline,
            'expiry_date': self.expiry_date,
            'requires_acknowledgement': self.requires_acknowledgement,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class NoticeRead(db.Model):
    __tablename__ = 'notice_reads'

    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_read_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=1)

class NoticeAcknowledgement(db.Model):
    __tablename__ = 'notice_acknowledgements'

    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)

class NoticeBookmark(db.Model):
    __tablename__ = 'notice_bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=True)
    message = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(30), default='NEW_NOTICE') # NEW_NOTICE, URGENT, ACKNOWLEDGEMENT, DEADLINE, EMERGENCY
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QRScan(db.Model):
    __tablename__ = 'qr_scans'

    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    device_type = db.Column(db.String(50), default='Mobile') # Mobile, Desktop, Tablet, Unknown
    session_id = db.Column(db.String(100), nullable=True)

class AIAnalysis(db.Model):
    __tablename__ = 'ai_analysis'

    id = db.Column(db.Integer, primary_key=True)
    notice_id = db.Column(db.Integer, db.ForeignKey('notices.id'), nullable=False)
    summary = db.Column(db.Text, nullable=True)
    key_points = db.Column(db.Text, nullable=True)
    suggested_category = db.Column(db.String(50), nullable=True)
    suggested_audience = db.Column(db.String(100), nullable=True)
    suggested_priority = db.Column(db.String(20), nullable=True)
    detected_deadline = db.Column(db.String(50), nullable=True)
    quality_score = db.Column(db.Integer, default=100)
    recommendations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

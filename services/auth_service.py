from flask import session
from database.models import User, AuditLog, db
from config import Config

class AuthService:
    """Service handling user authentication, role authorization, admin verification, and security audit logs."""

    @staticmethod
    def authenticate_user(email, password):
        user = User.query.filter_by(email=email.strip().lower()).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def login_session(user):
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['user_role'] = user.role
        session['user_dept'] = user.department or 'ALL'
        session['user_year'] = user.year or 'ALL'
        session['admin_verified'] = False

        AuthService.log_audit(user.id, 'LOGIN', details=f"User logged in as {user.role}")

    @staticmethod
    def verify_admin_key(entered_key):
        if entered_key == Config.ADMIN_VERIFICATION_KEY:
            session['admin_verified'] = True
            AuthService.log_audit(session.get('user_id'), 'ADMIN_VERIFICATION', details="Admin verification key validated successfully")
            return True
        return False

    @staticmethod
    def logout_session():
        user_id = session.get('user_id')
        if user_id:
            AuthService.log_audit(user_id, 'LOGOUT', details="User logged out")
        session.clear()

    @staticmethod
    def get_current_user():
        user_id = session.get('user_id')
        if user_id:
            return User.query.get(user_id)
        return None

    @staticmethod
    def is_authenticated():
        return 'user_id' in session

    @staticmethod
    def is_admin():
        return session.get('user_role') == 'ADMIN' and session.get('admin_verified', False)

    @staticmethod
    def log_audit(user_id, action, notice_id=None, details=None):
        try:
            log = AuditLog(
                user_id=user_id,
                action=action,
                notice_id=notice_id,
                details=details
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[AuthService] Audit log error: {e}")

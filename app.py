import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from config import Config
from database.schema import init_db
from database.models import db, User, Notice, NoticeRead, NoticeAcknowledgement, NoticeBookmark, Notification, AuditLog, AIAnalysis, QRScan
from services.auth_service import AuthService
from services.notice_service import NoticeService
from services.analytics_service import AnalyticsService
from services.qr_service import QRService
from services.search_service import SearchService
from ai.ai_service import AIService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)

    # Decorators for authentication and role authorization
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AuthService.is_authenticated():
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not AuthService.is_authenticated():
                flash("Authentication required.", "danger")
                return redirect(url_for('login'))
            if session.get('user_role') != 'ADMIN':
                flash("Access denied. Admin authorization required.", "danger")
                return redirect(url_for('user_dashboard'))
            if not session.get('admin_verified', False):
                flash("Admin security verification required.", "warning")
                return redirect(url_for('admin_verify', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    # Context processors
    @app.context_processor
    def inject_user():
        user = AuthService.get_current_user()
        unread_notif_count = 0
        if user:
            unread_notif_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        return dict(
            current_user=user,
            unread_notif_count=unread_notif_count,
            institution_name=Config.INSTITUTION_NAME
        )

    # Serve generated QR codes statically
    @app.route('/static/generated/qr/<path:filename>')
    def serve_qr(filename):
        return send_from_directory(Config.QR_FOLDER, filename)

    # Authentication Routes
    @app.route('/')
    def index():
        if AuthService.is_authenticated():
            if session.get('user_role') == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            user = AuthService.authenticate_user(email, password)
            if user:
                AuthService.login_session(user)
                flash(f"Welcome back, {user.name}!", "success")
                
                if user.role == 'ADMIN':
                    return redirect(url_for('admin_verify'))
                return redirect(url_for('user_dashboard'))
            else:
                flash("Invalid email or password. Please try again.", "danger")

        return render_template('login.html')

    @app.route('/admin/verify', methods=['GET', 'POST'])
    @login_required
    def admin_verify():
        if session.get('user_role') != 'ADMIN':
            return redirect(url_for('user_dashboard'))

        if session.get('admin_verified', False):
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            verification_key = request.form.get('verification_key')
            if AuthService.verify_admin_key(verification_key):
                flash("Admin security verification successful.", "success")
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin_dashboard'))
            else:
                flash("Invalid Admin Verification Key.", "danger")

        return render_template('admin_verify.html')

    @app.route('/logout')
    def logout():
        AuthService.logout_session()
        flash("You have been logged out.", "info")
        return redirect(url_for('login'))

    # Admin Routes
    @app.route('/admin/dashboard')
    @admin_required
    def admin_dashboard():
        kpis = AnalyticsService.get_dashboard_kpis()
        funnel = AnalyticsService.get_aggregate_funnel()
        recent_notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()

        # Risk Analysis on published notices
        published = Notice.query.filter_by(status='PUBLISHED').all()
        risk_alerts = []
        for n in published:
            analytics = AnalyticsService.get_notice_analytics(n.id)
            if analytics and analytics['risk_assessment']['has_risk']:
                risk_alerts.append({
                    'notice': n,
                    'risk': analytics['risk_assessment']
                })

        return render_template(
            'admin_dashboard.html',
            kpis=kpis,
            funnel=funnel,
            recent_notices=recent_notices,
            risk_alerts=risk_alerts
        )

    @app.route('/admin/notices')
    @admin_required
    def admin_notices():
        status = request.args.get('status', 'ALL')
        query = Notice.query
        if status != 'ALL':
            query = query.filter_by(status=status)
        notices = query.order_by(Notice.created_at.desc()).all()
        return render_template('admin_notices.html', notices=notices, current_status=status)

    @app.route('/admin/notices/create', methods=['GET', 'POST'])
    @admin_required
    def create_notice():
        if request.method == 'POST':
            title = request.form.get('title')
            content = request.form.get('content')
            category = request.form.get('category', 'General')
            audience = request.form.get('audience', 'ALL')
            department = request.form.get('department', 'ALL')
            year = request.form.get('year', 'ALL')
            priority = request.form.get('priority', 'MEDIUM')
            deadline = request.form.get('deadline')
            expiry_date = request.form.get('expiry_date')
            requires_ack = 'requires_acknowledgement' in request.form
            action_button = request.form.get('action') # 'draft' or 'publish'

            status = 'PUBLISHED' if action_button == 'publish' else 'DRAFT'

            # Run AI Analysis
            ai_service = AIService()
            ai_data = ai_service.analyze_full_notice(
                title=title,
                content=content,
                category=category,
                audience=audience,
                deadline=deadline,
                requires_ack=requires_ack
            )

            notice = NoticeService.create_notice(
                creator_id=session['user_id'],
                title=title,
                content=content,
                category=category,
                audience=audience,
                department=department,
                year=year,
                priority=priority,
                deadline=deadline,
                expiry_date=expiry_date,
                requires_ack=requires_ack,
                status=status,
                ai_data=ai_data
            )

            flash(f"Notice '{notice.title}' created successfully ({status}).", "success")
            return redirect(url_for('admin_notices'))

        return render_template('create_notice.html')

    @app.route('/ai/analyze-notice', methods=['POST'])
    @admin_required
    def ai_analyze_notice_ajax():
        data = request.get_json() or {}
        title = data.get('title', '')
        content = data.get('content', '')
        category = data.get('category', 'General')
        audience = data.get('audience', 'ALL')
        deadline = data.get('deadline')
        requires_ack = data.get('requires_acknowledgement', False)

        ai_service = AIService()
        analysis = ai_service.analyze_full_notice(
            title=title,
            content=content,
            category=category,
            audience=audience,
            deadline=deadline,
            requires_ack=requires_ack
        )
        return jsonify(analysis)

    @app.route('/admin/notices/<int:notice_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def edit_notice(notice_id):
        notice = Notice.query.get_or_404(notice_id)
        if request.method == 'POST':
            notice.title = request.form.get('title')
            notice.content = request.form.get('content')
            notice.category = request.form.get('category')
            notice.audience = request.form.get('audience')
            notice.department = request.form.get('department')
            notice.year = request.form.get('year')
            notice.priority = request.form.get('priority')
            notice.deadline = request.form.get('deadline')
            notice.expiry_date = request.form.get('expiry_date')
            notice.requires_acknowledgement = 'requires_acknowledgement' in request.form
            
            db.session.commit()
            AuthService.log_audit(session['user_id'], 'EDIT_NOTICE', notice_id=notice.id, details=f"Edited notice '{notice.title}'")
            flash("Notice updated successfully.", "success")
            return redirect(url_for('admin_notices'))

        return render_template('edit_notice.html', notice=notice)

    @app.route('/admin/notices/<int:notice_id>/publish', methods=['POST'])
    @admin_required
    def publish_notice(notice_id):
        notice = NoticeService.publish_notice(notice_id, session['user_id'])
        if notice:
            flash(f"Notice '{notice.title}' published successfully.", "success")
        return redirect(url_for('admin_notices'))

    @app.route('/admin/notices/<int:notice_id>/archive', methods=['POST'])
    @admin_required
    def archive_notice(notice_id):
        notice = Notice.query.get_or_404(notice_id)
        notice.status = 'ARCHIVED'
        db.session.commit()
        AuthService.log_audit(session['user_id'], 'ARCHIVE_NOTICE', notice_id=notice.id, details=f"Archived notice '{notice.title}'")
        flash(f"Notice '{notice.title}' archived.", "info")
        return redirect(url_for('admin_notices'))

    @app.route('/admin/notices/<int:notice_id>/analytics')
    @admin_required
    def notice_analytics(notice_id):
        analytics = AnalyticsService.get_notice_analytics(notice_id)
        qr_stats = QRService.get_qr_analytics(notice_id)
        if not analytics:
            flash("Notice analytics not found.", "danger")
            return redirect(url_for('admin_notices'))
        return render_template('notice_analytics.html', analytics=analytics, qr_stats=qr_stats)

    @app.route('/admin/notices/<int:notice_id>/viewers')
    @admin_required
    def viewer_details(notice_id):
        viewers_data = AnalyticsService.get_viewer_details(notice_id)
        if not viewers_data:
            flash("Notice not found.", "danger")
            return redirect(url_for('admin_notices'))
        return render_template('viewer_details.html', viewers_data=viewers_data)

    @app.route('/admin/audit')
    @admin_required
    def audit_logs():
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
        return render_template('audit_logs.html', logs=logs)

    @app.route('/admin/ai-assistant', methods=['GET', 'POST'])
    @admin_required
    def admin_ai_assistant():
        query = request.args.get('q') or request.form.get('question') or ""
        answer = None
        if query:
            ai_service = AIService()
            answer = ai_service.query_admin_assistant(query)
            
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'question': query, 'answer': answer})

        return render_template('admin_ai_assistant.html', question=query, answer=answer)

    # Student & User Dashboard Routes
    @app.route('/dashboard')
    @login_required
    def user_dashboard():
        user = AuthService.get_current_user()
        if user.role == 'ADMIN' and session.get('admin_verified', False):
            return redirect(url_for('admin_dashboard'))

        feed = NoticeService.get_personalized_student_feed(user)
        return render_template('user_dashboard.html', feed=feed)

    @app.route('/notices/<int:notice_id>')
    @login_required
    def notice_detail(notice_id):
        user = AuthService.get_current_user()
        notice = Notice.query.get_or_404(notice_id)

        # Track Read Event
        NoticeService.track_notice_read(notice_id, user.id)

        read_record = NoticeRead.query.filter_by(notice_id=notice_id, user_id=user.id).first()
        is_acked = NoticeAcknowledgement.query.filter_by(notice_id=notice_id, user_id=user.id).first() is not None
        is_bookmarked = NoticeBookmark.query.filter_by(notice_id=notice_id, user_id=user.id).first() is not None
        
        qr_code_url = QRService.generate_notice_qr(notice_id)

        return render_template(
            'notice_detail.html',
            notice=notice,
            read_record=read_record,
            is_acked=is_acked,
            is_bookmarked=is_bookmarked,
            qr_code_url=qr_code_url
        )

    @app.route('/notices/<int:notice_id>/acknowledge', methods=['POST'])
    @login_required
    def acknowledge_notice(notice_id):
        user = AuthService.get_current_user()
        NoticeService.acknowledge_notice(notice_id, user.id)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Acknowledged'})
            
        flash("Thank you! Notice acknowledgement recorded.", "success")
        return redirect(url_for('notice_detail', notice_id=notice_id))

    @app.route('/notices/<int:notice_id>/bookmark', methods=['POST'])
    @login_required
    def bookmark_notice(notice_id):
        user = AuthService.get_current_user()
        is_bookmarked = NoticeService.toggle_bookmark(notice_id, user.id)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'bookmarked': is_bookmarked})
            
        flash("Bookmark updated.", "info")
        return redirect(url_for('notice_detail', notice_id=notice_id))

    @app.route('/bookmarks')
    @login_required
    def bookmarks():
        user = AuthService.get_current_user()
        user_bookmarks = NoticeBookmark.query.filter_by(user_id=user.id).all()
        notice_ids = [b.notice_id for b in user_bookmarks]
        notices = Notice.query.filter(Notice.id.in_(notice_ids)).all() if notice_ids else []
        return render_template('bookmarks.html', notices=notices)

    @app.route('/notifications', methods=['GET', 'POST'])
    @login_required
    def notifications():
        user = AuthService.get_current_user()
        if request.method == 'POST':
            # Mark all as read
            Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
            db.session.commit()
            flash("All notifications marked as read.", "success")
            return redirect(url_for('notifications'))

        notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
        return render_template('notifications.html', notifications=notifs)

    @app.route('/search')
    @login_required
    def search():
        query_text = request.args.get('q', '')
        category = request.args.get('category', 'ALL')
        priority = request.args.get('priority', 'ALL')
        department = request.args.get('department', 'ALL')
        
        user = AuthService.get_current_user()
        search_res = SearchService.search_notices(
            query_text=query_text,
            category=category,
            priority=priority,
            department=department,
            current_user=user
        )

        return render_template(
            'search.html',
            query=query_text,
            category=category,
            priority=priority,
            department=department,
            results=search_res['results'],
            count=search_res['count'],
            ai_intent=search_res['ai_intent']
        )

    @app.route('/profile')
    @login_required
    def profile():
        user = AuthService.get_current_user()
        reads_count = NoticeRead.query.filter_by(user_id=user.id).count()
        acks_count = NoticeAcknowledgement.query.filter_by(user_id=user.id).count()
        bookmarks_count = NoticeBookmark.query.filter_by(user_id=user.id).count()

        return render_template(
            'profile.html',
            user=user,
            reads_count=reads_count,
            acks_count=acks_count,
            bookmarks_count=bookmarks_count
        )

    # Public QR Code Target Route (No Login Required)
    @app.route('/notice/public/<int:notice_id>')
    def public_notice(notice_id):
        notice = Notice.query.get_or_404(notice_id)

        # Record public QR scan with session cooldown
        session_id = session.get('qr_session')
        if not session_id:
            session_id = os.urandom(8).hex()
            session['qr_session'] = session_id

        QRService.record_scan(notice_id, request.user_agent.string, session_id)

        return render_template('public_notice.html', notice=notice)

    # Printable Notice Layout
    @app.route('/notice/<int:notice_id>/print')
    @login_required
    def print_notice(notice_id):
        notice = Notice.query.get_or_404(notice_id)
        qr_code_url = QRService.generate_notice_qr(notice_id)
        return render_template('print_notice.html', notice=notice, qr_code_url=qr_code_url)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', code=404, message="Page or Notice Not Found"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('error.html', code=403, message="Access Forbidden"), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', code=500, message="Internal Server Error"), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)

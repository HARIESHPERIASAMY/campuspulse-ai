import os
import qrcode
from datetime import datetime, timedelta
from database.models import QRScan, db
from config import Config

class QRService:
    """Service handling QR code generation, image storage, scan recording with session cooldown."""

    @staticmethod
    def generate_notice_qr(notice_id, base_url="http://127.0.0.1:5000"):
        os.makedirs(Config.QR_FOLDER, exist_ok=True)
        public_url = f"{base_url}/notice/public/{notice_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(public_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#1e293b", back_color="#ffffff")
        file_path = os.path.join(Config.QR_FOLDER, f"notice_{notice_id}.png")
        img.save(file_path)

        return f"/static/generated/qr/notice_{notice_id}.png"

    @staticmethod
    def record_scan(notice_id, user_agent_str, session_id):
        """Records public QR code scan with 5-minute session cooldown to prevent scan count inflation."""
        five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_scan = QRScan.query.filter(
            QRScan.notice_id == notice_id,
            QRScan.session_id == session_id,
            QRScan.scanned_at >= five_mins_ago
        ).first()

        if recent_scan:
            return recent_scan # Cooldown active

        # Device classification
        ua_lower = (user_agent_str or "").lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            device_type = "Mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            device_type = "Tablet"
        else:
            device_type = "Desktop"

        scan = QRScan(
            notice_id=notice_id,
            scanned_at=datetime.utcnow(),
            device_type=device_type,
            session_id=session_id
        )
        db.session.add(scan)
        db.session.commit()

        return scan

    @staticmethod
    def get_qr_analytics(notice_id):
        scans = QRScan.query.filter_by(notice_id=notice_id).all()
        total_scans = len(scans)
        unique_sessions = len({s.session_id for s in scans if s.session_id})

        mobile_count = sum(1 for s in scans if s.device_type == 'Mobile')
        desktop_count = sum(1 for s in scans if s.device_type == 'Desktop')
        tablet_count = sum(1 for s in scans if s.device_type == 'Tablet')

        return {
            'total_scans': total_scans,
            'unique_sessions': unique_sessions,
            'mobile_count': mobile_count,
            'desktop_count': desktop_count,
            'tablet_count': tablet_count,
            'recent_scans': [
                {
                    'scanned_at': s.scanned_at.strftime("%Y-%m-%d %H:%M"),
                    'device_type': s.device_type
                } for s in sorted(scans, key=lambda x: x.scanned_at, reverse=True)[:5]
            ]
        }

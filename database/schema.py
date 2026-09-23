import os
from database.models import db

def init_db(app):
    """Initialize database and ensure instance folder exists."""
    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path, exist_ok=True)
        
    db.init_app(app)
    with app.app_context():
        db.create_all()

def reset_db(app):
    """Drop and recreate all tables."""
    with app.app_context():
        db.drop_all()
        db.create_all()

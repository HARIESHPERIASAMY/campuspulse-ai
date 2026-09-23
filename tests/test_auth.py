import pytest
from app import create_app
from database.models import db, User

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        admin = User(name='Test Admin', email='admin@test.com', role='ADMIN', department='CSE')
        admin.set_password('AdminPass123')
        db.session.add(admin)

        student = User(name='Test Student', email='student@test.com', role='STUDENT', department='CSE')
        student.set_password('StudentPass123')
        db.session.add(student)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_success(client):
    res = client.post('/login', data={'email': 'student@test.com', 'password': 'StudentPass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Personalized Feed" in res.data or b"Welcome back" in res.data or b"Test Student" in res.data

def test_login_failure(client):
    res = client.post('/login', data={'email': 'student@test.com', 'password': 'WrongPassword'}, follow_redirects=True)
    assert b"Invalid email or password" in res.data

def test_admin_verification_flow(client):
    # Step 1: Login as admin -> redirects to admin_verify
    res = client.post('/login', data={'email': 'admin@test.com', 'password': 'AdminPass123'}, follow_redirects=True)
    assert res.status_code == 200

    # Step 2: Provide invalid key
    res = client.post('/admin/verify', data={'verification_key': 'WRONG_KEY'}, follow_redirects=True)
    assert b"Invalid Admin Verification Key" in res.data

    # Step 3: Provide valid key -> Unlocks admin dashboard
    res = client.post('/admin/verify', data={'verification_key': 'CP_ADMIN_2026_SECURE'}, follow_redirects=True)
    assert b"Communication Assurance" in res.data or b"Dashboard" in res.data or b"Notice" in res.data

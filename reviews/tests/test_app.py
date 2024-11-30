import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from reviews.app import app as flask_app
import pytest
from flask import json
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from flask_jwt_extended import create_access_token
from argon2 import PasswordHasher
from unittest.mock import patch
from line_profiler import LineProfiler




ph = PasswordHasher()

@pytest.fixture(scope='session')
def app():
    """
    Creates a Flask application configured for testing.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield flask_app
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope='session')
def client(app):
    """
    Provides a test client for the Flask application.
    """
    return app.test_client()

@pytest.fixture
def db_session():
    """
    Creates a new database session for a test.
    """
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def add_test_data(db_session):
    """
    Adds test data to the database.
    """
    customer = db_session.query(Customer).filter_by(username="testuser").first()
    if not customer:
        customer = Customer(
            fullname="Test User",
            username="testuser",
            age=25,
            address="123 Test St",
            gender="male",
            marital_status="single",
            password=ph.hash("password"),
            role="customer",
            wallet=100.0
        )
        db_session.add(customer)

    item = db_session.query(InventoryItem).filter_by(name="Test Item").first()
    if not item:
        item = InventoryItem(
            id=1,
            name="Test Item",
            category="Electronics",
            price_per_item=50.0,
            stock_count=10
        )
        db_session.add(item)

    review = db_session.query(Review).filter_by(comment="Great product!").first()
    if not review:
        review = Review(
        customer_id=1,
        item_id=1,
        rating=5,
        comment="Great product!",
        status="approved"
    )
    db_session.add(review)


    db_session.commit()

@pytest.fixture
def get_auth_token():
    """
    Creates tokens for authenticated users.
    """
    tokens = {}

    tokens['admin'] = create_access_token(identity=json.dumps({'username': 'admin',"role": "admin"}))

    tokens['user'] = create_access_token(identity=json.dumps({'username': 'user1',"role": "customer"}))

    tokens['manager'] = create_access_token(identity=json.dumps({'username': 'manager1',"role": "product_manager"}))

    return tokens


def test_add_review(client, db_session, get_auth_token, add_test_data):
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  
            "username": username,
        }
        
        response = client.post(
            f'/reviews/{1}',
            headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
            json={
                'rating': 4,
                'comment': 'A new review comment!',
                'status': 'approved'
            }
        )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Review submitted successfully'
    assert 'review_id' in data

    review = db_session.query(Review).filter_by(comment='A new review comment!').first()
    assert review is not None
    assert review.rating == 4
    assert review.comment == 'A new review comment!'
    assert review.status == 'approved'
    assert review.item_id == 1
    assert review.customer_id == 1

def test_submit_review_with_profanity(client, db_session, get_auth_token, add_test_data):
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,
            "username": username,
        }

        response = client.post(
            '/reviews/1',
            json={"rating": 3, "comment": "This is a shit product!"},
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Inappropriate comment detected."

    review = db_session.query(Review).filter_by(comment="This is a badword!").first()
    assert review is None


def test_get_review_by_id(client, db_session, get_auth_token, add_test_data):
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1, 
            "username": username,
        }

        response = client.get(
            '/reviews/1',
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == 1
    assert data['rating'] == 5
    assert data['comment'] == "Great product!"

    review = db_session.query(Review).filter_by(id=1).first()
    assert review is not None
    assert review.rating == 5
    assert review.comment == "Great product!"


def test_get_product_reviews(client, db_session, get_auth_token, add_test_data):
    response = client.get(
        '/reviews/product/1',
        headers={"Authorization": f"Bearer {get_auth_token['user']}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0
    assert data[0]['comment'] == "Great product!"


def test_update_review(client, db_session, get_auth_token, add_test_data):
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1, 
            "username": username,
        }

        response = client.put(
            '/reviews/1',
            json={"rating": 4, "comment": "Updated review comment"},
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Review updated successfully"

    review = db_session.query(Review).filter_by(id=1).first()
    assert review is not None
    assert review.comment == "Updated review comment"
    assert review.rating == 4

def test_delete_review(client, db_session, get_auth_token, add_test_data):
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  
            "username": username,
        }

        response = client.delete(
            f'/reviews/{1}',
            headers={'Authorization': f'Bearer {get_auth_token["admin"]}'}
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == f'Review deleted successfully'

    review = db_session.query(Review).filter_by(id=1).first()
    assert review is None


def test_flag_review(client, db_session, get_auth_token, add_test_data):
    with db_session.begin():
        review = db_session.query(Review).filter_by(id=1).first()
        if not review:
            test_review = Review(
                id=1,
                customer_id=1,
                item_id=1,
                rating=5,
                comment="Great product!",
                status="approved"
            )
            db_session.add(test_review)

    client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
        "id": 1,  
        "username": username,
    }

    response = client.put(
        '/reviews/flag/1',
        headers={"Authorization": f"Bearer {get_auth_token['user']}"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Review 1 flagged successfully"

    flagged_review = db_session.query(Review).filter_by(id=1).first()
    assert flagged_review is not None
    assert flagged_review.status == "flagged"

def test_approve_review(client, db_session, get_auth_token, add_test_data):
    with db_session.begin():
        review = db_session.query(Review).filter_by(id=1).first()
        if not review:
            test_review = Review(
                id=1,
                customer_id=1,
                item_id=1,
                rating=5,
                comment="Great product!",
                status="flagged"  
            )
            db_session.add(test_review)
        else:
            review.status = "flagged"
            db_session.add(review)

    client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
        "id": 1,  
        "username": username,
    }

    response = client.put(
        '/reviews/approve/1',
        headers={"Authorization": f"Bearer {get_auth_token['admin']}"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Review 1 approved successfully"

    approved_review = db_session.query(Review).filter_by(id=1).first()
    assert approved_review is not None
    assert approved_review.status == "approved"

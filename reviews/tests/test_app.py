import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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


# Initialize Password Hasher
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
    # Add test customers
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

    # Add test inventory items
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

    # Add test reviews
    review = db_session.query(Review).filter_by(comment="Great product!").first()
    if not review:
        review = Review(
            id=1,
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


# Test: Add review
def test_add_review(client, db_session, get_auth_token, add_test_data):
    # Mock the `GET_CUSTOMER_DATA_FUNC`
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  # Mocked customer ID
            "username": username,
        }
        
        # Admin adds a new review
        response = client.post(
            f'/reviews/{1}',
            headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
            json={
                'rating': 4,
                'comment': 'A new review comment!',
                'status': 'approved'
            }
        )
    
    # Assertions for the response
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Review submitted successfully'
    assert 'review_id' in data

    # Verify in DB
    review = db_session.query(Review).filter_by(comment='A new review comment!').first()
    assert review is not None
    assert review.rating == 4
    assert review.comment == 'A new review comment!'
    assert review.status == 'approved'
    assert review.item_id == 1
    assert review.customer_id == 1

# Test: Submit a review with profanity
def test_submit_review_with_profanity(client, db_session, get_auth_token, add_test_data):
    # Mock the `GET_CUSTOMER_DATA_FUNC`
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  # Mocked customer ID
            "username": username,
        }

        # Submit a review with profanity
        response = client.post(
            '/reviews/1',
            json={"rating": 3, "comment": "This is a shit product!"},
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    # Assertions for the response
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Inappropriate comment detected."

    # Ensure no review is created in the database
    review = db_session.query(Review).filter_by(comment="This is a badword!").first()
    assert review is None


# Test: Get review by ID
def test_get_review_by_id(client, db_session, get_auth_token, add_test_data):
    # Mock the `GET_CUSTOMER_DATA_FUNC`
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  # Mocked customer ID
            "username": username,
        }

        # Perform the GET request for the review by ID
        response = client.get(
            '/reviews/1',
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    # Assertions for the response
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == 1
    assert data['rating'] == 5
    assert data['comment'] == "Great product!"

    # Verify the review exists in the database
    review = db_session.query(Review).filter_by(id=1).first()
    assert review is not None
    assert review.rating == 5
    assert review.comment == "Great product!"


# Test: Get all reviews for a product
def test_get_product_reviews(client, db_session, get_auth_token, add_test_data):
    response = client.get(
        '/reviews/product/1',
        headers={"Authorization": f"Bearer {get_auth_token['user']}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0
    assert data[0]['comment'] == "Great product!"



# Test: Update a review
def test_update_review(client, db_session, get_auth_token, add_test_data):
    # Mock the `GET_CUSTOMER_DATA_FUNC`
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  # Mocked customer ID
            "username": username,
        }

        # Perform the PUT request to update the review
        response = client.put(
            '/reviews/1',
            json={"rating": 4, "comment": "Updated review comment"},
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    # Assertions for the response
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Review updated successfully"

    # Verify the updated review exists in the database
    review = db_session.query(Review).filter_by(id=1).first()
    assert review is not None
    assert review.comment == "Updated review comment"
    assert review.rating == 4

'''
# Test: Delete a review
def test_delete_review(client, db_session, get_auth_token, add_test_data):
    # Mock the `GET_CUSTOMER_DATA_FUNC` to simulate user validation
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  # Mocked customer ID
            "username": username,
        }

        # Perform the DELETE request for the review
        response = client.delete(
            f'/reviews/{1}',
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    # Assertions for the response
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Review deleted successfully"

    # Verify that the review was deleted in the database
    review = db_session.query(Review).filter_by(id=1).first()
    assert review is None

from unittest.mock import patch

# Test: Flag a review
def test_flag_review(client, db_session, get_auth_token, add_test_data):
    # Mock the `GET_CUSTOMER_DATA_FUNC` for authorization
    with client.application.app_context():
        client.application.config['GET_CUSTOMER_DATA_FUNC'] = lambda username, headers: {
            "id": 1,  # Mocked customer ID
            "username": username,
        }

        # Perform the PUT request to flag the review
        response = client.put(
            '/reviews/flag/1',
            headers={"Authorization": f"Bearer {get_auth_token['user']}"}
        )

    # Assertions for the response
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Review 1 flagged successfully"

    # Verify the flagged status in the database
    review = db_session.query(Review).filter_by(id=1).first()
    assert review is not None
    assert review.status == "flagged"


# Test: Approve a flagged review
def test_approve_review(client, db_session, get_auth_token, add_test_data):
    # First, flag the review
    client.put(
        '/reviews/flag/1',
        headers={"Authorization": f"Bearer {get_auth_token['customer']}"}
    )

    # Approve the flagged review
    response = client.put(
        '/reviews/approve/1',
        headers={"Authorization": f"Bearer {get_auth_token['customer']}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Review 1 approved successfully"
'''
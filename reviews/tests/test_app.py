import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from reviews.app import app as flask_app
import pytest
from flask import json
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.inventory import InventoryItem
from shared.models.customer import Customer
from shared.models.review import Review
import requests
from unittest.mock import patch
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Set up the database for testing
    Base.metadata.create_all(bind=engine)
    yield flask_app
    # Teardown the database after testing
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def db_session():
    """Create a new database session for a test."""
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def auth_header(username='testuser'):
    """Generate an authentication header with JWT token."""
    access_token = create_access_token(identity=json.dumps({'username': username}))
    return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def setup_test_data(db_session):
    """Add a customer and an inventory item to the database."""
    # Add a customer
    customer = Customer(
        fullname='Test User',
        username='testuser',
        password='password123',
        age=30,
        address='123 Test St',
        gender='male',
        marital_status='single'
    )
    db_session.add(customer)
    db_session.commit()

    # Add an inventory item
    item = InventoryItem(
        name='Test Item',
        category='electronics',
        price_per_item=99.99,
        description='A test item.',
        stock_count=10
    )
    db_session.add(item)
    db_session.commit()

    return customer, item

@pytest.fixture
def mock_get_customer_data(app, setup_test_data,auth_header):
    """Inject a mock function to get customer data without external requests."""
    customer, _ = setup_test_data

    def mock_get_customer_data(username):
        if username == customer.username:
            return {
                'id': customer.id,
                'fullname': customer.fullname,
                'username': customer.username,
                'age': customer.age,
                'address': customer.address,
                'gender': customer.gender,
                'marital_status': customer.marital_status,
                'wallet': customer.wallet
            }
        else:
            raise Exception('Customer not found')

    app.config['GET_CUSTOMER_DATA_FUNC'] = mock_get_customer_data

def test_submit_review(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test submitting a new review."""
    _, item = setup_test_data

    review_data = {
        'rating': 5,
        'comment': 'Excellent product!',
        'status': 'approved'
    }

    response = client.post(
        f'/reviews/{item.id}',
        json=review_data,
        headers=auth_header
    )
    assert response.status_code == 201
    assert 'review_id' in response.json

def test_submit_review_invalid_data(client, auth_header, setup_test_data, mock_get_customer_data):
    """Test submitting a review with invalid data."""
    _, item = setup_test_data

    review_data = {
        'rating': 6,  # Invalid rating
        'comment': 'Great!',
        'status': 'approved'
    }

    response = client.post(
        f'/reviews/{item.id}',
        json=review_data,
        headers=auth_header
    )
    assert response.status_code == 400
    assert "Invalid rating" in response.json['error']

def test_get_review_details(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test retrieving review details."""
    customer, item = setup_test_data

    # Add a review
    review = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=4,
        comment='Good product.',
        status='approved'
    )
    db_session.add(review)
    db_session.commit()

    response = client.get(f'/reviews/{review.id}', headers=auth_header)
    assert response.status_code == 200
    assert response.json['rating'] == 4

def test_get_review_details_not_found(client, auth_header, mock_get_customer_data):
    """Test retrieving a non-existent review."""
    response = client.get('/reviews/999', headers=auth_header)
    assert response.status_code == 404
    assert response.json['error'] == 'Review not found'

def test_get_customer_reviews(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test retrieving all reviews submitted by a customer."""
    customer, item = setup_test_data

    # Add reviews
    review1 = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=5,
        comment='Fantastic!',
        status='approved'
    )
    review2 = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=3,
        comment='Average product.',
        status='approved'
    )
    db_session.add_all([review1, review2])
    db_session.commit()

    response = client.get('/reviews/customer/', headers=auth_header)
    assert response.status_code == 200
    assert len(response.json) == 2

def test_get_product_reviews(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test retrieving all reviews for a specific product."""
    customer, item = setup_test_data

    # Add reviews
    review1 = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=4,
        comment='Good value.',
        status='approved'
    )
    db_session.add(review1)
    db_session.commit()

    response = client.get(f'/reviews/product/{item.id}', headers=auth_header)
    assert response.status_code == 200
    assert len(response.json) == 1

def test_update_review(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test updating an existing review."""
    customer, item = setup_test_data

    # Add a review
    review = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=3,
        comment='It is okay.',
        status='approved'
    )
    db_session.add(review)
    db_session.commit()

    updated_data = {
        'rating': 4,
        'comment': 'Actually, it is good.'
    }

    response = client.put(f'/reviews/{review.id}', json=updated_data, headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == 'Review updated successfully'

def test_update_review_invalid_user(client, db_session, setup_test_data, mock_get_customer_data):
    """Test updating a review by a different user."""
    customer, item = setup_test_data

    # Add another customer
    other_customer = Customer(
        fullname='Other User',
        username='otheruser',
        password='password123',
        age=25,
        address='456 Other St',
        gender='female',
        marital_status='single'
    )
    db_session.add(other_customer)
    db_session.commit()

    # Update mock function to include other user
    def mock_get_customer_data(username):
        if username == customer.username:
            return {
                'id': customer.id,
                'fullname': customer.fullname,
                'username': customer.username,
                'age': customer.age,
                'address': customer.address,
                'gender': customer.gender,
                'marital_status': customer.marital_status,
                'wallet': customer.wallet
            }
        elif username == other_customer.username:
            return {
                'id': other_customer.id,
                'fullname': other_customer.fullname,
                'username': other_customer.username,
                'age': other_customer.age,
                'address': other_customer.address,
                'gender': other_customer.gender,
                'marital_status': other_customer.marital_status,
                'wallet': other_customer.wallet
            }
        else:
            raise Exception('Customer not found')

    flask_app.config['GET_CUSTOMER_DATA_FUNC'] = mock_get_customer_data

    # Add a review by the first customer
    review = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=2,
        comment='Not great.',
        status='approved'
    )
    db_session.add(review)
    db_session.commit()

    # Auth header for the other user
    access_token = create_access_token(identity=json.dumps({'username': 'otheruser'}))
    auth_header_other = {'Authorization': f'Bearer {access_token}'}

    updated_data = {
        'rating': 5,
        'comment': 'Changed my mind.'
    }

    response = client.put(f'/reviews/{review.id}', json=updated_data, headers=auth_header_other)
    assert response.status_code == 400
    assert response.json['error'] == 'User cannot update this review'

def test_delete_review(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test deleting a review."""
    customer, item = setup_test_data

    # Add a review
    review = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=1,
        comment='Bad product.',
        status='approved'
    )
    db_session.add(review)
    db_session.commit()

    response = client.delete(f'/reviews/{review.id}', headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == 'Review deleted successfully'

def test_delete_review_invalid_user(client, db_session, setup_test_data, mock_get_customer_data):
    """Test deleting a review by a different user."""
    customer, item = setup_test_data

    # Add another customer
    other_customer = Customer(
        fullname='Other User',
        username='otheruser',
        password='password123',
        age=25,
        address='456 Other St',
        gender='female',
        marital_status='single'
    )
    db_session.add(other_customer)
    db_session.commit()

    # Update mock function to include other user
    def mock_get_customer_data(username):
        if username == customer.username:
            return {
                'id': customer.id,
                'fullname': customer.fullname,
                'username': customer.username,
                'age': customer.age,
                'address': customer.address,
                'gender': customer.gender,
                'marital_status': customer.marital_status,
                'wallet': customer.wallet
            }
        elif username == other_customer.username:
            return {
                'id': other_customer.id,
                'fullname': other_customer.fullname,
                'username': other_customer.username,
                'age': other_customer.age,
                'address': other_customer.address,
                'gender': other_customer.gender,
                'marital_status': other_customer.marital_status,
                'wallet': other_customer.wallet
            }
        else:
            raise Exception('Customer not found')

    flask_app.config['GET_CUSTOMER_DATA_FUNC'] = mock_get_customer_data

    # Add a review by the first customer
    review = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=2,
        comment='Not great.',
        status='approved'
    )
    db_session.add(review)
    db_session.commit()

    # Auth header for the other user
    access_token = create_access_token(identity=json.dumps({'username': 'otheruser'}))
    auth_header_other = {'Authorization': f'Bearer {access_token}'}

    response = client.delete(f'/reviews/{review.id}', headers=auth_header_other)
    assert response.status_code == 400
    assert response.json['error'] == 'User cannot delete this review'

def test_flag_review(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test flagging a review."""
    customer, item = setup_test_data

    # Add a review
    review = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=3,
        comment='Average.',
        status='normal'
    )
    db_session.add(review)
    db_session.commit()

    response = client.put(f'/reviews/flag/{review.id}', headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == f'Review {review.id} flagged successfully'

def test_approve_review(client, auth_header, db_session, setup_test_data, mock_get_customer_data):
    """Test approving a flagged review."""
    customer, item = setup_test_data

    # Add a flagged review
    review = Review(
        customer_id=customer.id,
        item_id=item.id,
        rating=3,
        comment='Average.',
        status='flagged'
    )
    db_session.add(review)
    db_session.commit()

    response = client.put(f'/reviews/approve/{review.id}', headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == f'Review {review.id} approved successfully'

def test_validate_data_missing_field():
    """Test review data validation with missing required field."""
    data = {
        # 'rating' is missing
        'comment': 'Nice product.',
        'status': 'approved'
    }
    is_valid, message = Review.validate_data(data)
    assert not is_valid
    assert message == "'rating' is a required field."

def test_validate_data_invalid_rating():
    """Test review data validation with invalid rating."""
    data = {
        'rating': 6,  # Invalid rating
        'comment': 'Too good to be true.',
        'status': 'approved'
    }
    is_valid, message = Review.validate_data(data)
    assert not is_valid
    assert "Invalid rating" in message

def test_validate_data_invalid_status():
    """Test review data validation with invalid status."""
    data = {
        'rating': 4,
        'comment': 'Good.',
        'status': 'unknown'  # Invalid status
    }
    is_valid, message = Review.validate_data(data)
    assert not is_valid
    assert "Invalid status" in message

def test_validate_data_invalid_comment():
    """Test review data validation with invalid comment."""
    data = {
        'rating': 4,
        'comment': 12345,  # Comment should be a string or null
        'status': 'approved'
    }
    is_valid, message = Review.validate_data(data)
    assert not is_valid
    assert "Invalid comment" in message

def test_validate_data_valid():
    """Test review data validation with valid data."""
    data = {
        'rating': 5,
        'comment': 'Excellent!',
        'status': 'approved'
    }
    is_valid, message = Review.validate_data(data)
    assert is_valid
    assert message == "Validation successful."
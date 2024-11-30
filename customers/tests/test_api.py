import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from customers.app import app as flask_app
import pytest
from flask import json
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.models.order import Order
from shared.models.wishlist import Wishlist
from flask_jwt_extended import create_access_token
from argon2 import PasswordHasher

# Initialize Password Hasher
ph = PasswordHasher()

@pytest.fixture(scope='session')
def app():
    """
    Creates a Flask application configured for testing.
    """
    # Create the database and the database tables
    Base.metadata.create_all(bind=engine)
    yield flask_app
    # Teardown: Drop all tables
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
def add_default_admin(db_session):
    """
    Adds a default admin user to the database.
    """
    admin = Customer(
        fullname="Admin User",
        username="admin",
        age=30,
        address="123 Admin St",
        gender="male",
        marital_status="single",
        password=ph.hash("admin123"),
        role="admin",
        wallet=1000.0
    )
    db_session.add(admin)
    db_session.commit()
    return admin

@pytest.fixture
def add_regular_user(db_session):
    """
    Adds a regular customer user to the database.
    """
    user = Customer(
        fullname="Regular User",
        username="user1",
        age=25,
        address="456 User Ave",
        gender="female",
        marital_status="married",
        password=ph.hash("userpass"),
        role="customer",
        wallet=500.0
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def get_auth_token(client):
    """
    Logs in both admin and regular user to obtain JWT tokens.
    Returns a dictionary with 'admin' and 'user' tokens.
    """
    tokens = {}

    tokens['admin'] = create_access_token(identity=json.dumps({'username': 'admin',"role": "admin"}))

    tokens['user'] = create_access_token(identity=json.dumps({'username': 'user1',"role": "customer"}))

    return tokens

# Test: Get all customers
def test_get_customers(client, db_session, get_auth_token, add_default_admin, add_regular_user):
    response = client.get(
        '/customers',
        headers={'Authorization': f'Bearer {get_auth_token["admin"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2  # Only admin exists initially
    assert data[0]['username'] == 'admin'

# Test: Get customer by username
def test_get_customer_by_username(client, db_session, get_auth_token):
    # Admin accessing another user's data
    response = client.get(
        '/customers/user1',
        headers={'Authorization': f'Bearer {get_auth_token["admin"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'user1'

    # Regular user accessing their own data
    response = client.get(
        '/customers/user1',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'user1'

# Test: Get customer by username (No User)
def test_get_customer_by_username_no_user(client, db_session, get_auth_token):
    response = client.get(
        '/customers/nonexistent',
        headers={'Authorization': f'Bearer {get_auth_token["admin"]}'}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Customer not found'

# Test: Add customer
def test_add_customer(client, db_session):
    response = client.post('/customers', json={
        'fullname': 'New User',
        'username': 'newuser',
        'password': 'newpass123',
        'age': 28,
        'address': '789 New Rd',
        'gender': 'other',
        'marital_status': 'single'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Customer added successfully'
    assert 'customer_id' in data

    # Verify in DB
    customer = db_session.query(Customer).filter_by(username='newuser').first()
    assert customer is not None
    assert customer.fullname == 'New User'

# Test: Add customer with invalid data
def test_add_customer_invalid_data(client, db_session):
    # Missing required fields
    response = client.post('/customers', json={
        'fullname': 'No Username',
        # 'username' is missing
        'password': 'pass123',
        'age': 20,
        'address': 'No Username St',
        'gender': 'male',
        'marital_status': 'single'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "'username' is a required field."

    # Invalid age
    response = client.post('/customers', json={
        'fullname': 'Young User',
        'username': 'younguser',
        'password': 'pass123',
        'age': 15,  # Invalid age
        'address': 'Young St',
        'gender': 'female',
        'marital_status': 'single'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Invalid value for 'age'. It must be greater than 16."

# Test: Update customer
def test_update_customer(client, db_session, get_auth_token):
    response = client.put(
        '/customers/user1',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={
            'fullname': 'Updated User',
            'age': 26,
            'address': 'Updated Address',
            'gender': 'female',
            'marital_status': 'married'
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Customer user1 updated successfully'

    # Verify in DB
    customer = db_session.query(Customer).filter_by(username='user1').first()
    assert customer.fullname == 'Updated User'
    assert customer.age == 26
    assert customer.address == 'Updated Address'
    assert customer.marital_status == 'married'

# Test: Update customer with invalid data
def test_update_customer_invalid_data(client, db_session, get_auth_token):
    # Invalid gender
    response = client.put(
        '/customers/user1',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={
            'fullname': 'User',
            'age': 25,
            'address': 'User Address',
            'gender': 'invalid_gender',  # Invalid gender
            'marital_status': 'single'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid value for 'gender'" in data['error']

    # Invalid age
    response = client.put(
        '/customers/user1',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={
            'fullname': 'User',
            'age': 10,  # Invalid age
            'address': 'User Address',
            'gender': 'male',
            'marital_status': 'single'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid value for 'age'" in data['error']

# Test: Update customer with invalid user
def test_update_customer_invalid_user(client, db_session, get_auth_token):
    # Regular user trying to update another user's data
    response = client.put(
        '/customers/admin',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={
            'fullname': 'Hacked Admin',
            'age': 35,
            'address': 'Hacked Address',
            'gender': 'male',
            'marital_status': 'married'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid user'

# Test: Change password
def test_change_password(client, db_session, get_auth_token):
    response = client.post(
        '/customers/user1/change-password',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={
            'current_password': 'userpass',
            'new_password': 'newuserpass'
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Password changed successfully'

# Test: Change password with invalid current password
def test_change_password_invalid_password(client, db_session, get_auth_token):
    response = client.post(
        '/customers/user1/change-password',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={
            'current_password': 'newuserpass',
            'new_password': 'bad'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid value for new password. It must be at least 6 characters'

# Test: Delete customer
def test_delete_customer(client, db_session, get_auth_token):
    response = client.delete(
        '/customers/user1',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Customer user1 deleted successfully'

    # Verify deletion in DB
    customer = db_session.query(Customer).filter_by(username='user1').first()
    assert customer is None

# Test: Delete customer (No User)
def test_delete_customer_no_user(client, db_session, get_auth_token):
    response = client.delete(
        '/customers/user1',
        headers={'Authorization': f'Bearer {get_auth_token["admin"]}'}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Customer not found'

# Test: Deduct wallet
def test_deduct_wallet(client, db_session, get_auth_token, add_regular_user):
    response = client.post(
        '/customers/user1/wallet/deduct',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={'amount': 100.0}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Deducted $100.0 from user1's wallet"
    assert data['new_balance'] == 400.0

# Test: Deduct wallet with bad amount
def test_deduct_wallet_bad_amount(client, db_session, get_auth_token):
    response = client.post(
        '/customers/user1/wallet/deduct',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={'amount': -50.0}  # Invalid amount
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid amount'

# Test: Deduct wallet with insufficient balance
def test_deduct_wallet_insufficient(client, db_session, get_auth_token):
    response = client.post(
        '/customers/user1/wallet/deduct',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={'amount': 1000.0}  # Exceeds current wallet
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Insufficient balance'

# Test: Add wallet
def test_add_wallet(client, db_session, get_auth_token):
    response = client.post(
        '/customers/user1/wallet/add',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={'amount': 200.0}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == "Added $200.0 to user1's wallet"
    assert data['new_balance'] == 600.0

# Test: Add wallet with bad amount
def test_add_wallet_bad_amount(client, db_session, get_auth_token):
    response = client.post(
        '/customers/user1/wallet/add',
        headers={'Authorization': f'Bearer {get_auth_token["user"]}'},
        json={'amount': -100.0}  # Invalid amount
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid amount'

# Test: Add product manager role
def test_add_product_manager_role(client, db_session, get_auth_token):
    response = client.post(
        '/customers/add-role',
        headers={'Authorization': f'Bearer {get_auth_token["admin"]}'},
        json={
            'fullname': 'Product Manager',
            'username': 'pm_user',
            'password': 'pmpass123',
            'age': 35,
            'address': '789 PM Blvd',
            'gender': 'female',
            'marital_status': 'married',
            'role': 'product_manager'
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'New user added successfully'
    assert 'customer_id' in data

    # Verify in DB
    pm_user = db_session.query(Customer).filter_by(username='pm_user').first()
    assert pm_user is not None
    assert pm_user.role == 'product_manager'

# Test: Get previous orders
def test_get_previous_orders(client, db_session, get_auth_token):
    # Add an order for user1
    item = InventoryItem(name="apple",category="food",price_per_item=1,stock_count=10)

    order = Order(
        customer_id=1,
        item_id=1,  
        quantity=2
    )
    db_session.add(item)
    db_session.add(order)
    db_session.commit()

    response = client.get(
        '/customers/admin/orders',
        headers={'Authorization': f'Bearer {get_auth_token["admin"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    print(data)
    assert 'orders' in data
    assert len(data['orders']) == 1
    assert data['orders'][0]['quantity'] == 2

# Test: Get wishlist
def test_get_wishlist(client, db_session, get_auth_token):
    # Add a wishlist item for admin
    wishlist_item = Wishlist(
        customer_id=1,
        item_id=1  
    )
    db_session.add(wishlist_item)
    db_session.commit()

    response = client.get(
        '/customers/admin/wishlist',
        headers={'Authorization': f'Bearer {get_auth_token["admin"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'wishlist' in data
    assert len(data['wishlist']) == 1
    assert data['wishlist'][0]['item_id'] == 1

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from flask import json
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.models.order import Order
from shared.models.wishlist import Wishlist
from inventory.app import app as flask_app
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
def add_inventory_item(db_session):
    """
    Adds an inventory item to the database.
    """
    item = InventoryItem(
        name="Apple",
        description="An expensive apple",
        price_per_item=50.0,
        stock_count=100,
        category="food"
    )
    db_session.add(item)
    db_session.commit()
    return item

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
def add_product_manager(db_session):
    """
    Adds a product manager user to the database.
    """
    user = Customer(
        fullname="Product Manager User",
        username="manager1",
        age=25,
        address="456 User Ave",
        gender="female",
        marital_status="married",
        password=ph.hash("userpass"),
        role="product_manager",
        wallet=500.0
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def get_auth_tokens(client):
    """
    Logs in all users to obtain JWT tokens.
    Returns a dictionary with 'admin', 'user', and manager tokens.
    """
    tokens = {}

    tokens['admin'] = create_access_token(identity=json.dumps({'username': 'admin',"role": "admin"}))

    tokens['user'] = create_access_token(identity=json.dumps({'username': 'user1',"role": "customer"}))

    tokens['manager'] = create_access_token(identity=json.dumps({'username': 'manager1',"role": "product_manager"}))

    return tokens

# Test: Add item
def test_add_item(client, db_session, get_auth_tokens):
    # Admin adds a new item
    response = client.post(
        '/inventory',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={
            'name': 'New Product',
            'description': 'A new product description',
            'price_per_item': 99.99,
            'stock_count': 50,
            'category': 'electronics'
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Good added successfully'
    assert 'item_id' in data

    # Verify in DB
    item = db_session.query(InventoryItem).filter_by(name='New Product').first()
    assert item is not None
    assert item.description == 'A new product description'
    assert item.price_per_item == 99.99
    assert item.stock_count == 50
    assert item.category == 'electronics'

# Test: Add item with invalid data
def test_add_item_invalid_data(client, db_session, get_auth_tokens):
    # Missing required fields
    response = client.post(
        '/inventory',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={
            'name': 'Incomplete Product',
            'stock_count': 30,
            'category': 'books'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "'price_per_item' is a required field."

    # Invalid price_per_item (negative)
    response = client.post(
        '/inventory',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={
            'name': 'Negative Price Product',
            'description': 'Product with negative price',
            'price_per_item': 10.0,
            'stock_count': 10,
            'category': 'gadgets'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid value for 'category'. Valid options are: food, clothes, accessories, electronics." in data['error']

# Test: Add item with bad role
def test_add_item_bad_role(client, db_session, get_auth_tokens):
    # Regular user attempts to add an item
    response = client.post(
        '/inventory',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={
            'name': 'Unauthorized Product',
            'description': 'Should not be added',
            'price_per_item': 59.99,
            'stock_count': 20,
            'category': 'accessories'
        }
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data['error'] == 'Permission denied: Insufficient role'

# Test: Update item
def test_update_item(client, db_session, get_auth_tokens):
    # Admin updates the item
    response = client.put(
        f'/inventory/{1}',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={
            'name': 'Updated Test Item',
            'description': 'Updated description',
            'price_per_item': 75.0,
            'stock_count': 80,
            'category': 'food'
        }
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == f'Item {1} updated successfully'

    # Verify in DB
    item = db_session.query(InventoryItem).filter_by(id=1).first()
    assert item.name == 'Updated Test Item'
    assert item.description == 'Updated description'
    assert item.price_per_item == 75.0
    assert item.stock_count == 80
    assert item.category == 'food'

# Test: Update item with invalid data
def test_update_item_invalid_data(client, db_session, get_auth_tokens):
    # Invalid stock_count (negative)
    response = client.put(
        f'/inventory/{1}',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={
            'stock_count': -20
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "'name' is a required field." in data['error']

    # Invalid price_per_item (non-float)
    response = client.put(
        f'/inventory/{1}',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={
            'name': 'Updated Test Item',
            'description': 'Updated description',
            'price_per_item': 20,
            'stock_count': -20,
            'category': 'food'
        }
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid value for 'stock_count'" in data['error']

# Test: Update item that does not exist
def test_update_item_no_item(client, db_session, get_auth_tokens):
    response = client.put(
        '/inventory/9999',  # Assuming this ID does not exist
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={
            'name': 'Nonexistent Item',
            'description': 'Should not be updated',
            'price_per_item': 100.0,
            'stock_count': 10,
            'category': 'none'
        }
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Item not found'

# Test: Delete item
def test_delete_item(client, db_session, get_auth_tokens):
    # Admin deletes the item
    response = client.delete(
        f'/inventory/{1}',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == f'Item {1} deleted successfully'

    # Verify deletion in DB
    item = db_session.query(InventoryItem).filter_by(id=1).first()
    assert item is None

# Test: Delete item that does not exist
def test_delete_item_no_item(client, db_session, get_auth_tokens):
    response = client.delete(
        '/inventory/9999',  # Assuming this ID does not exist
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Item not found'

# Test: Delete item with bad role
def test_delete_item_bad_role(client, db_session, get_auth_tokens, add_inventory_item):
    # Regular user attempts to delete an item
    response = client.delete(
        f'/inventory/{add_inventory_item.id}',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'}
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data['error'] == 'Permission denied: Insufficient role'

# Test: Remove stock
def test_remove_stock(client, db_session, get_auth_tokens):
    # Add stock to ensure sufficient quantity

    # Deduct 20 items
    response = client.post(
        f'/inventory/{2}/stock/remove',
        headers={'Authorization': f'Bearer {get_auth_tokens["manager"]}'},
        json={'quantity': 20}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == '20 items deducted from stock'
    assert data['new_stock'] == 30

    # Verify in DB
    item = db_session.query(InventoryItem).filter_by(id=2).first()
    assert item.stock_count == 30

# Test: Remove stock with bad quantity
def test_remove_stock_bad_quantity(client, db_session, get_auth_tokens):
    # Attempt to deduct negative quantity
    response = client.post(
        f'/inventory/{2}/stock/remove',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={'quantity': -10}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid quantity. Must be a positive integer.'

    # Attempt to deduct non-integer quantity
    response = client.post(
        f'/inventory/{2}/stock/remove',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={'quantity': 'ten'}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid quantity. Must be a positive integer.'

# Test: Remove stock with insufficient quantity
def test_remove_stock_insufficient(client, db_session, get_auth_tokens):
    # Set stock_count to 5
    db_session.commit()

    # Attempt to deduct 10 items
    response = client.post(
        f'/inventory/{2}/stock/remove',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={'quantity': 100}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Not enough stock available'

# Test: Add stock
def test_add_stock(client, db_session, get_auth_tokens):
    # Add 50 items to stock
    response = client.post(
        f'/inventory/{2}/stock/add',
        headers={'Authorization': f'Bearer {get_auth_tokens["manager"]}'},
        json={'quantity': 50}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Successfully added 50 items to stock'
    assert data['new_stock'] == 80

    # Verify in DB
    item = db_session.query(InventoryItem).filter_by(id=2).first()
    assert item.stock_count == 80

# Test: Add stock with bad amount
def test_add_stock_bad_amount(client, db_session, get_auth_tokens):
    # Attempt to add negative quantity
    response = client.post(
        f'/inventory/{2}/stock/add',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={'quantity': -20}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid quantity. Must be a positive integer.'

    # Attempt to add non-integer quantity
    response = client.post(
        f'/inventory/{2}/stock/add',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'},
        json={'quantity': 'twenty'}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Invalid quantity. Must be a positive integer.'

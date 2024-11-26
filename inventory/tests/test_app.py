# test_app.py
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from inventory.app import app as flask_app
import pytest
from flask import json
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.inventory import InventoryItem
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

def test_get_inventory_empty(client, auth_header):
    """Test getting inventory when none exist."""
    response = client.get('/inventory', headers=auth_header)
    assert response.status_code == 200
    assert response.json == []

def test_add_item(client, auth_header, db_session):
    """Test adding a new inventory item."""
    item_data = {
        'name': 'Laptop',
        'category': 'electronics',
        'price_per_item': 999.99,
        'description': 'A high-end laptop.',
        'stock_count': 10
    }
    response = client.post('/inventory', json=item_data, headers=auth_header)
    assert response.status_code == 201
    assert 'item_id' in response.json

def test_add_item_invalid_data(client, auth_header):
    """Test adding an item with invalid data."""
    item_data = {
        'name': 'La',  # Invalid name (too short)
        'category': 'unknown',  # Invalid category
        'price_per_item': -100,  # Invalid price
        'description': 'Bad',  # Invalid description (too short)
        'stock_count': -5  # Invalid stock count
    }
    response = client.post('/inventory', json=item_data, headers=auth_header)
    assert response.status_code == 400
    assert "Invalid value for" in response.json['error']

def test_get_inventory(client, auth_header, db_session):
    """Test retrieving all inventory items."""
    # Add items to the database
    item1 = InventoryItem(
        name='Smartphone',
        category='electronics',
        price_per_item=499.99,
        description='A smartphone with a great camera.',
        stock_count=20
    )
    item2 = InventoryItem(
        name='T-Shirt',
        category='clothes',
        price_per_item=19.99,
        description='A comfortable cotton t-shirt.',
        stock_count=50
    )
    db_session.add_all([item1, item2])
    db_session.commit()

    response = client.get('/inventory', headers=auth_header)
    assert response.status_code == 200
    assert len(response.json) == 2

def test_get_item_details(client, auth_header, db_session):
    """Test retrieving item details by item_id."""
    # Add an item to retrieve
    item = InventoryItem(
        name='Headphones',
        category='accessories',
        price_per_item=79.99,
        description='Noise-cancelling headphones.',
        stock_count=15
    )
    db_session.add(item)
    db_session.commit()

    response = client.get(f'/inventory/{item.id}', headers=auth_header)
    assert response.status_code == 200
    assert response.json['name'] == 'Headphones'

def test_get_item_details_not_found(client, auth_header):
    """Test retrieving details of a non-existent item."""
    response = client.get('/inventory/999', headers=auth_header)
    assert response.status_code == 404
    assert response.json['error'] == 'Item not found'

def test_update_item(client, auth_header, db_session):
    """Test updating an existing inventory item."""
    # Add an item to update
    item = InventoryItem(
        name='Tablet',
        category='electronics',
        price_per_item=299.99,
        description='A tablet with a large display.',
        stock_count=30
    )
    db_session.add(item)
    db_session.commit()

    # Update data
    updated_data = {
        'name': 'Tablet Pro',
        'category': 'electronics',
        'price_per_item': 399.99,
        'description': 'An upgraded tablet with better performance.',
        'stock_count': 25
    }

    response = client.put(f'/inventory/{item.id}', json=updated_data, headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == f'Item {item.id} updated successfully'

def test_update_item_invalid_data(client, auth_header, db_session):
    """Test updating an item with invalid data."""
    # Add an item to update
    item = InventoryItem(
        name='Camera',
        category='electronics',
        price_per_item=549.99,
        description='A DSLR camera.',
        stock_count=10
    )
    db_session.add(item)
    db_session.commit()

    # Invalid update data
    updated_data = {
        'name': 'Ca',  # Invalid name
        'category': 'unknown',  # Invalid category
        'price_per_item': -50,  # Invalid price
        'description': 'Bad',  # Invalid description
        'stock_count': -1  # Invalid stock count
    }

    response = client.put(f'/inventory/{item.id}', json=updated_data, headers=auth_header)
    assert response.status_code == 400
    assert "Invalid value for" in response.json['error']

def test_update_item_not_found(client, auth_header):
    """Test updating a non-existent item."""
    updated_data = {
        'name': 'Non-existent Item',
        'category': 'electronics',
        'price_per_item': 100.0,
        'description': 'This item does not exist.',
        'stock_count': 5
    }
    response = client.put('/inventory/999', json=updated_data, headers=auth_header)
    assert response.status_code == 404
    assert response.json['error'] == 'Item not found'

def test_delete_item(client, auth_header, db_session):
    """Test deleting an inventory item."""
    # Add an item to delete
    item = InventoryItem(
        name='Watch',
        category='accessories',
        price_per_item=199.99,
        description='A luxury watch.',
        stock_count=5
    )
    db_session.add(item)
    db_session.commit()

    response = client.delete(f'/inventory/{item.id}', headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == f'Item {item.id} deleted successfully'

def test_delete_item_not_found(client, auth_header):
    """Test deleting a non-existent item."""
    response = client.delete('/inventory/999', headers=auth_header)
    assert response.status_code == 404
    assert response.json['error'] == 'Item not found'

def test_deduct_item_stock(client, auth_header, db_session):
    """Test deducting stock from an item."""
    # Add an item
    item = InventoryItem(
        name='Backpack',
        category='accessories',
        price_per_item=49.99,
        description='A durable backpack.',
        stock_count=20
    )
    db_session.add(item)
    db_session.commit()

    response = client.post(
        f'/inventory/{item.id}/remove_stock',
        json={'quantity': 5},
        headers=auth_header
    )
    assert response.status_code == 200
    assert response.json['new_stock'] == 15

def test_deduct_item_stock_invalid_quantity(client, auth_header):
    """Test deducting stock with invalid quantity."""
    response = client.post(
        '/inventory/1/remove_stock',
        json={'quantity': -5},
        headers=auth_header
    )
    assert response.status_code == 400
    assert response.json['error'] == 'Invalid quantity. Must be a positive integer.'

def test_deduct_item_stock_insufficient_stock(client, auth_header, db_session):
    """Test deducting more stock than available."""
    # Add an item
    item = InventoryItem(
        name='Sunglasses',
        category='accessories',
        price_per_item=59.99,
        description='Polarized sunglasses.',
        stock_count=3
    )
    db_session.add(item)
    db_session.commit()

    response = client.post(
        f'/inventory/{item.id}/remove_stock',
        json={'quantity': 5},
        headers=auth_header
    )
    assert response.status_code == 400
    assert response.json['error'] == 'Not enough stock available'

def test_add_item_stock(client, auth_header, db_session):
    """Test adding stock to an item."""
    # Add an item
    item = InventoryItem(
        name='Book',
        category='accessories',
        price_per_item=14.99,
        description='A bestselling novel.',
        stock_count=10
    )
    db_session.add(item)
    db_session.commit()

    response = client.post(
        f'/inventory/{item.id}/add_stock',
        json={'quantity': 5},
        headers=auth_header
    )
    assert response.status_code == 200
    assert response.json['new_stock'] == 15

def test_add_item_stock_invalid_quantity(client, auth_header):
    """Test adding stock with invalid quantity."""
    response = client.post(
        '/inventory/1/add_stock',
        json={'quantity': -3},
        headers=auth_header
    )
    assert response.status_code == 400
    assert response.json['error'] == 'Invalid quantity. Must be a positive integer.'

def test_validate_data_missing_field():
    """Test inventory item data validation with missing field."""
    data = {
        # 'name' is missing
        'category': 'electronics',
        'price_per_item': 299.99,
        'description': 'A great gadget.',
        'stock_count': 10
    }
    is_valid, message = InventoryItem.validate_data(data)
    assert not is_valid
    assert message == "'name' is a required field."

def test_validate_data_invalid_name():
    """Test inventory item data validation with invalid name."""
    data = {
        'name': 'TV',  # Too short
        'category': 'electronics',
        'price_per_item': 299.99,
        'description': 'A high-definition television.',
        'stock_count': 10
    }
    is_valid, message = InventoryItem.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'name'" in message

def test_validate_data_invalid_category():
    """Test inventory item data validation with invalid category."""
    data = {
        'name': 'Refrigerator',
        'category': 'appliances',  # Invalid category
        'price_per_item': 499.99,
        'description': 'A double-door refrigerator.',
        'stock_count': 5
    }
    is_valid, message = InventoryItem.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'category'" in message

def test_validate_data_invalid_price():
    """Test inventory item data validation with invalid price."""
    data = {
        'name': 'Microwave',
        'category': 'electronics',
        'price_per_item': -50,  # Negative price
        'description': 'A microwave oven.',
        'stock_count': 8
    }
    is_valid, message = InventoryItem.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'price_per_item'" in message

def test_validate_data_invalid_stock_count():
    """Test inventory item data validation with invalid stock count."""
    data = {
        'name': 'Oven',
        'category': 'electronics',
        'price_per_item': 249.99,
        'description': 'An electric oven.',
        'stock_count': -2  # Negative stock count
    }
    is_valid, message = InventoryItem.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'stock_count'" in message

def test_validate_data_invalid_description():
    """Test inventory item data validation with invalid description."""
    data = {
        'name': 'Blender',
        'category': 'electronics',
        'price_per_item': 39.99,
        'description': 'Mix',  # Too short
        'stock_count': 15
    }
    is_valid, message = InventoryItem.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'description'" in message

def test_validate_data_valid():
    """Test inventory item data validation with valid data."""
    data = {
        'name': 'Coffee Maker',
        'category': 'electronics',
        'price_per_item': 79.99,
        'description': 'A programmable coffee maker.',
        'stock_count': 12
    }
    is_valid, message = InventoryItem.validate_data(data)
    assert is_valid
    assert message == "Validation successful."

def test_get_inventory_invalid_token(client):
    """Test getting inventory with invalid token."""
    auth_header = {'Authorization': 'Bearer invalidtoken'}
    response = client.get('/inventory', headers=auth_header)
    assert response.status_code == 422  # Unprocessable Entity (Invalid token)

def test_get_inventory_missing_token(client):
    """Test getting inventory without token."""
    response = client.get('/inventory')
    assert response.status_code == 401  # Unauthorized

def test_add_item_no_auth(client):
    """Test adding an item without authentication."""
    item_data = {
        'name': 'Printer',
        'category': 'electronics',
        'price_per_item': 129.99,
        'description': 'A wireless printer.',
        'stock_count': 7
    }
    response = client.post('/inventory', json=item_data)
    assert response.status_code == 401  # Unauthorized

def test_update_item_no_auth(client):
    """Test updating an item without authentication."""
    updated_data = {
        'name': 'Updated Item',
        'category': 'electronics',
        'price_per_item': 99.99,
        'description': 'Updated description.',
        'stock_count': 5
    }
    response = client.put('/inventory/1', json=updated_data)
    assert response.status_code == 401  # Unauthorized

def test_delete_item_no_auth(client):
    """Test deleting an item without authentication."""
    response = client.delete('/inventory/1')
    assert response.status_code == 401  # Unauthorized

def test_deduct_item_stock_no_auth(client):
    """Test deducting item stock without authentication."""
    response = client.post(
        '/inventory/1/remove_stock',
        json={'quantity': 1}
    )
    assert response.status_code == 401  # Unauthorized

def test_add_item_stock_no_auth(client):
    """Test adding item stock without authentication."""
    response = client.post(
        '/inventory/1/add_stock',
        json={'quantity': 1}
    )
    assert response.status_code == 401  # Unauthorized

def test_add_item_stock_item_not_found(client, auth_header):
    """Test adding stock to a non-existent item."""
    response = client.post(
        '/inventory/999/add_stock',
        json={'quantity': 5},
        headers=auth_header
    )
    assert response.status_code == 404
    assert response.json['error'] == 'Item not found'

def test_deduct_item_stock_item_not_found(client, auth_header):
    """Test deducting stock from a non-existent item."""
    response = client.post(
        '/inventory/999/remove_stock',
        json={'quantity': 5},
        headers=auth_header
    )
    assert response.status_code == 404
    assert response.json['error'] == 'Item not found'

def test_add_item_duplicate_name(client, auth_header, db_session):
    """Test adding an item with a duplicate name."""
    # Add an item with a specific name
    item = InventoryItem(
        name='UniqueItem',
        category='electronics',
        price_per_item=199.99,
        description='A unique item.',
        stock_count=5
    )
    db_session.add(item)
    db_session.commit()

    # Attempt to add another item with the same name
    item_data = {
        'name': 'UniqueItem',  # Duplicate name
        'category': 'electronics',
        'price_per_item': 299.99,
        'description': 'Another item with the same name.',
        'stock_count': 5
    }
    response = client.post('/inventory', json=item_data, headers=auth_header)
    # Assuming the 'name' field is unique, adjust if necessary
    assert response.status_code == 201  # If name is not unique, item is added
    # If name should be unique, uncomment the following lines:
    # assert response.status_code == 400
    # assert 'already exists' in response.json['error']

def test_update_item_no_data(client, auth_header, db_session):
    """Test updating an item with no data provided."""
    # Add an item
    item = InventoryItem(
        name='Smartwatch',
        category='electronics',
        price_per_item=149.99,
        description='A smartwatch with fitness tracking.',
        stock_count=25
    )
    db_session.add(item)
    db_session.commit()

    response = client.put(f'/inventory/{item.id}', json={}, headers=auth_header)
    assert response.status_code == 400
    assert response.json['error'] == "'name' is a required field."

def test_add_item_invalid_json(client, auth_header):
    """Test adding an item with invalid JSON payload."""
    response = client.post(
        '/inventory',
        data="Invalid JSON",
        headers={**auth_header, 'Content-Type': 'application/json'}
    )
    assert response.status_code == 400  # Bad Request

def test_get_item_details_invalid_id(client, auth_header):
    """Test retrieving item details with invalid ID."""
    response = client.get('/inventory/invalid_id', headers=auth_header)
    assert response.status_code == 404  # Not Found or could be 400 Bad Request depending on implementation

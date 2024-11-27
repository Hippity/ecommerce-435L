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

def test_add_item(client, auth_header):
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
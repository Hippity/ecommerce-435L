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
from sales.app import app as flask_app
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
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def mock_get_customer_data(username,headers):
            return {
                "id": 2,
            "fullname":"Regular User",
            "username":"user1",
            "age":25,
            "address":"456 User Ave",
            "gender":"female",
            "marital_status":"married",
            "role":"customer",
            "wallet":500.0
            }
    def mock_deduct_wallet(username,total_cost,headers):
        print("hellooo")
        return 0
    
    def mock_remove_stock(item_id,quantity,headers):
        return 0

    flask_app.config['GET_CUSTOMER_DATA_FUNC'] = mock_get_customer_data
    flask_app.config['REMOVE_STOCK_FUNC'] = mock_remove_stock
    flask_app.config['DEDUCT_WALLET_FUNC'] = mock_deduct_wallet

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

def test_get_item_by_id(client, db_session, add_inventory_item, get_auth_tokens, add_regular_user,add_product_manager,add_default_admin ):
    """
    Test retrieving an inventory item by its ID.
    """
    response = client.get(
        f'/inventory/{add_inventory_item.id}',
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == add_inventory_item.id
    assert data['name'] == add_inventory_item.name
    assert data['price_per_item'] == add_inventory_item.price_per_item
    assert data['stock_count'] == add_inventory_item.stock_count

def test_get_item_by_id_no_item(client, db_session, get_auth_tokens):
    """
    Test retrieving a non-existent inventory item by its ID.
    """
    response = client.get(
        '/inventory/9999',  # Assuming this ID does not exist
        headers={'Authorization': f'Bearer {get_auth_tokens["admin"]}'}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Item not found'

def test_get_items(client, db_session, get_auth_tokens, ):
    """
    Test retrieving all inventory items.
    """
    response = client.get(
        '/inventory',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1 
    assert data[0]['name'] == 'Apple'


def test_get_items_by_category(client, db_session, get_auth_tokens, ):
    """
    Test retrieving inventory items by category.
    """
    response = client.get(
        f'/inventory/food',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]['name'] == 'Apple'


def test_add_wishlist(client, db_session, get_auth_tokens, ):
    """
    Test adding an item to the customer's wishlist.
    """
    response = client.post(
        f'/inventory/{1}/wishlist/add',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == f"Item {1} added to wishlist successfully."

    # Verify in DB
    wishlist_item = db_session.query(Wishlist).filter_by(
        customer_id=2,  # Assuming add_regular_user has ID 1
        item_id=1
    ).first()
    assert wishlist_item is not None

def test_add_wishlist_already_there(client, db_session, get_auth_tokens, ):
    """
    Test adding an item to the wishlist that's already there.
    """
    # First addition
    client.post(
        f'/inventory/{1}/wishlist/add',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={}
    )

    # Second addition
    response = client.post(
        f'/inventory/{1}/wishlist/add',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == f"Item {1} is already in your wishlist."

def test_add_wishlist_no_item(client, db_session, get_auth_tokens, ):
    """
    Test adding a non-existent item to the wishlist.
    """
    response = client.post(
        '/inventory/9999/wishlist/add',  # Assuming this ID does not exist
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Item not found"

def test_remove_wishlist(client, db_session, get_auth_tokens, ):
    """
    Test removing an item from the customer's wishlist.
    """
    # Add to wishlist first
    client.post(
        f'/inventory/{1}/wishlist/add',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={}
    )

    # Remove from wishlist
    response = client.delete(
        f'/inventory/{1}/wishlist/remove',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == f"Item {1} removed from wishlist successfully."

    # Verify removal in DB
    wishlist_item = db_session.query(Wishlist).filter_by(
        customer_id=1,
        item_id=1
    ).first()
    assert wishlist_item is None

def test_remove_wishlist_no_item(client, db_session, get_auth_tokens, ):
    """
    Test removing a non-existent item from the wishlist.
    """
    response = client.delete(
        '/inventory/9999/wishlist/remove',  # Assuming this ID does not exist
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Item not found"

def test_remove_wishlist_not_there(client, db_session, get_auth_tokens, ):
    """
    Test removing an item that is not in the wishlist.
    """
    response = client.delete(
        f'/inventory/{1}/wishlist/remove',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['message'] == f"Item {1} is not in your wishlist."

# ---------------------------
# Tests for Purchase
# ---------------------------
def test_purchase_item(client, db_session, get_auth_tokens ):
    """
    Test purchasing an item with sufficient wallet balance and stock.
    """
    response = client.post(
        f'/purchase/{1}',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={'quantity': 2}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert f"successfully purchased 2 unit(s) of Apple." in data['message']
    assert 'order_id' in data

    # Verify in DB
    order = db_session.query(Order).filter_by(id=data['order_id']).first()
    assert order is not None
    assert order.quantity == 2

def test_purchase_item_insufficient_amount(client, db_session, get_auth_tokens, ):
    """
    Test purchasing an item when the wallet balance is insufficient.
    """
    # Set user's wallet to a low amount
    customer = db_session.query(Customer).filter_by(username='user1').first()
    customer.wallet = 10.0
    db_session.commit()

    response = client.post(
        f'/purchase/{1}',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={'quantity': 100}  # Total cost = 50.0 > wallet
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Insufficient wallet balance'

def test_purchase_item_no_stock(client, db_session, get_auth_tokens, ):
    """
    Test purchasing an item when there is insufficient stock.
    """

    db_session.commit()

    response = client.post(
        f'/purchase/{1}',
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={'quantity': 200}  # Quantity > stock
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == 'Not enough stock available'

def test_purchase_item_no_item(client, db_session, get_auth_tokens, ):
    """
    Test purchasing a non-existent item.
    """
    response = client.post(
        '/purchase/9999',  # Assuming this ID does not exist
        headers={'Authorization': f'Bearer {get_auth_tokens["user"]}'},
        json={'quantity': 1}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'Item not found'
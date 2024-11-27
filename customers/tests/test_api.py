import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from customers.app import app as flask_app
import pytest
from flask import json
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.customer import Customer
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
def auth_header():
    """Generate an authentication header with JWT token."""
    access_token = create_access_token(identity=json.dumps({'username': 'testuser'}))
    return {'Authorization': f'Bearer {access_token}'}

def test_get_customers_empty(client, auth_header):
    """Test getting customers when none exist."""
    response = client.get('/customers', headers=auth_header)
    assert response.status_code == 200
    assert response.json == []

def test_add_customer(client, auth_header):
    """Test adding a new customer."""
    customer_data = {
        'fullname': 'John Doe',
        'username': 'johndoe',
        'password': 'secret123',
        'age': 30,
        'address': '123 Main St',
        'gender': 'male',
        'marital_status': 'single'
    }
    response = client.post('/customers', json=customer_data, headers=auth_header)
    assert response.status_code == 201
    assert 'customer_id' in response.json

def test_add_customer_existing_username(client, auth_header, db_session):
    """Test adding a customer with an existing username."""
    # Add a customer first
    existing_customer = Customer(
        fullname='Jane Doe',
        username='janedoe',
        password='secret123',
        age=28,
        address='456 Elm St',
        gender='female',
        marital_status='single'
    )
    db_session.add(existing_customer)
    db_session.commit()

    # Attempt to add another customer with the same username
    customer_data = {
        'fullname': 'Janet Smith',
        'username': 'janedoe',  # Same username
        'password': 'password123',
        'age': 35,
        'address': '789 Oak St',
        'gender': 'female',
        'marital_status': 'married'
    }
    response = client.post('/customers', json=customer_data, headers=auth_header)
    assert response.status_code == 400
    assert response.json['error'] == 'Username is already taken'

def test_get_customer_by_username(client, auth_header, db_session):
    """Test retrieving a customer by username."""
    # Add a customer to retrieve
    customer = Customer(
        fullname='Alice Wonderland',
        username='alice',
        password='wonderland',
        age=25,
        address='Magic Forest',
        gender='female',
        marital_status='single'
    )
    db_session.add(customer)
    db_session.commit()

    response = client.get('/customers/alice', headers=auth_header)
    assert response.status_code == 200
    assert response.json['username'] == 'alice'

def test_get_customer_by_username_not_found(client, auth_header):
    """Test retrieving a non-existent customer."""
    response = client.get('/customers/nonexistent', headers=auth_header)
    assert response.status_code == 404
    assert response.json['error'] == 'Customer not found'

def test_update_customer(client, auth_header, db_session):
    """Test updating a customer's information."""
    # Add a customer to update
    customer = Customer(
        fullname='Bob Builder',
        username='bobbuilder',
        password='canwefixit',
        age=40,
        address='Construction Site',
        gender='male',
        marital_status='married'
    )
    db_session.add(customer)
    db_session.commit()

    # Update data
    updated_data = {
        'fullname': 'Bob the Builder',
        'username': 'bobbuilder',
        'password': 'yeswecan',
        'age': 41,
        'address': 'New Construction Site',
        'gender': 'male',
        'marital_status': 'married'
    }

    # Update JWT to match username
    access_token = create_access_token(identity=json.dumps({'username': 'bobbuilder'}))
    auth_header = {'Authorization': f'Bearer {access_token}'}

    response = client.put('/customers/bobbuilder', json=updated_data, headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == 'Customer bobbuilder updated successfully'

def test_delete_customer(client, db_session):
    """Test deleting a customer."""
    # Add a customer to delete
    customer = Customer(
        fullname='Dora Explorer',
        username='dora',
        password='backpack',
        age=18,
        address='Jungle',
        gender='female',
        marital_status='single'
    )
    db_session.add(customer)
    db_session.commit()

    # Update JWT to match username
    access_token = create_access_token(identity=json.dumps({'username': 'dora'}))
    auth_header = {'Authorization': f'Bearer {access_token}'}

    response = client.delete('/customers/dora', headers=auth_header)
    assert response.status_code == 200
    assert response.json['message'] == 'Customer dora deleted successfully'

def test_add_customer_wallet(client, db_session):
    """Test adding to a customer's wallet."""
    # Add a customer
    customer = Customer(
        fullname='Eve Online',
        username='eve',
        password='spaceship',
        age=29,
        address='Universe',
        gender='female',
        marital_status='single',
        wallet=100.0
    )
    db_session.add(customer)
    db_session.commit()

    # Update JWT to match username
    access_token = create_access_token(identity=json.dumps({'username': 'eve'}))
    auth_header = {'Authorization': f'Bearer {access_token}'}

    response = client.post(
        '/customers/eve/wallet/add',
        json={'amount': 50.0},
        headers=auth_header
    )
    assert response.status_code == 200
    assert response.json['new_balance'] == 150.0

def test_add_customer_wallet_invalid_amount(client, auth_header):
    """Test adding to wallet with invalid amount."""
    response = client.post(
        '/customers/eve/wallet/add',
        json={'amount': -10},
        headers=auth_header
    )
    assert response.status_code == 400
    assert response.json['error'] == 'Invalid amount'

def test_deduct_customer_wallet(client, db_session):
    """Test deducting from a customer's wallet."""
    # Add a customer
    customer = Customer(
        fullname='Frank Ocean',
        username='frank',
        password='blonde',
        age=33,
        address='Music Studio',
        gender='male',
        marital_status='single',
        wallet=200.0
    )
    db_session.add(customer)
    db_session.commit()

    # Update JWT to match username
    access_token = create_access_token(identity=json.dumps({'username': 'frank'}))
    auth_header = {'Authorization': f'Bearer {access_token}'}

    response = client.post(
        '/customers/frank/wallet/deduct',
        json={'amount': 50.0},
        headers=auth_header
    )
    assert response.status_code == 200
    assert response.json['new_balance'] == 150.0

def test_deduct_customer_wallet_invalid_amount(client, auth_header):
    """Test deducting wallet with invalid amount."""
    response = client.post(
        '/customers/eve/wallet/deduct',
        json={'amount': -10},
        headers=auth_header
    )
    assert response.status_code == 400
    assert response.json['error'] == 'Invalid amount'

def test_deduct_customer_wallet_insufficient_balance(client, db_session):
    """Test deducting more than the wallet balance."""
    # Add a customer
    customer = Customer(
        fullname='Grace Hopper',
        username='grace',
        password='computer',
        age=85,
        address='Programming Lab',
        gender='female',
        marital_status='single',
        wallet=20.0
    )
    db_session.add(customer)
    db_session.commit()

    # Update JWT to match username
    access_token = create_access_token(identity=json.dumps({'username': 'grace'}))
    auth_header = {'Authorization': f'Bearer {access_token}'}

    response = client.post(
        '/customers/grace/wallet/deduct',
        json={'amount': 50.0},
        headers=auth_header
    )
    assert response.status_code == 400
    assert response.json['error'] == 'Insufficient balance'

def test_validate_data_missing_field():
    """Test customer data validation with missing field."""
    data = {
        'fullname': 'Hank Hill',
        # 'username' is missing
        'password': 'propane',
        'age': 45,
        'address': 'Arlen, Texas',
        'gender': 'male',
        'marital_status': 'married'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert message == "'username' is a required field."

def test_validate_data_invalid_fullname():
    """Test customer data validation with invalid fullname."""
    data = {
        'fullname': 'Al',  # Too short
        'username': 'albert',
        'password': 'password',
        'age': 30,
        'address': '123 Street',
        'gender': 'male',
        'marital_status': 'single'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'fullname'" in message

def test_validate_data_invalid_username():
    """Test customer data validation with invalid username."""
    data = {
        'fullname': 'Albert Einstein',
        'username': 'ae',  
        'password': 'relativity',
        'age': 42,
        'address': 'Physics Lab',
        'gender': 'male',
        'marital_status': 'married'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'username'" in message

def test_validate_data_invalid_password():
    """Test customer data validation with invalid password."""
    data = {
        'fullname': 'Isaac Newton',
        'username': 'newton',
        'password': 'apple',  # Too short
        'age': 50,
        'address': 'Science Academy',
        'gender': 'male',
        'marital_status': 'single'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'password'" in message

def test_validate_data_invalid_age():
    """Test customer data validation with invalid age."""
    data = {
        'fullname': 'Marie Curie',
        'username': 'marie',
        'password': 'radiation',
        'age': 15, 
        'address': 'Chemistry Lab',
        'gender': 'female',
        'marital_status': 'married'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'age'" in message

def test_validate_data_invalid_address():
    """Test customer data validation with invalid address."""
    data = {
        'fullname': 'Nikola Tesla',
        'username': 'tesla',
        'password': 'electricity',
        'age': 60,
        'address': 'NY',  # Too short
        'gender': 'male',
        'marital_status': 'single'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'address'" in message

def test_validate_data_invalid_gender():
    """Test customer data validation with invalid gender."""
    data = {
        'fullname': 'Ivy League',
        'username': 'ivylea',
        'password': 'password',
        'age': 22,
        'address': 'College',
        'gender': 'unknown',
        'marital_status': 'single'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'gender'" in message

def test_validate_data_invalid_marital_status():
    """Test customer data validation with invalid marital status."""
    data = {
        'fullname': 'Jack Sparrow',
        'username': 'captainjack',
        'password': 'blackpearl',
        'age': 40,
        'address': 'Caribbean Sea',
        'gender': 'male',
        'marital_status': 'complicated'
    }
    is_valid, message = Customer.validate_data(data)
    assert not is_valid
    assert "Invalid value for 'marital_status'" in message

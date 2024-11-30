from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth.app import role_required
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.models.order import Order
from shared.models.wishlist import Wishlist
from shared.database import engine, SessionLocal
from sqlalchemy.sql import text
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)
ph = PasswordHasher()

# Create tables if not created
Base.metadata.create_all(bind=engine)

@app.route('/customers', methods=['GET'])
@jwt_required()
@role_required(["admin"])
def get_customers():
    """
    Retrieve all customers from the database.

    Endpoint:
        GET /customers

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(["admin"]) - Restricts access to users with the "admin" role.

    Returns:
        - 200 OK: A JSON list of customer objects
        - 500 Internal Server Error: A JSON object with an "error" field if an exception occurs during database access.
    """
    db_session = SessionLocal()
    try:
        customers = db_session.query(Customer).all()
        customers_list = [
            {
                'id': customer.id,
                'fullname': customer.fullname,
                'username': customer.username,
                'age': customer.age,
                'address': customer.address,
                'gender': customer.gender,
                'marital_status': customer.marital_status,
                'wallet': customer.wallet,
                "role" : customer.role
            }
            for customer in customers
        ]
        return jsonify(customers_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def get_customer_by_username(username):
    """
    Retrieve customer information by username.

    Endpoint:
        GET /customers/<string:username>

    Parameters:
        username (str): The username of the customer whose information is to be retrieved.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer', 'product_manager']) - Restricts access to users with 
          "admin" or "customer" or "product_manager" roles.

    Returns:
        - 200 OK: A JSON object containing the customer's details.
        - 400 Bad Request: If a non-admin user tries to access another customer's data.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during database access.
    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        customer_data = {
            'id': customer.id,
            'fullname': customer.fullname,
            'username': customer.username,
            'age': customer.age,
            'address': customer.address,
            'gender': customer.gender,
            'marital_status': customer.marital_status,
            'wallet': customer.wallet
        }
        return jsonify(customer_data), 200
    except Exception as e:
        print(e)
        print("hello")
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers', methods=['POST'])
def add_customer():
    """
    Register a new customer. It validates the input data, ensures that the username
    is unique, hashes the customer's password, and stores the customer in the database.

    Endpoint:
        POST /customers

    Request Body:
        A JSON object containing the following fields:
            - fullname (str): The full name of the customer.
            - username (str): The unique username of the customer.
            - password (str): The customer's password (will be hashed before storage).
            - age (int): The customer's age.
            - address (str): The customer's address.
            - gender (str): The customer's gender.
            - marital_status (str): The customer's marital status.
            
    Returns:
        - 201 Created: If the customer is successfully registered. Includes a success message
        and the customer's ID.
        - 400 Bad Request: If the username is already taken or the input data fails validation.
        - 500 Internal Server Error: If an exception occurs during the registration process.
    """
    data = request.json
    db_session = SessionLocal()
    try:
        existing_customer = db_session.query(Customer).filter_by(username=data.get('username')).first()
        if existing_customer:
            return jsonify({'error': 'Username is already taken'}), 400

        is_valid, message = Customer.validate_data(data,"add")
        if not is_valid:
            return jsonify({'error': message}), 400

        hashed_password = ph.hash(data.get('password'))

        new_customer = Customer(
            fullname=data.get('fullname'),
            username=data.get('username'),
            password=hashed_password,
            age=data.get('age'),
            address=data.get('address'),
            gender=data.get('gender'),
            marital_status=data.get('marital_status'),
            wallet=0.0,  
            role="customer" 
        )
        db_session.add(new_customer)
        db_session.commit()

        return jsonify({'message': 'Customer added successfully', 'customer_id': new_customer.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def update_customer(username):
    """
    Update customer information.

    Endpoint:
        PUT /customers/<string:username>

    Path Parameter:
        username (str): The username of the customer whose information is to be updated.
    
    Request Body:
        A JSON object containing the following fields:
            - fullname (str): The full name of the customer.
            - age (int): The customer's age.
            - address (str): The customer's address.
            - gender (str): The customer's gender.
            - marital_status (str): The customer's marital status.
         
    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer']) - Restricts access to users with 
        "admin" or "customer" roles.

    Returns:
        - 200 OK: If the customer information is successfully updated.
        - 400 Bad Request: If the user is not authorized to update the information 
        or the input data fails validation.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during the update process.
           
    """
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        is_valid, message = Customer.validate_data(data,"edit")
        if not is_valid:
            return jsonify({'error': message}), 400

        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        db_session.commit()
        return jsonify({'message': f'Customer {username} updated successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>/change-password', methods=['POST'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def change_password(username):
    """
    Change the password of a customer.

    Endpoint:
        POST /customers/<string:username>/change-password

    Path Parameter:
        username (str): The username of the customer whose password is to be changed.

    Request Body:
        A JSON object containing the following fields:
            - current_password (str): The current password of the customer.
            - new_password (str): The new password to set.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer']) - Restricts access to users with 
          "admin" or "customer" roles.

    Returns:
        - 200 OK: If the password is successfully changed.
        - 400 Bad Request: If the current password is incorrect or the new password is invalid.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400

    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        if not ph.verify(customer.password, current_password):
            return jsonify({'error': 'Invalid current password'}), 400
        
        if not isinstance(new_password, str) or len(new_password) < 6:
            return jsonify({'error': 'Invalid value for new password. It must be at least 6 characters'}), 400

        customer.password = ph.hash(new_password)
        db_session.commit()

        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def delete_customer(username):
    """
    Delete a customer by username and all entries related to it.

    Endpoint:
        DELETE /customers/<string:username>

    Path Parameter:
        username (str): The username of the customer to be deleted.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer']) - Restricts access to users with 
        "admin" or "customer" roles.

    Returns:
        - 200 OK: If the customer is successfully deleted.
        - 400 Bad Request: If a non-admin user attempts to delete another user's account.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during the deletion process.
    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        db_session.query(Order).filter_by(customer_id=customer.id).delete()
        db_session.query(Review).filter_by(customer_id=customer.id).delete()
        db_session.query(Wishlist).filter_by(customer_id=customer.id).delete()

        db_session.delete(customer)
        db_session.commit()
        return jsonify({'message': f'Customer {username} deleted successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>/wallet/add', methods=['POST'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def add_customer_wallet(username):
    """
    Add funds to a customer's wallet.

    Endpoint:
        POST /customers/<string:username>/wallet/add

    Path Parameter:
        username (str): The username of the customer whose wallet is to be charged.

    Request Body:
        A JSON object containing the following field:
            - amount (float): The amount to add to the customer's wallet. Must be greater than 0.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer','product_manager']) - Restricts access to users with 
        "admin" or "customer" or "product_manager" roles.

    Returns:
        - 200 OK: If the amount is successfully added to the customer's wallet. 
        - 400 Bad Request: If the amount is invalid or if a non-admin user attempts to add funds to another user's wallet.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    amount = data.get('amount')

    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        customer.wallet += amount
        db_session.commit()
        return jsonify({'message': f'Added ${amount} to {username}\'s wallet', 'new_balance': customer.wallet}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>/wallet/deduct', methods=['POST'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def deduct_customer_wallet(username):
    """
    Deduct funds to a customer's wallet.

    Endpoint:
        POST /customers/<string:username>/wallet/deduct

    Path Parameter:
        username (str): The username of the customer whose wallet is to be charged.

    Request Body:
        A JSON object containing the following field:
            - amount (float): The amount to deduct from the customer's wallet. Must be greater than 0.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer']) - Restricts access to users with 
        "admin" or "customer" roles.

    Returns:
        - 200 OK: If the amount is successfully deducted to the customer's wallet. 
        - 400 Bad Request: If the amount is invalid or if a non-admin user attempts to deduct funds from another user's wallet.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    amount = data.get('amount')

    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400

        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        if customer.wallet < amount:
            return jsonify({'error': 'Insufficient balance'}), 400

        customer.wallet -= amount
        db_session.commit()
        return jsonify({'message': f'Deducted ${amount} from {username}\'s wallet', 'new_balance': customer.wallet}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>/orders', methods=['GET'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def get_customer_orders(username):
    """
    Retrieve all previous orders of a customer.

    Endpoint:
        GET /customers/<string:username>/orders

    Path Parameter:
        username (str): The username of the customer whose orders are to be retrieved.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer']) - Restricts access to users with 
        "admin" or "customer" roles.

    Returns:
        - 200 OK: A JSON object containing a list of the customer's orders. 
        - 400 Bad Request: If a non-admin user attempts to view the orders of another customer.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during the process. 
    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400

        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        orders = customer.previous_orders 
        orders_list = [
            {
                'order_id': order.id,
                'item_id': order.item_id,
                'item_name' : order.inventory_item.name,
                'quantity': order.quantity
            }
            for order in orders
        ]
        return jsonify({'orders': orders_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()
        
@app.route('/customers/<string:username>/wishlist', methods=['GET'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def get_customer_wishlist(username):
    """
    Retrieve all wishlist items of a customer.

    Endpoint:
        GET /customers/<string:username>/wishlist

    Path Parameter:
        username (str): The username of the customer whose wishlist is to be retrieved.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer']) - Restricts access to users with 
        "admin" or "customer" roles.

    Returns:
        - 200 OK: A JSON object containing a list of the customer's wishlist items. 
        - 400 Bad Request: If a non-admin user attempts to view the wishlist of another customer.
        - 404 Not Found: If the customer with the specified username does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())

        if 'admin' not in user['role'] and user['username'] != username:
            return jsonify({'error': 'Invalid user'}), 400

        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        wishlist = customer.wishlist_items  
        wishlist_items = [
            {
                'wishlist_id': item.wishlist_id,
                'item_id': item.item_id,
                'item_name': item.inventory_item.name,  
                'item_price': item.inventory_item.price_per_item  
            }
            for item in wishlist
        ]

        return jsonify({'wishlist': wishlist_items}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/add-role', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def add_admin():
    """
    Register a new customer with a role

    Endpoint:
        POST /admins

    Request Body:
        A JSON object containing the following fields:
            - fullname (str): The full name of the admin.
            - username (str): The unique username of the admin.
            - password (str): The admin's password (will be hashed before storage).
            - age (int): The admin's age.
            - address (str): The admin's address.
            - gender (str): The admin's gender.
            - marital_status (str): The admin's marital status.
            - role (str): The role of the admin

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin']) - Restricts access to users with the "admin" role.

    Returns:
        - 201 Created: If the admin is successfully registered. Includes a success message
        and the admin's ID.
        - 400 Bad Request: If the username is already taken or the input data fails validation.
        - 500 Internal Server Error: If an exception occurs during the registration process.

    """
    data = request.json
    db_session = SessionLocal()
    try:
        existing_customer = db_session.query(Customer).filter_by(username=data.get('username')).first()
        if existing_customer:
            return jsonify({'error': 'Username is already taken'}), 400

        is_valid, message = Customer.validate_data(data,'add')
        if not is_valid:
            return jsonify({'error': message}), 400

        hashed_password = ph.hash(data.get('password'))

        new_customer = Customer(
            fullname=data.get('fullname'),
            username=data.get('username'),
            password=hashed_password,
            age=data.get('age'),
            address=data.get('address'),
            gender=data.get('gender'),
            marital_status=data.get('marital_status'),
            wallet=0.0,  # Default wallet balance
            role= data.get('role')
        )
        db_session.add(new_customer)
        db_session.commit()

        return jsonify({f'message': f'New user added successfully', 'customer_id': new_customer.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to monitor service and database status.

    Returns:
        - 200 OK: If the service and database are operational.
        - 500 Internal Server Error: If the database or any service is unavailable.
    """
    db_status = "unknown"
    db_session = SessionLocal()
    try:
        db_session.execute(text("SELECT 1"))
        db_session.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"unavailable: {str(e)}"

    # Determine overall status
    overall_status = "healthy" if db_status == "connected" else "unhealthy"

    # Return health check details
    return jsonify({
        "status": overall_status,
        "database": db_status,
    }), 200 if overall_status == "healthy" else 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)

from flask import Flask, json, request, jsonify , current_app
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth.app import role_required
from shared.models.wishlist import Wishlist
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.order import Order
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, jwt_required, get_jwt_identity
import json
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)

def get_customer_details(username,headers):
    """
    Retrieve customer data from the customer service.

    Parameters:
        username (str): The username of the customer whose details are to be retrieved.
        headers (dict): A dictionary of HTTP headers to include in the request. Typically includes 
                        authentication headers.

    Returns:
        dict: A JSON object containing customer details if the request is successful.
        rasies an exception

    """
    response = requests.get(f'http://customer-service:3000/customer/{username}', timeout=5, headers=headers)
    response.raise_for_status()
    if response.headers.get('Content-Type') != 'application/json':
        raise Exception('Unexpected content type: JSON expected')
    customer = response.json()
    return customer

def remove_stock(item_id,quantity,headers):
    """
    Remove stock for a specific inventory item.

    Parameters:
        item_id (int): The ID of the inventory item whose stock is to be deducted.
        quantity (int): The quantity to deduct from the stock. Must be a positive integer.
        headers (dict): A dictionary of HTTP headers to include in the request, typically 
                        including authentication headers.

    Returns:
        None: The function raises an exception if there is an error during the process.
"""
    stock_payload = {"quantity": quantity}
    stock_response = requests.post(
            f'http://inventory-service:3001/inventory/{item_id}/stock/remove',
            json=stock_payload,
            headers=headers,
            timeout=5
    )
    stock_response.raise_for_status()  # Raise exception for HTTP errors
    if stock_response.headers.get('Content-Type') != 'application/json':
        raise Exception('Unexpected content type: JSON expected from inventory service')

def deduct_wallet(username,total_cost,headers):
        """
    Deduct funds from a customer's wallet.

    Parameters:
        username (str): The username of the customer whose wallet balance is to be deducted.
        total_cost (float): The amount to deduct from the customer's wallet. Must be a positive number.
        headers (dict): A dictionary of HTTP headers to include in the request, typically 
                        including authentication headers.

    Returns:
        None: The function raises an exception if there is an error during the process.

    """
        wallet_payload = {"amount": total_cost}
        wallet_response = requests.post(
            f'http://customers-service:3000/customers/{username}/wallet/deduct',
            json=wallet_payload,
            headers=headers,
            timeout=5
        )
        wallet_response.raise_for_status()  # Raise exception for HTTP errors
        if wallet_response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected from wallet service')

# Set the default function in app config
app.config['GET_CUSTOMER_DATA_FUNC'] = get_customer_details
app.config['REMOVE_STOCK_FUNC'] = remove_stock
app.config['DEDUCT_WALLER_FUNC'] = deduct_wallet

# Create tables if not created
Base.metadata.create_all(bind=engine)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)
    
@app.route('/inventory', methods=['GET'])
@role_required(['admin', 'customer', 'product_manager'])
@jwt_required()
def get_inventory():
    """
    Retrieve all items in the inventory with their name and price.

    Endpoint:
        GET /inventory

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer', 'product_manager']) - Restricts access to users 
        with "admin", "customer", or "product_manager" roles.

    Returns:
        - 200 OK: A JSON object containing a list of all inventory items. Each item includes:
            - name (str): The name of the item.
            - price (float): The price per item.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    db_session = SessionLocal()
    try:
        goods = db_session.query(InventoryItem.name, InventoryItem.price_per_item).all()
        json_results = [{"name": name, "price": price} for name, price in goods]
        return jsonify(json_results), 200
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        db_session.close()

@app.route('/inventory/<str:category>', methods=['GET'])
@role_required(['admin', 'customer', 'product_manager'])
@jwt_required()
def get_inventory(category):
    """
    Retrieve all items in the inventory with their name and price given a category.

    Endpoint:
        GET /inventory

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer', 'product_manager']) - Restricts access to users 
        with "admin", "customer", or "product_manager" roles.

    Returns:
        - 200 OK: A JSON object containing a list of all inventory items in a category. Each item includes:
            - name (str): The name of the item.
            - price (float): The price per item.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    db_session = SessionLocal()
    try:
        goods = db_session.query(InventoryItem.name, InventoryItem.price_per_item).filter(InventoryItem.category == category).all()
        json_results = [{"name": name, "price": price} for name, price in goods]
        return jsonify(json_results), 200
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'customer', 'product_manager'])
def get_item_details(item_id):
    """
    Retrieve all items in the inventory with their name and price.

    Endpoint:
        GET /inventory

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer', 'product_manager']) - Restricts access to users 
        with "admin", "customer", or "product_manager" roles.

    Returns:
        - 200 OK: A JSON object containing a list of all inventory items. Each item includes:
            - name (str): The name of the item.
            - price (float): The price per item.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    db_session = SessionLocal()
    try:
        item = db_session.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if item is None:
            return jsonify({"error": "Item not found"}), 404
        item_details = {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price_per_item": item.price_per_item,
            "description": item.description,
            "stock_count": item.stock_count
        }
        return jsonify(item_details), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>/wishlist/add', methods=['POST'])
@jwt_required()
@role_required(['customer','admin','product_manager'])
def add_wishlist(item_id):
    """
    Add an item to the customer's wishlist.

    Endpoint:
        POST /inventory/<int:item_id>/wishlist/add

    Path Parameter:
        item_id (int): The ID of the inventory item to be added to the wishlist.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['customer', 'admin', 'product_manager']) - Restricts access to users 
        with "customer", "admin", or "product_manager" roles.

    Returns:
        - 200 OK: If the item is successfully added to the wishlist or is already in the wishlist.
        - 404 Not Found: If the customer or the inventory item does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)

        item = get_item_details(item_id)

        existing_wishlist_item = db_session.query(Wishlist).filter(
            Wishlist.customer_id == customer.id,
            Wishlist.item_id == item.id
        ).first()
        if existing_wishlist_item:
            return jsonify({'message': f"Item {item_id} is already in your wishlist."}), 200

        new_wishlist_item = Wishlist(customer_id=customer.id, item_id=item.id)
        db_session.add(new_wishlist_item)
        db_session.commit()

        return jsonify({"message": f"Item {item_id} added to wishlist successfully."}), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>/wishlist/remove', methods=['DELETE'])
@jwt_required()
@role_required(['customer','admin'])
def remove_wishlist(item_id):
    """
    Remove an item from the customer's wishlist.

    Endpoint:
        DELETE /inventory/<int:item_id>/wishlist/remove

    Path Parameter:
        item_id (int): The ID of the inventory item to be removed from the wishlist.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['customer', 'admin']) - Restricts access to users with "customer" 
        or "admin" roles.

    Returns:
        - 200 OK: If the item is successfully removed from the wishlist.
        - 404 Not Found: If the item is not found in the customer's wishlist.
        - 500 Internal Server Error: If an exception occurs during the process.

    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)

        item = get_item_details(item_id)

        wishlist_item = db_session.query(Wishlist).filter(
            Wishlist.customer_id == customer.id,
            Wishlist.item_id == item.id
        ).first()

        if not wishlist_item:
            return jsonify({'message': f"Item {item_id} is not in your wishlist."}), 404

        db_session.delete(wishlist_item)
        db_session.commit()

        return jsonify({'message': f"Item {item_id} removed from wishlist successfully."}), 200

    except Exception as e:
        db_session.rollback()  
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()
        

@app.route('/purchase/<int:item_id>', methods=['POST'])
@jwt_required()
@role_required(['admin', 'customer'])
def purchase_item(item_id):
    """
    Handle item purchase by a logged-in customer and log the order.

    Endpoint:
        POST /purchase/<int:item_id>

    Path Parameter:
        item_id (int): The ID of the inventory item to be purchased.

    Request Body:
        A JSON object containing the following field:
            - quantity (int): The quantity of the item to purchase. Must be a positive integer.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'customer']) - Restricts access to users with "admin" or 
        "customer" roles.

    Returns:
        - 200 OK: If the purchase is successful. Includes a success message and the order ID.
        - 400 Bad Request: If the quantity is invalid, stock is insufficient, or the wallet 
        balance is insufficient.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    quantity = data.get('quantity', 0)

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity. Must be a positive integer.'}), 400

    db_session = SessionLocal()
    try:
        # Get logged-in user's identity
        user = json.loads(get_jwt_identity())
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)

        item = get_item_details(item_id)

        # Check if there is enough stock and if the user has sufficient wallet balance
        total_cost = item.price_per_item * quantity
        if item.stock_count < quantity:
            return jsonify({'error': 'Not enough stock available'}), 400
        if customer.wallet < total_cost:
            return jsonify({'error': 'Insufficient wallet balance'}), 400

        # Deduct from customer's wallet via API
        deduct_wallet_func = current_app.config['DEDUCT_WALLER_DATA_FUNC']
        deduct_wallet_func(user['username'],total_cost,headers)
        
        # Deduct stock via inventory API
        remove_stock_func = current_app.config['REMOVE_STOCK_DATA_FUNC']
        remove_stock_func(item_id,quantity,headers)

        # Log the order in the local database
        new_order = Order(customer_id=customer.id, item_id=item.id, good_name=item.name, quantity=quantity)
        db_session.add(new_order)
        db_session.commit()

        return jsonify({
            "message": f"{customer.username} successfully purchased {quantity} unit(s) of {item.name}.",
            "order_id": new_order.id
        }), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)

    
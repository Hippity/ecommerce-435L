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
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)

#Base.metadata.drop_all(bind=engine)
# Create tables if not created
Base.metadata.create_all(bind=engine)

@app.route('/inventory', methods=['POST'])
@jwt_required()
@role_required(['admin', 'product_manager'])
def add_item():
    """
    Add a new item to the inventory.

    Endpoint:
        POST /inventory

    Request Body:
        A JSON object containing the details of the item to be added. 
            - name (str): The name of the item.
            - description (str): A brief description of the item.
            - price_per_item (float): The price of the item.
            - stock_quantity (int): The available stock quantity of the item.
            - category (str): The category the item belongs to.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'product_manager']) - Restricts access to users with 
        "admin" or "product_manager" roles.

    Returns:
        - 201 Created: If the item is successfully added to the inventory. Includes a success 
        message and the item ID.
        - 400 Bad Request: If the input data is invalid.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    db_session = SessionLocal()
    try:

        is_valid, message = InventoryItem.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        new_item = InventoryItem(**data)
        db_session.add(new_item)
        db_session.commit()

        return jsonify({'message': 'Good added successfully', 'item_id': new_item.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'product_manager'])
def update_item(item_id):
    """
    Update fields related to a specific inventory item.

    Endpoint:
        PUT /inventory/<int:item_id>

    Path Parameter:
        item_id (int): The ID of the inventory item to be updated.

    Request Body:
        A JSON object containing the fields to update.
            - name (str): The name of the item.
            - description (str): A brief description of the item.
            - price_per_item (float): The price of the item.
            - stock_quantity (int): The available stock quantity of the item.
            - category (str): The category the item belongs to.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'product_manager']) - Restricts access to users with 
        "admin" or "product_manager" roles.

    Returns:
        - 200 OK: If the item is successfully updated. Includes a success message.
        - 400 Bad Request: If the input data is invalid.
        - 404 Not Found: If the item with the specified ID does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    db_session = SessionLocal()
    try:     
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        is_valid, message = InventoryItem.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)

        db_session.commit()
        return jsonify({'message': f'Item {item_id} updated successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'product_manager'])
def delete_item(item_id):
    """
    Delete an inventory item and its associated data.

    Endpoint:
        DELETE /inventory/<int:item_id>

    Path Parameter:
        item_id (int): The ID of the inventory item to be deleted.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'product_manager']) - Restricts access to users with 
        "admin" or "product_manager" roles.

    Returns:
        - 200 OK: If the item and its associated data are successfully deleted. 
        - 404 Not Found: If the item with the specified ID does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    db_session = SessionLocal()
    try:
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()

        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        db_session.query(Order).filter_by(item_id=item.id).delete()
        db_session.query(Review).filter_by(item_id=item.id).delete()
        db_session.query(Wishlist).filter_by(item_id=item.id).delete()

        db_session.delete(item)
        db_session.commit()

        return jsonify({'message': f'Item {item_id} deleted successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>/stock/remove', methods=['POST'])
@jwt_required()
@role_required(['admin', 'product_manager','customer'])
def deduct_item(item_id):
    """
    Remove stock from an inventory item.

    Endpoint:
        POST /inventory/<int:item_id>/stock/remove

    Path Parameter:
        item_id (int): The ID of the inventory item whose stock is to be deducted.

    Request Body:
        A JSON object containing the following field:
            - quantity (int): The amount to deduct from the stock. Must be a positive integer.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'product_manager', 'customer']) - Restricts access to users 
        with "admin", "product_manager", or "customer" roles.

    Returns:
        - 200 OK: If the stock is successfully deducted. Includes a success message and the new stock count.
        - 400 Bad Request: If the input quantity is invalid or if there is insufficient stock.error": "Not enough stock available"
        - 404 Not Found: If the item with the specified ID does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    quantity = data.get('quantity', 0)
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity. Must be a positive integer.'}), 400
    
    db_session = SessionLocal()

    try:
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if item.stock_count < quantity:
            return jsonify({'error': 'Not enough stock available'}), 400

        item.stock_count -= quantity
        db_session.commit()

        return jsonify({'message': f'{quantity} items deducted from stock', 'new_stock': item.stock_count}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>/stock/add', methods=['POST'])
@jwt_required()
@role_required(['admin', 'product_manager'])
def add_stock(item_id):
    """
    Add stock to an inventory item.

    Endpoint:
        POST /inventory/<int:item_id>/stock/add

    Path Parameter:
        item_id (int): The ID of the inventory item whose stock is to be increased.

    Request Body:
        A JSON object containing the following field:
            - quantity (int): The amount to add to the stock. Must be a positive integer.

    Decorators:
        @jwt_required() - Ensures the user is authenticated using a JWT token.
        @role_required(['admin', 'product_manager']) - Restricts access to users with 
        "admin" or "product_manager" roles.

    Returns:
        - 200 OK: If the stock is successfully increased. Includes a success message and the new stock count.
        - 400 Bad Request: If the input quantity is invalid.
        - 404 Not Found: If the item with the specified ID does not exist.
        - 500 Internal Server Error: If an exception occurs during the process.
    """
    data = request.json
    quantity = data.get('quantity', 0)

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity. Must be a positive integer.'}), 400
    
    db_session = SessionLocal()

    try:
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        item.stock_count += quantity
        db_session.commit()

        return jsonify({'message': f'Successfully added {quantity} items to stock', 'new_stock': item.stock_count}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3001)
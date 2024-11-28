from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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

# Create tables if not created
Base.metadata.create_all(bind=engine)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)
    
@app.route('/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    """
    Retrieve all items with their name and price.
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

@app.route('/inventory/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item_details(item_id):
    """
    Retrieve detailed information about a specific item.
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
@app.route('/purchase/<int:item_id>', methods=['POST'])
@jwt_required()
def purchase_item(item_id):
    """
    Handle purchasing an item by a logged-in customer and log the order.
    """
    data = request.json
    quantity = data.get('quantity', 0)

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity. Must be a positive integer.'}), 400

    db_session = SessionLocal()
    try:
        # Get logged-in user's identity
        user = json.loads(get_jwt_identity())
        customer = db_session.query(Customer).filter(Customer.username == user["username"]).first()
        item = db_session.query(InventoryItem).filter(InventoryItem.id == item_id).first()

        # Validate customer and item
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Check if there is enough stock and if the user has sufficient wallet balance
        total_cost = item.price_per_item * quantity
        if item.stock_count < quantity:
            return jsonify({'error': 'Not enough stock available'}), 400
        if customer.wallet < total_cost:
            return jsonify({'error': 'Insufficient wallet balance'}), 400

        # Prepare JWT token for API calls
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        # Deduct from customer's wallet via API
        wallet_payload = {"amount": total_cost}
        wallet_response = requests.post(
            f'http://customers-service:3000/customers/{user["username"]}/wallet/deduct',
            json=wallet_payload,
            headers=headers,
            timeout=5
        )
        wallet_response.raise_for_status()  # Raise exception for HTTP errors
        if wallet_response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected from wallet service')

        # Deduct stock via inventory API
        stock_payload = {"quantity": quantity}
        stock_response = requests.post(
            f'http://inventory-service:3001/inventory/{item_id}/remove_stock',
            json=stock_payload,
            headers=headers,
            timeout=5
        )
        stock_response.raise_for_status()  # Raise exception for HTTP errors
        if stock_response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected from inventory service')

        # Log the order in the local database
        new_order = Order(customer_id=customer.id, item_id=item.id, good_name=item.name, quantity=quantity)
        db_session.add(new_order)
        db_session.commit()

        return jsonify({
            "message": f"{customer.username} successfully purchased {quantity} unit(s) of {item.name}.",
            "order_id": new_order.id
        }), 200

    except requests.exceptions.RequestException as e:
        db_session.rollback()
        return jsonify({'error': f'Error in external API call: {str(e)}'}), 500
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)

    
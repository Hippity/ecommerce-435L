from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import get_jwt_identity, jwt_required
import requests
from shared.models.base import Base
from shared.database import engine, SessionLocal
from shared.models.customer import Customer
from shared.models.inventory import InventoryItem

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database tables
Base.metadata.create_all(bind=engine)
# create a database session to interact with database
db_session = SessionLocal()

@app.route('/sales_goods', methods=['GET'])
def get_goods():
    try:
        response = requests.get('http://inventory-service:3001/api/get_goods', timeout=5)
        response.raise_for_status()  
        if response.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unexpected content type; JSON expected'}), 400
        goods = response.json()
        return jsonify(goods), 200

    except requests.exceptions.Timeout:
        return jsonify({'error': 'The request to the inventory service timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Unable to connect to the inventory service'}), 503
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), response.status_code

@app.route('/inventory', methods=['GET'])
def get_inventory():
    """
    Retrieve all available goods with their name and price.
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
def get_item_details(item_id):
    """
    Retrieve detailed information about a specific good.
    """
    db_session = SessionLocal()
    try:
        good = db_session.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if good is None:
            return jsonify({"error": "Item not found"}), 404
        item_details = {
            "id": good.id,
            "name": good.name,
            "category": good.category,
            "price_per_item": good.price_per_item,
            "description": good.description,
            "stock_count": good.stock_count
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
    Handle purchasing an item by a logged-in customer.
    """
    db_session = SessionLocal()
    try:
        # Get the logged-in user
        current_user = db_session.query(Customer).filter(Customer.username == get_jwt_identity()).first()
        if not current_user:
            return jsonify({"error": "User not found"}), 404

        # Get the item details
        good = db_session.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not good:
            return jsonify({"error": "Item not found"}), 404

        # Validate purchase quantity
        quantity = request.json.get("quantity")
        if not quantity or quantity <= 0:
            return jsonify({"error": "Invalid quantity"}), 400

        # Check funds and stock availability
        total_cost = good.price_per_item * quantity
        if current_user.wallet < total_cost:
            return jsonify({"error": "Insufficient funds"}), 400
        if good.stock_count < quantity:
            return jsonify({"error": "Insufficient stock"}), 400

        # Process purchase
        current_user.wallet -= total_cost
        good.stock_count -= quantity
        db_session.commit()

        return jsonify({
            "message": "Purchase successful",
            "remaining_wallet": current_user.wallet,
            "remaining_stock": good.stock_count
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)

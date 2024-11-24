from flask import Flask, json, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt_identity, jwt_required
import requests
from shared.database import engine, SessionLocal
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database tables
Base.metadata.create_all(bind=engine)
# create a database session to interact with database


# Configure JWT
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)
    
@app.route('/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    """
    Retrieve all inventory with their name and price.
    """
    try:
        response = requests.get('http://inventory-service:3001/inventory', timeout=5)
        response.raise_for_status()  
        if response.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unexpected content type; JSON expected'}), 400
        inventory = response.json()
        return jsonify(inventory), 200

    except requests.exceptions.Timeout:
        return jsonify({'error': 'The request to the inventory service timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Unable to connect to the inventory service'}), 503
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), response.status_code

@app.route('/inventory/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item_details(item_id):
    """
    Retrieve all available goods with their name and price.
    """
    try:
        response = requests.get(f'http://inventory-service:3001/inventory/{item_id}', timeout=5)
        response.raise_for_status()  
        if response.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unexpected content type; JSON expected'}), 400
        item = response.json()
        return jsonify(item), 200
    
    except requests.exceptions.Timeout:
        return jsonify({'error': 'The request to the inventory service timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Unable to connect to the inventory service'}), 503
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), response.status_code

@app.route('/purchase/<int:item_id>', methods=['POST'])
@jwt_required()
def purchase_item(item_id):
    """
    Handle purchasing an item by a logged-in customer.
    """
    quantity = request.json.get("quantity")
    db_session = SessionLocal()
    try:        
        user = json.loads(get_jwt_identity()) 
        response = requests.get(f'http://inventory-service:3001/inventory/{item_id}', timeout=5)
        response.raise_for_status()  
        if response.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unexpected content type; JSON expected'}), 400
        item = response.json()
        if item["stock_count"]>quantity and user["wallet"]>= item["price_per_item"]*quantity:
            response = requests.post(
            f'http://customers-service:3000/customers/{user["username"]}/wallet/deduct',
            json={"amount": item["price_per_item"]*quantity}, 
            timeout=5
            ) 
            response.raise_for_status()  
        if response.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unexpected content type; JSON expected'}), 400
        response = requests.post(
        f'http://inventory-service:3001/inventory/{item_id}/remove_stock',
        json={"quantity": quantity}, 
        timeout=5
        ) 
        response.raise_for_status()  
        if response.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unexpected content type; JSON expected'}), 400
        return jsonify({'message': 'Successful purchased '}), 200
    
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)
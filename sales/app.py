from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
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
    Retrieve all inventory with their name and price.
    """
    try:
        response = requests.get('http://inventory-service:3001/inventory', timeout=5)
        response.raise_for_status()  

        if response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected')
        
        inventory = response.json()
        return jsonify(inventory), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
            raise Exception('Unexpected content type: JSON expected')

        item = response.json()
        return jsonify(item), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/purchase/<int:item_id>', methods=['POST'])
@jwt_required()
def purchase_item(item_id):
    """
    Handle purchasing an item by a logged-in customer.
    """
    data = request.json
    quantity = data.get('quantity', 0)

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity. Must be a positive integer.'}), 400
    
    try:        
        user = json.loads(get_jwt_identity()) 

        response = requests.get(f'http://inventory-service:3001/inventory/{item_id}', timeout=5)
        response.raise_for_status()  

        if response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected')
        
        item = response.json()

        if item["stock_count"]>quantity and user["wallet"]>= item["price_per_item"]*quantity:

            response = requests.post(
            f'http://customers-service:3000/customers/{user["username"]}/wallet/deduct',
            json={"amount": item["price_per_item"]*quantity}, 
            timeout=5
            ) 
            response.raise_for_status()  
            
            if response.headers.get('Content-Type') != 'application/json':
                raise Exception('Unexpected content type: JSON expected')
            
            response = requests.post(
            f'http://inventory-service:3001/inventory/{item_id}/remove_stock',
            json={"quantity": quantity}, 
            timeout=5
            ) 
            response.raise_for_status()  

            if response.headers.get('Content-Type') != 'application/json':
                raise Exception('Unexpected content type: JSON expected')
        
        return jsonify({'message': f'{user['username']} successfully purchased {quantity} unit(s) of {item['name']}'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)
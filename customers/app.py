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

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)

# Create tables if not created
Base.metadata.create_all(bind=engine)

@app.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """Get all customers."""
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
                'wallet': customer.wallet
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
def get_customer_by_username(username):
    """Get customer information by username."""
    db_session = SessionLocal()
    try:
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
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers', methods=['POST'])
def add_customer():
    """Register a new customer."""
    data = request.json
    db_session = SessionLocal()
    try:
        existing_customer = db_session.query(Customer).filter_by(username=data.get('username')).first()
        if existing_customer:
            return jsonify({'error': 'Username is already taken'}), 400
        
        is_valid, message = Customer.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        new_customer = Customer(**data)
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
def update_customer(username):
    """Update customer information."""
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if user['username'] != username:
            return jsonify({'error': 'Invalid User'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        is_valid, message = Customer.validate_data(data)
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

@app.route('/customers/<string:username>', methods=['DELETE'])
@jwt_required()
def delete_customer(username):
    """Delete a customer by username."""
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if user['username'] != username:
            return jsonify({'error': 'Invalid User'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

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
def charge_customer_wallet(username):
    """Add to a customer's wallet."""
    data = request.json
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if user['username'] != username:
            return jsonify({'error': 'Invalid User'}), 400
        
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404

        customer.wallet += amount
        db_session.commit()
        return jsonify({'message': f'Charged ${amount} to {username}\'s wallet', 'new_balance': customer.wallet}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<string:username>/wallet/deduct', methods=['POST'])
@jwt_required()
def deduct_customer_wallet(username):
    """Deduct money from a customer's wallet."""
    data = request.json
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        if user['username'] != username:
            return jsonify({'error': 'Invalid User'}), 400

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)

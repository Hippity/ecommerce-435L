import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, request, jsonify
from flask_cors import CORS
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
from flask_jwt_extended import JWTManager, create_access_token

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

# Create tables if not created
Base.metadata.create_all(bind=engine)

@app.route('/customers', methods=['GET'])
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

@app.route('/customers', methods=['POST'])
def add_customer():
    """Register a new customer."""
    data = request.json
    db_session = SessionLocal()
    try:
        # Check for existing username
        existing_customer = db_session.query(Customer).filter_by(username=data.get('username')).first()
        if existing_customer:
            return jsonify({'error': 'Username is already taken'}), 400
        
        # Validate input data
        is_valid, message = Customer.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Create and save new customer
        new_customer = Customer(**data)
        db_session.add(new_customer)
        db_session.commit()

        return jsonify({'message': 'Customer added successfully', 'customer_id': new_customer.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/customers/<username>', methods=['DELETE'])
def delete_customer(username):
    """Delete a customer by username."""
    db_session = SessionLocal()
    try:
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

@app.route('/customers/<username>', methods=['PUT'])
def update_customer(username):
    """Update customer information."""
    data = request.json
    db_session = SessionLocal()
    try:
        customer = db_session.query(Customer).filter_by(username=username).first()
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        is_valid, message = Customer.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Update fields dynamically
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

@app.route('/customers/<username>', methods=['GET'])
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

@app.route('/customers/<username>/wallet/charge', methods=['POST'])
def charge_customer_wallet(username):
    """Charge a customer's wallet."""
    data = request.json
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    db_session = SessionLocal()
    try:
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

@app.route('/customers/<username>/wallet/deduct', methods=['POST'])
def deduct_customer_wallet(username):
    """Deduct money from a customer's wallet."""
    data = request.json
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    db_session = SessionLocal()
    try:
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

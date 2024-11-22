import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, request, jsonify 
from flask_cors import CORS
from shared.models.base import Base 
from shared.models.customer import Customer
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Create tables if not created
Base.metadata.create_all(bind=engine)
# Database session
db_session = SessionLocal()

@app.route('/customers', methods=['GET'])
def get_customers():
    try:
        customers = db_session.query(Customer).all()
        return jsonify(customers), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/customers', methods=['POST'])
def add_customer():
    data = request.json
    try:
        # Check if username is unique
        existing_customer = db_session.query(Customer).filter_by(username=data.get('username')).first()
        if existing_customer:
            return jsonify({'error': 'Username is already taken'}), 400

        # Create a new customer
        new_customer = Customer(
            fullname=data.get('fullname'),
            username=data.get('username'),
            password=data.get('password'), 
            age=data.get('age'),
            address=data.get('address'),
            gender=data.get('gender'),
            marital_status=data.get('marital_status')
        )
        db_session.add(new_customer)
        db_session.commit()

        return jsonify({'message': 'Customer added successfully', 'customer_id': new_customer.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)
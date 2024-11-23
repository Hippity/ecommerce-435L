import sys
import os

from flask_jwt_extended import create_access_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, request, jsonify 
from flask_cors import CORS
from shared.models.base import Base 
from shared.models.customer import Customer
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
from flask_jwt_extended import JWTManager

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Set the secret key for JWTs
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
# Initialize JWTManager
jwt = JWTManager(app)

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
            marital_status=data.get('marital_status'),
            wallet=data.get('wallet'),
        )
        db_session.add(new_customer)
        db_session.commit()

        return jsonify({'message': 'Customer added successfully', 'customer_id': new_customer.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route("/login", methods=['POST'])
def login():
    try:  
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        db_session = SessionLocal()
        try:
            user = db_session.query(Customer).filter(Customer.username == username).first()

            if not user or user.password != password:  
                return jsonify({"error": "Invalid username or password"}), 401

            access_token = create_access_token(identity=username)
            return jsonify({"access_token": access_token}), 200
        finally:
            db_session.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)
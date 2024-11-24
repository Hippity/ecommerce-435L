from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os

from flask_jwt_extended import create_access_token
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

Base.metadata.create_all(bind=engine)


# Configure JWT
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)


@app.route("/login", methods=['GET'])
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
            access_token = create_access_token(identity=json.dumps({"username": username}))
            return jsonify({"access_token": access_token}), 200
        finally:
            db_session.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3004)
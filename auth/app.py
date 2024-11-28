from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
from functools import wraps
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

Base.metadata.create_all(bind=engine)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)

ph = PasswordHasher()

def create_default_admin():
    """Create a default admin user if none exists."""
    db_session = SessionLocal()
    try:
        existing_admin = db_session.query(Customer).filter_by(role="admin").first()
        if not existing_admin:
            admin = Customer(
                fullname="Admin User",
                username="admin",
                age = 0,
                address = "Admin's address",
                gender = "men",
                marital_status = "single",
                password=ph.hash("admin123"), 
                role="admin",
                wallet=0.0
            )
            db_session.add(admin)
            db_session.commit()
            print("Default admin created successfully!")
    except Exception as e:
        db_session.rollback()
        print(f"Error creating admin: {e}")
    finally:
        db_session.close()

@app.route("/login", methods=['POST'])
def login():
    """Authenticate a user and return the access token."""
    data = request.json
    db_session = SessionLocal()
    try:
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        user = db_session.query(Customer).filter(Customer.username == username).first()
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401

        try:
            ph.verify(user.password, password) 
        except VerifyMismatchError:
            return jsonify({"error": "Invalid username or password"}), 401

        access_token = create_access_token(identity=json.dumps({"username": username, "role": user.role, "wallet": user.wallet}))

        return jsonify({"access_token": access_token}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()
    
def role_required(allowed_roles):
    """
    A decorator to restrict access to specific roles.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                identity = json.loads(get_jwt_identity())
                user_role = identity.get("role")

                if user_role not in allowed_roles:
                    return jsonify({"error": "Permission denied: Insufficient role"}), 403

                return func(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": f"Role validation failed: {str(e)}"}), 500
        return wrapper
    return decorator

    
if __name__ == '__main__':
    create_default_admin()
    app.run(host="0.0.0.0", port=3004)
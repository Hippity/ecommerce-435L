from flask import Flask, request, jsonify 
from flask_cors import CORS
from flask_jwt_extended import get_jwt_identity, jwt_required
from shared.models.base import Base
from shared.database import engine, SessionLocal
from shared.models.customer import Customer
from shared.models.inventory import InventoryItem

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

Base.metadata.create_all(bind=engine)
# create a database session to interact with database
db_session = SessionLocal()

@app.route('/sales_goods', methods=['GET'])
def get_goods():
    try: 
        goods = db_session.query(InventoryItem.name, InventoryItem.price_per_item).all()
        json_results = [{"name": name, "price": price} for name, price in goods]
        return jsonify(json_results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sales_goods/<int:good_id>', methods=['GET'])
def get_goodsById(good_id):
    try:
        if not good_id:
            return jsonify({"error": "Good ID is required"}), 400
        good = db_session.query(InventoryItem).filter(InventoryItem.id == good_id).first()
        if good is None:
            return jsonify({"error": f"No good found"}), 404
        return jsonify(good), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/sales_goods/<int:good_id>/purchase', methods=['POST'])
@jwt_required()
def good_purchase(good_id):
    try:
        current_user = db_session.query(Customer).filter(Customer.username == get_jwt_identity()).first()
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        good = db_session.query(InventoryItem).filter(InventoryItem.id == good_id).first()
        if not good:
            return jsonify({"error": "Good not found"}), 404

        # validate the quantity in the request body
        quantity = request.json.get("quantity")
        if not quantity or quantity <= 0:
            return jsonify({"error": "Invalid quantity"}), 400

        # check if the user has enough money and the stock is sufficient
        total_cost = good.price_per_item * quantity
        if current_user.wallet < total_cost:
            return jsonify({"error": "Insufficient funds"}), 400
        if good.stock_count < quantity:
            return jsonify({"error": "Insufficient stock"}), 400

        current_user.wallet -= total_cost
        good.stock_count -= quantity

        db_session.commit()

        return jsonify({"message": "Purchase successful", "remaining_wallet": current_user.wallet, "remaining_stock": good.stock_count}), 200
    except Exception as e:
        db_session.rollback() 
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)
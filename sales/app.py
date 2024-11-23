from flask import Flask, request, jsonify 
from flask_cors import CORS
from flask_jwt_extended import get_jwt_identity, jwt_required
from shared.models.base import Base
from shared.database import engine, SessionLocal
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
def get_goods(good_id):
    try:
        if not good_id:
            return jsonify({"error": "Good ID is required"}), 400
        good = db_session.query(InventoryItem).filter(InventoryItem.id == good_id).first()
        if good is None:
            return jsonify({"error": f"No good found"}), 404
        return jsonify(good), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/sales_goods/<int:good_id>/purchase')
@jwt_required()
def good_purchase():
    try:
        good_name = request.json.get("good_name")
        quantity = request.json.get("quantity")
        good = db_session.query(InventoryItem).filter(InventoryItem.name == good_name).first()
        current_user = get_jwt_identity()
        # if the user has enough money and the product is available, make the transaction
        if current_user.wallet >= good.price_per_item*quantity and good.stock_count>=quantity:
            current_user.wallet -= good.price_per_item*quantity
            good.stock_count -= quantity
            return jsonify({"Purchase successful"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)
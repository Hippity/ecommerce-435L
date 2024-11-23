from flask import Flask, request, jsonify 
from flask_cors import CORS
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)
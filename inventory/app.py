from flask import Flask, request, jsonify 
from flask_cors import CORS
from shared.models.base import Base
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

Base.metadata.create_all(bind=engine)
db_session = SessionLocal()

@app.route('/inventory/add_good', methods=['POST'])
def add_customer():
    data = request.json
    try:
        new_good = InventoryItem(
            name = data.get("name"),
            category = data.get("category"),
            price_per_item = data.get("price_per_item"),
            description = data.get("description"),
            stock_count = data.get("stock_count"),
        )  
        db_session.add(new_good)
        db_session.commit()

        return jsonify({'message': 'Good added successfully', 'good_id': new_good.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_goods', methods=['GET'])
def get_goods():
    try: 
        goods = db_session.query(InventoryItem.name, InventoryItem.price_per_item).all()
        json_results = [{"name": name, "price": price} for name, price in goods]
        return jsonify(json_results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3001)
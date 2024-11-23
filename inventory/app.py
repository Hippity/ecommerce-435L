from flask import Flask, request, jsonify
from flask_cors import CORS
from shared.models.base import Base
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

Base.metadata.create_all(bind=engine)

# Add a new item to the inventory
@app.route('/inventory/', methods=['POST'])
def add_item():
    """Add a new item to the inventory."""
    data = request.json
    try:
        db_session = SessionLocal()

        # Validate input data
        is_valid, message = InventoryItem.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Create and save the new item
        new_item = InventoryItem(**data)
        db_session.add(new_item)
        db_session.commit()

        return jsonify({'message': 'Good added successfully', 'item_id': new_item.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Deduct stock for an item
@app.route('/inventory/<int:item_id>/remove_stock', methods=['POST'])
def deduct_item(item_id):
    """Remove stock from an item."""
    data = request.json
    quantity = data.get('quantity', 0)
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity. Must be a positive integer.'}), 400

    try:
        db_session = SessionLocal()
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if item.stock_count < quantity:
            return jsonify({'error': 'Not enough stock available'}), 400

        item.stock_count -= quantity
        db_session.commit()

        return jsonify({'message': f'{quantity} items deducted from stock', 'new_stock': item.stock_count}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>/add_stock', methods=['POST'])
def add_stock(item_id):
    data = request.json
    quantity = data.get('quantity', 0)

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Invalid quantity. Must be a positive integer.'}), 400

    try:
        db_session = SessionLocal()
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        item.stock_count += quantity
        db_session.commit()

        return jsonify({'message': f'Successfully added {quantity} items to stock', 'new_stock': item.stock_count}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Update an existing item
@app.route('/inventory/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update fields related to a specific inventory item."""
    data = request.json
    try:
        db_session = SessionLocal()
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Update fields dynamically
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)

        db_session.commit()
        return jsonify({'message': f'Item {item_id} updated successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        db_session = SessionLocal()
        item = db_session.query(InventoryItem).filter_by(id=item_id).first()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        db_session.delete(item)
        db_session.commit()

        return jsonify({'message': f'Item {item_id} deleted successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

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
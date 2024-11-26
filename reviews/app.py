from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

# Create tables if not created
Base.metadata.create_all(bind=engine)

# Get details of a specific review.
@app.route('/reviews/<int:review_id>', methods=['GET'])
@jwt_required()
def get_review_details(review_id):
    """Get details of a specific review."""
    db_session = SessionLocal()
    try:
        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404

        review_details = {
            'id': review.id,
            'customer_id': review.customer_id,
            'item_id': review.item_id,
            'rating': review.rating,
            'comment': review.comment,
            'status': review.status,
            'created_at': review.created_at,
        }
        return jsonify(review_details), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Get all reviews submitted by a specific customer.
@app.route('/reviews/customer/', methods=['GET'])
@jwt_required()
def get_customer_reviews():
    """Get all reviews submitted by a specific customer."""
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        response = requests.get(f'http://customer-service:3000/customer/{user['username']}', timeout=5)
        response.raise_for_status()  

        if response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected')

        customer = response.json()
        reviews = db_session.query(Review).filter_by(customer_id=customer.id).all()

        if not reviews:
            return jsonify({'message': 'No reviews found for this customer'}), 404

        review_list = [
            {
                'id': review.id,
                'item_id': review.item_id,
                'rating': review.rating,
                'comment': review.comment,
                'status': review.status,
                'created_at': review.created_at,
            }
            for review in reviews
        ]
        return jsonify(review_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/reviews/product/<int:item_id>', methods=['GET'])
@jwt_required()
def get_product_reviews(item_id):
    """Get all reviews for a specific product."""
    db_session = SessionLocal()
    try:
        reviews = db_session.query(Review).filter_by(item_id=item_id).all()
        if not reviews:
            return jsonify({'message': 'No reviews found for this product'}), 404

        review_list = [
            {
                'id': review.id,
                'customer_id': review.customer_id,
                'rating': review.rating,
                'comment': review.comment,
                'status': review.status,
                'created_at': review.created_at,
            }
            for review in reviews
        ]
        return jsonify(review_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Submit a new review
@app.route('/reviews/<int:item_id>', methods=['POST'])
@jwt_required()
def submit_review(item_id):
    """Submit a new review."""
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        response = requests.get(f'http://customer-service:3000/customer/{user['username']}', timeout=5)
        response.raise_for_status()  

        if response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected')

        customer = response.json()
        # Validate review data
        is_valid, message = Review.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Create and save the review
        new_review = Review(
            customer_id=customer.id,
            item_id=item_id,
            rating=data["rating"],
            comment=data.get("comment"),
            status=data.get("status", "approved").lower()
        )
        db_session.add(new_review)
        db_session.commit()
        return jsonify({'message': 'Review submitted successfully', 'review_id': new_review.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Update an existing review.
@app.route('/reviews/<int:review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    """Update an existing review."""
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity()) 

        response = requests.get(f'http://customer-service:3000/customer/{user['username']}', timeout=5)
        response.raise_for_status()  

        if response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected')

        customer = response.json()

        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        is_valid, message = Review.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        if review.customer_id != customer.id:
            return jsonify({'error': "User cannot update this review"}), 400

        for key, value in data.items():
            if hasattr(review, key):
                setattr(review, key, value)

        db_session.commit()
        return jsonify({'message': 'Review updated successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Delete a review.
@app.route('/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """Delete a review."""
    db_session = SessionLocal()
    try:

        user = json.loads(get_jwt_identity()) 

        response = requests.get(f'http://customer-service:3000/customer/{user['username']}', timeout=5)
        response.raise_for_status()  

        if response.headers.get('Content-Type') != 'application/json':
            raise Exception('Unexpected content type: JSON expected')

        customer = response.json()

        review = db_session.query(Review).filter_by(id=review_id).first()

        if review.customer_id != customer.id:
            return jsonify({'error': "User cannot delete this review"}), 400

        if not review:
            return jsonify({'error': 'Review not found'}), 404

        db_session.delete(review)
        db_session.commit()
        return jsonify({'message': 'Review deleted successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Flag a review
@app.route('/reviews/flag/<int:review_id>', methods=['PUT'])
@jwt_required()
def moderate_review(review_id):
    """Flag a review"""
    db_session = SessionLocal()
    try:
        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404

        review.status = 'flagged'
        db_session.commit()
        return jsonify({'message': f'Review {review_id} flagged successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

# Approve a review
@app.route('/reviews/approve/<int:review_id>', methods=['PUT'])
@jwt_required()
def moderate_review(review_id):
    """Approve a review"""
    db_session = SessionLocal()
    try:
        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404

        review.status = 'approved'
        db_session.commit()
        return jsonify({'message': f'Review {review_id} approved successfully'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)

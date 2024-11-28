from flask import Flask, json, request, jsonify, current_app
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from auth.app import role_required
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
app.config['JWT_SECRET_KEY'] = 'secret-key'
jwt = JWTManager(app)

#Base.metadata.drop_all(bind=engine)
# Create tables if not created
Base.metadata.create_all(bind=engine)

# Get details of a specific review.
@app.route('/reviews/<int:review_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'moderator'])
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
@role_required(['admin', 'customer', 'moderator'])
def get_customer_reviews():
    """Get all reviews submitted by a specific customer."""
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        customer = db_session.query(Customer).filter_by(username=user['username']).first()

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
@role_required(['admin', 'product_manager', 'moderator'])
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
@role_required(['customer'])
def submit_review(item_id):
    """Submit a new review."""
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        customer = db_session.query(Customer).filter_by(username=user['username']).first()

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
@role_required(['customer'])
def update_review(review_id):
    """Update an existing review."""
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        customer = db_session.query(Customer).filter_by(username=user['username']).first()

        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404

        if review.customer_id != customer.id:
            return jsonify({'error': "User cannot update this review"}), 400

        updated_review = {
            "rating": data.get("rating") or review.rating,
            "comment": data.get("comment") or review.comment,
            "status": data.get("status") or review.status
        }

        is_valid, message = Review.validate_data(updated_review)
        if not is_valid:
            return jsonify({'error': message}), 400

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
@role_required(['admin', 'customer', 'moderator'])
def delete_review(review_id):
    """Delete a review."""
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        customer = db_session.query(Customer).filter_by(username=user['username']).first()

        review = db_session.query(Review).filter_by(id=review_id).first()

        if not review:
            return jsonify({'error': 'Review not found'}), 404

        if review.customer_id != customer.id:
            return jsonify({'error': "User cannot delete this review"}), 400

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
@role_required(['admin', 'product_manager', 'moderator'])
def flag_review(review_id):
    """Flag a review."""
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
@role_required(['admin', 'product_manager', 'moderator'])
def approve_review(review_id):
    """Approve a review."""
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

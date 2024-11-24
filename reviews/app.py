from flask import Flask, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from shared.database import SessionLocal
from shared.models.base import Base
from shared.models.customer import Customer
from shared.models.review import Review
from shared.models.inventory import InventoryItem
from shared.database import engine, SessionLocal
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

Base.metadata.create_all(bind=engine)

@app.route('/reviews', methods=['POST'])
def submit_review():
    """Submit a new review."""
    data = request.json
    db_session = SessionLocal()
    try:
        # Validate review data
        is_valid, message = Review.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Create and save the review
        new_review = Review(
            customer_id=data["customer_id"],
            item_id=data["item_id"],
            rating=data["rating"],
            comment=data.get("comment"),
            status=data.get("status", "pending").lower()
        )
        db_session.add(new_review)
        db_session.commit()
        return jsonify({'message': 'Review submitted successfully', 'review_id': new_review.id}), 201
    except IntegrityError:
        db_session.rollback()
        return jsonify({'error': 'Duplicate review or invalid customer/item reference'}), 400
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    """Update an existing review."""
    data = request.json
    db_session = SessionLocal()
    try:
        # Find the review
        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        is_valid, message = Review.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

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

@app.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Delete a review."""
    db_session = SessionLocal()
    try:
        review = db_session.query(Review).filter_by(id=review_id).first()
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

@app.route('/reviews/product/<int:item_id>', methods=['GET'])
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

@app.route('/reviews/customer/<int:customer_id>', methods=['GET'])
def get_customer_reviews(customer_id):
    """Get all reviews submitted by a specific customer."""
    db_session = SessionLocal()
    try:
        reviews = db_session.query(Review).filter_by(customer_id=customer_id).all()
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

@app.route('/reviews/moderate/<int:review_id>', methods=['PUT'])
def moderate_review(review_id):
    """Moderate a review (approve or flag)."""
    data = request.json
    db_session = SessionLocal()
    try:
        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404

        if "status" not in data or data["status"].lower() not in ["approved", "flagged"]:
            return jsonify({'error': 'Invalid status. Must be "approved" or "flagged".'}), 400

        review.status = data["status"].lower()
        db_session.commit()
        return jsonify({'message': f'Review {review_id} moderated successfully to {review.status}'}), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@app.route('/reviews/<int:review_id>', methods=['GET'])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)

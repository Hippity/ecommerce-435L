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

def get_customer_details(username,headers):
    """
    Retrieve customer data from the customer service.

    Parameters:
        username (str): The username of the customer whose details are to be retrieved.
        headers (dict): A dictionary of HTTP headers to include in the request. Typically includes 
                        authentication headers.

    Returns:
        dict: A JSON object containing customer details if the request is successful.
        rasies an exception

    """
    response = requests.get(f'http://customer-service:3000/customers/{username}', timeout=5, headers=headers)
    response.raise_for_status()
    if response.headers.get('Content-Type') != 'application/json':
        raise Exception('Unexpected content type: JSON expected')
    return response.json()

app.config['GET_CUSTOMER_DATA_FUNC'] = get_customer_details

#Base.metadata.drop_all(bind=engine)
# Create tables if not created
Base.metadata.create_all(bind=engine)

# Get details of a specific review.
@app.route('/reviews/<int:review_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'product_manager','customer'])
def get_review_details(review_id):
    """
    Get details of a specific review.

    Endpoint:
        GET /reviews/<int:review_id>

    Path Parameter:
        review_id (int): The ID of the review to retrieve.

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['admin', 'product_manager', 'customer']) - Restricts access based on roles.

    Returns:
        - 200 OK: JSON object containing the review details.
        - 404 Not Found: If the review does not exist.
        - 500 Internal Server Error: If an error occurs.
    """
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
@role_required(['admin', 'customer'])
def get_customer_reviews():
    """
    Get all reviews submitted by a specific customer.

    Endpoint:
        GET /reviews/customer/

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['admin', 'customer']) - Restricts access based on roles.

    Returns:
        - 200 OK: JSON list of reviews submitted by the customer.
        - 404 Not Found: If the customer has no reviews.
        - 500 Internal Server Error: If an error occurs.
    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)

        reviews = db_session.query(Review).filter_by(customer_id=customer["id"]).all()

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
@role_required(['admin', 'product_manager', 'customer'])
def get_product_reviews(item_id):
    """
    Get all reviews for a specific product.

    Endpoint:
        GET /reviews/product/<int:item_id>

    Path Parameter:
        item_id (int): The ID of the product to retrieve reviews for.

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['admin', 'product_manager', 'customer']) - Restricts access based on roles.

    Returns:
        - 200 OK: JSON list of reviews for the specified product.
        - 404 Not Found: If no reviews exist for the product.
        - 500 Internal Server Error: If an error occurs.
    """
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
@role_required(['customer','admin'])
def submit_review(item_id):
    """
    Submit a new review.

    Endpoint:
        POST /reviews/<int:item_id>

    Path Parameter:
        item_id (int): The ID of the product to review.

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['customer']) - Restricts access to customers only.

    Request Body:
        JSON object containing:
            - rating (int): Rating for the product (required).
            - comment (str): Optional comment for the review.
            - status (str): Optional status of the review (default: "approved").

    Returns:
        - 201 Created: If the review is successfully submitted.
        - 400 Bad Request: If validation fails.
        - 500 Internal Server Error: If an error occurs.

    """
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)

        # Validate review data
        is_valid, message = Review.validate_data(data)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Create and save the review
        new_review = Review(
            customer_id=customer["id"],
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
@role_required(['customer','admin'])
def update_review(review_id):
    """
    Update an existing review.

    Endpoint:
        PUT /reviews/<int:review_id>

    Path Parameter:
        review_id (int): The ID of the review to update.

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['customer']) - Restricts access to customers only.

    Request Body:
        JSON object containing:
            - rating (int): Updated rating for the product.
            - comment (str): Updated comment for the review.
            - status (str): Updated status of the review.

    Returns:
        - 200 OK: If the review is successfully updated.
        - 400 Bad Request: If validation fails or if the user is not authorized.
        - 404 Not Found: If the review does not exist.
        - 500 Internal Server Error: If an error occurs.

    """
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)

        review = db_session.query(Review).filter_by(id=review_id).first()
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        if 'admin' not in user['role'] and review.customer_id != customer["id"]:
            return jsonify({'error': 'Invalid user'}), 400

        is_valid, message = Review.validate_data(data,)
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

# Delete a review.
@app.route('/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin', 'customer'])
def delete_review(review_id):
    """
    Delete a review.

    Endpoint:
        DELETE /reviews/<int:review_id>

    Path Parameter:
        review_id (int): The ID of the review to delete.

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['admin', 'customer']) - Restricts access to admins and customers.

    Returns:
        - 200 OK: If the review is successfully deleted.
        - 400 Bad Request: If the user is not authorized.
        - 404 Not Found: If the review does not exist.
        - 500 Internal Server Error: If an error occurs.
    """
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())
        
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)

        review = db_session.query(Review).filter_by(id=review_id).first()

        if not review:
            return jsonify({'error': 'Review not found'}), 404

        if 'admin' not in user['role'] and review.customer_id != customer["id"]:
            return jsonify({'error': 'Invalid user'}), 400

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
@role_required(['admin', 'product_manager', 'customer'])
def flag_review(review_id):
    """
    Flag a review.

    Endpoint:
        PUT /reviews/flag/<int:review_id>

    Path Parameter:
        review_id (int): The ID of the review to flag.
    
    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['admin', 'product_manager', 'customer']) - Restricts access based on roles.

    Returns:
        - 200 OK: If the review is successfully flagged.
        - 404 Not Found: If the review does not exist.
        - 500 Internal Server Error: If an error occurs.
    """
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
@role_required(['admin', 'product_manager'])
def approve_review(review_id):
    """
    Approve a review.

    Endpoint:
        PUT /reviews/approve/<int:review_id>

    Path Parameter:
        review_id (int): The ID of the review to approve.

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['admin', 'product_manager']) - Restricts access to admins and product managers.

    Returns:
        - 200 OK: If the review is successfully approved.
        - 404 Not Found: If the review does not exist.
        - 500 Internal Server Error: If an error occurs.
    """
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

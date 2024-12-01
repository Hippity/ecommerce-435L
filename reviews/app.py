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
from sqlalchemy.sql import text
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json
from better_profanity import profanity
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

def get_item_exists(item_id,headers):
    """
    Retrieve item data from the inventory service.

    Parameters:
        username (str): The username of the customer whose details are to be retrieved.
        headers (dict): A dictionary of HTTP headers to include in the request. Typically includes 
                        authentication headers.

    Returns:
        dict: A JSON object containing customer details if the request is successful.
        rasies an exception

    """
    response = requests.get(f'http://invenotry-service:3001/inventory/{item_id}', timeout=5, headers=headers)
    response.raise_for_status()
    if response.headers.get('Content-Type') != 'application/json':
        raise Exception('Unexpected content type: JSON expected')
    return True

app.config['GET_CUSTOMER_DATA_FUNC'] = get_customer_details
app.config['GET_ITEM_EXISTS_FUNC'] = get_item_exists

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
        user = json.loads(get_jwt_identity())

        # Get customer details
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
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

profanity.load_censor_words()

@app.route('/reviews/<int:item_id>', methods=['POST'])
@jwt_required()
@role_required(['customer', 'admin'])
def submit_review(item_id):
    """
    Submit a new review.

    Endpoint:
        POST /reviews/<int:item_id>

    Path Parameter:
        item_id (int): The ID of the product to review.

    Decorators:
        @jwt_required() - Requires authentication via JWT.
        @role_required(['customer', 'admin']) - Restricts access to customers and admins.

    Request Body:
        JSON object containing:
            - rating (int): Rating for the product (required).
            - comment (str): Optional comment for the review.
            - status (str): Optional status of the review (default: "approved").

    Returns:
        - 201 Created: If the review is successfully submitted.
        - 404 Not Found: If item doesn't exist
        - 400 Bad Request: If validation fails.
        - 500 Internal Server Error: If an error occurs.
    """
    data = request.json
    db_session = SessionLocal()
    try:
        user = json.loads(get_jwt_identity())

        # Get customer details
        jwt_token = create_access_token(identity=get_jwt_identity())
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        get_customer_data_func = current_app.config['GET_CUSTOMER_DATA_FUNC']
        customer = get_customer_data_func(user['username'],headers)
        
        get_item_exists_func = current_app.config['GET_ITEM_EXISTS_FUNC']
        item = get_item_exists_func(item_id, headers)
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Validate review data
        if not isinstance(data.get("rating"), int) or not (1 <= data["rating"] <= 5):
            return jsonify({'error': 'Invalid rating. Must be an integer between 1 and 5.'}), 400

        comment = data.get("comment", "").strip()
        if len(comment) > 500:
            return jsonify({'error': 'Comment exceeds maximum length of 500 characters.'}), 400

        # Check for profanity using `better-profanity`
        if comment and profanity.contains_profanity(comment):
            return jsonify({'error': 'Inappropriate comment detected.'}), 400

        # Create and save the review
        new_review = Review(
            customer_id=customer["id"],
            item_id=item_id,
            rating=data["rating"],
            comment=comment,
            status=data.get("status", "approved").lower()
        )
        db_session.add(new_review)
        db_session.commit()

        return jsonify({
            'message': 'Review submitted successfully',
            'review_id': new_review.id
        }), 201

    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Error in submit_review: {str(e)}")
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

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        - 200 OK: If the service and all dependencies are operational.
        - 500 Internal Server Error: If any dependency is not operational.
    """
    db_status = "unknown"
    customer_service_status = "unknown"

    # Check database connectivity
    try:
        db_session = SessionLocal()
        db_session.execute(text("SELECT 1"))
        db_session.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"unavailable: {str(e)}"

    # Check customer-service health
    try:
        response = requests.get('http://customer-service:3000/health', timeout=5)
        if response.status_code == 200:
            customer_service_status = "healthy"
        else:
            customer_service_status = f"unhealthy: {response.status_code}"
    except Exception as e:
        customer_service_status = f"unavailable: {str(e)}"

    # Aggregate overall status
    overall_status = "healthy" if db_status == "connected" and customer_service_status == "healthy" else "unhealthy"

    # Return JSON response
    return jsonify({
        "status": overall_status,
        "database": db_status,
        "customer_service": customer_service_status
    }), 200 if overall_status == "healthy" else 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)

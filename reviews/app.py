from flask import Flask, request, jsonify 
from flask_cors import CORS
from shared.models.base import Base
from shared.database import engine, SessionLocal

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

Base.metadata.create_all(bind=engine)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3002)
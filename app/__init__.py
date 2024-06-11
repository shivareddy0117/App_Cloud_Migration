from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import json
from bson import ObjectId
from pymongo import MongoClient

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

client = MongoClient('mongodb+srv://CloudProjectGroup01:dbhEGgjTGz2WjSGk@cluster0.ejz2u2z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['HoustonTaxiDB']

socket_io = SocketIO()

def create_app():
    app = Flask(__name__, static_url_path='/static')
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.json_encoder = JSONEncoder

    CORS(app)
    socket_io.init_app(app)

    app.config['db'] = db  # Ensure MongoDB client is available globally

    # Import blueprints here to avoid circular imports
    from app.routes import main
    from app.socketio_bp import socketio_bp

    app.register_blueprint(main)
    app.register_blueprint(socketio_bp)

    return app, socket_io

def create_socketio(socket_io):
    @socket_io.on('connect')
    def test_connect():
        print('Client connected')

    @socket_io.on('disconnect')
    def test_disconnect():
        print('Client disconnected')

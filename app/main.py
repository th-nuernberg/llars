from flask import Flask
from flask_socketio import SocketIO
from db.db import configure_database
from routes import configure_routes
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes_socketio import configure_socket_routes

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-geheimer-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

jwt = JWTManager(app)
configure_database(app)
configure_routes(app)
configure_socket_routes(socketio)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8081, debug=True)


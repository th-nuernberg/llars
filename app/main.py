from flask import Flask
from flask_socketio import SocketIO
from db.db import configure_database
# from routes import configure_routes
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes_socketio import configure_socket_routes
from routes import auth_blueprint, data_blueprint
from routes_websocket_prompt_eng import configure_websocket_prompt_eng

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-geheimer-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

jwt = JWTManager(app)
configure_database(app)

# configure routes
# configure_routes(app)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(data_blueprint, url_prefix='/api')


configure_socket_routes(socketio)
configure_websocket_prompt_eng(socketio)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8081, debug=True)


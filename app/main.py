from flask import Flask
from db.db import configure_database
from routes import configure_routes
from flask_jwt_extended import JWTManager
from flask_cors import CORS
# Importiere die Modelle, damit sie von SQLAlchemy erkannt werden

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-geheimer-key'  # Ändere dies zu einem sicheren Schlüssel
CORS(app)
# Initialisiere JWTManager mit der Flask-App
jwt = JWTManager(app)
# Initialisiere die Datenbank mit der Flask-App
configure_database(app)
configure_routes(app)

if __name__ == '__main__':
    app.run(debug=True)

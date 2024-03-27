from flask import Flask
from db.db import configure_database
# Importiere die Modelle, damit sie von SQLAlchemy erkannt werden

app = Flask(__name__)

# Initialisiere die Datenbank mit der Flask-App
configure_database(app)

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)

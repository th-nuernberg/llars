# database/__init__.py
from flask_sqlalchemy import SQLAlchemy

# Initialisieren der SQLAlchemy DB-Instanz
db = SQLAlchemy()

# Importieren der Modelle, um sicherzustellen, dass sie der DB-Instanz bekannt sind
from .tables import User

#!/usr/bin/env python3
from app.db.db import db
from app.main import app

print(f"db type: {type(db)}")
print(f"hasattr(db, 'session') without context: {hasattr(db, 'session')}")

with app.app_context():
    print(f"hasattr(db, 'session') with context: {hasattr(db, 'session')}")
    if hasattr(db, 'session'):
        print(f"db.session type: {type(db.session)}")

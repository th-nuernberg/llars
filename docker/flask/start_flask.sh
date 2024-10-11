#!/bin/sh

echo "Waiting for 2 seconds before starting the Flask app..."
sleep 2

# Führt die Datenbankmigrationen durch, um sicherzustellen, dass die neuesten Änderungen angewendet werden
echo "Running database migrations..."
flask db upgrade

# Startet die Flask-App
echo "Starting Flask app on port 8081..."
flask run --host=0.0.0.0 --port=8081

#!/bin/sh

echo "Waiting for 2 seconds before starting the Flask app..."
sleep 2

# Automatisiere die Migration, um sicherzustellen, dass die Datenbank auf dem neuesten Stand ist
# echo "Running database migrations..."
# flask db upgrade


#ALTER TABLE users ADD COLUMN group_id INT NOT NULL DEFAULT 1;

# Starte die Flask-App
echo "Starting Flask app on port 8081 with hot-reload enabled..."
flask run --host=0.0.0.0 --port=8081 --reload

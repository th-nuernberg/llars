#!/bin/sh
echo "Starting supervisor..."
echo "Waiting for Flask server to start..."
# echo "Checking if Flask server is healthy..."
# Wiederhole den Gesundheitscheck, bis der Server antwortet
while ! curl -s http://backend-flask-service:8081/health_check | grep -q "Server is running"
do
  # echo "Waiting for the Flask server to become healthy..."
  echo "Waiting for the Flask server to become healthy..."
  sleep 1
done


echo "Flask server is healthy."

echo "Step -1: Running Container..."
python -u /supervisor/supervisor.py

echo "Supervisor successfully started."

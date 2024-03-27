#!/bin/sh

# echo "Starting script in the background"
# python your_script.py &
echo "Waiting for 3 seconds before starting the Flask app..."
sleep 5

# export FLASK_APP=main.py
flask run --host=0.0.0.0 --port=8081

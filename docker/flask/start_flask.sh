#!/bin/sh

# echo "Starting script in the background"
# python your_script.py &
echo "Waiting for 2 seconds before starting the Flask app..."
sleep 2

# export FLASK_APP=main.py
flask run --host=0.0.0.0 --port=8081

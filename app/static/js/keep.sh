#!/bin/bash

# Path to the Python app and the Python binary
APP_PATH="/home/ubuntu/aws-community-labs/run.py"
PYTHON_BIN="/home/ubuntu/aws-community-labs/venv/bin/python3"
PORT=5000

# Function to check if the app is running
is_app_running() {
    lsof -i :$PORT | grep LISTEN &> /dev/null
    return $? # Returns 0 if the port is in use, 1 otherwise
}

# Function to kill the app if it's stuck
kill_stale_app() {
    lsof -t -i :$PORT | xargs kill -9 &> /dev/null
}

# Function to start the app
start_app() {
    nohup $PYTHON_BIN $APP_PATH &>/dev/null &
}

# Main script logic
while true; do
    if is_app_running; then
        echo "$(date): App is running on port $PORT."
    else
        echo "$(date): App is not running. Restarting..."
        kill_stale_app
        start_app
        echo "$(date): App restarted."
    fi
    sleep 300 # Wait for 5 minutes before checking again
done
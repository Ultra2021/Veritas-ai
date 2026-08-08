#!/bin/bash
# start.sh
# Start the FastAPI backend in the background
cd /app/backend
# Set host to 127.0.0.1 since the frontend will proxy to it on localhost
uvicorn main:app --host 127.0.0.1 --port 8000 &

# Start the Next.js frontend
cd /app/frontend
exec npm start

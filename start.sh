#!/bin/bash
set -e

export PORT=${PORT:-8080}
export ST_PORT=${STREAMLIT_SERVER_PORT:-8501}

# Substitute environment variables into Nginx config
envsubst '${PORT} ${ST_PORT}' < /app/nginx.conf.template > /etc/nginx/nginx.conf

# Start Streamlit in the background
streamlit run app.py --server.port=${ST_PORT} --server.address=0.0.0.0 &

# Wait for Streamlit to start
sleep 3

# Start Nginx in the foreground
echo "Starting Nginx on port ${PORT} (proxying to ${ST_PORT}) with HTTP/2 enabled..."
nginx -g 'daemon off;'

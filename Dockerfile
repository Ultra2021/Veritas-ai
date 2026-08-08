# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Final Image
FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Setup Backend
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend/ /app/backend/
COPY candidates.json /app/candidates.json
COPY curriculum.json /app/curriculum.json

# Setup Frontend
COPY --from=frontend-builder /app/frontend/package.json /app/frontend/
COPY --from=frontend-builder /app/frontend/package-lock.json /app/frontend/
COPY --from=frontend-builder /app/frontend/.next /app/frontend/.next
COPY --from=frontend-builder /app/frontend/node_modules /app/frontend/node_modules

# Copy start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the frontend port (which proxies to the backend)
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NEXT_TELEMETRY_DISABLED=1
ENV PYTHONPATH=/app/backend

CMD ["/app/start.sh"]

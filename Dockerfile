# Multi-stage Dockerfile: Frontend Builder + Python FastAPI Backend
# Ideal for Render, Railway, Fly.io, and container deployments

# Stage 1: Build the React 19 Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend-react

COPY frontend-react/package*.json ./
RUN npm ci

COPY frontend-react/ ./
RUN npm run build

# Stage 2: Production Python Backend
FROM python:3.12-slim AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install essential runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application backend, data and logic
COPY backend/ ./backend/
COPY cases/ ./cases/
COPY data/ ./data/
COPY kanban_store.py table_store.py boxes_store.py table_mcp.py ./
RUN mkdir -p data/cases data/logs

# Copy compiled frontend from Stage 1 into frontend-react/dist
COPY --from=frontend-builder /app/frontend-react/dist ./frontend-react/dist

EXPOSE 8000

# Run Uvicorn listening on the dynamically assigned $PORT
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

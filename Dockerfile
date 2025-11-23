# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app

# Copy root package files and client package file to leverage workspace support
COPY package*.json ./
COPY client/package.json ./client/

# Install dependencies (using npm ci for reproducible builds)
RUN npm ci

# Copy client source
COPY client/ ./client/

# Build client
WORKDIR /app/client
RUN npm run build

# Stage 2: Setup Python Backend
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (git might be needed for transformers remote code if cloning repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY server_py/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY server_py/ ./server_py/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/client/dist ./client/dist

# Environment setup
ENV STATIC_DIR=/app/client/dist
ENV PORT=3000
ENV DATA_PATH=/app/data

# Create data dir
RUN mkdir -p /app/data

RUN apt-get update && apt-get install -y libvips-dev

# Expose port
EXPOSE 3000

# Run command
CMD ["python", "server_py/main.py"]

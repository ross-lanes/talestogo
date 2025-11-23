# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Force rebuild - Railway deployment fix
# Rebuild to pick up VITE environment variables

# Install system dependencies including Node.js for building frontend
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build frontend
RUN cd frontend && npm install && npm run build && cd ..

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run database setup and start the server
# Use shell form to allow environment variable expansion
CMD sh -c "python -c 'from app.database import engine, Base; from app import models; Base.metadata.create_all(bind=engine)' && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"

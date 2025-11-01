# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for database if it doesn't exist
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///./data/tales.db

# Run database migrations on startup and then start the server
CMD python app/migrations/run_migrations.py --db-path ./data/tales.db --no-backup && \
    python -c "from app.database import engine, Base; from app import models; Base.metadata.create_all(bind=engine)" && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000

# =============================================================================
# Tales Multi-Stage Dockerfile (PPPL-Compliant)
# =============================================================================
# This Dockerfile uses multi-stage builds to create a smaller, more secure image.
#
# Stage 1: Build frontend with Node.js
# Stage 2: Install Python dependencies
# Stage 3: Final runtime image (no build tools)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Frontend Builder
# ---------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy frontend source
COPY frontend/ ./

# Build arguments for Vite
ARG VITE_API_URL
ARG VITE_MICROSOFT_CLIENT_ID
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_MICROSOFT_CLIENT_ID=${VITE_MICROSOFT_CLIENT_ID}

# Build the frontend
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Python Dependencies
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS python-deps

WORKDIR /app

# Install build dependencies for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 3: Final Runtime Image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from deps stage
COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY requirements.txt .

# Copy built frontend from builder stage
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Make entrypoint script executable
RUN chmod +x scripts/docker-entrypoint.sh

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the entrypoint script (JSON form for proper signal handling)
CMD ["scripts/docker-entrypoint.sh"]

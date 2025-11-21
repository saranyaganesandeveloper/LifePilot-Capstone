# ------------------------------
# Stage 1 — Builder
# ------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install build deps needed to compile some Python wheels (only in builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (cacheable)
COPY requirements.txt .

# Install Python packages into /usr/local (system location) to copy into final image
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt -t /usr/local

# ------------------------------
# Stage 2 — Runtime
# ------------------------------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PATH=/usr/local/bin:$PATH

# Create a non-root user for better security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed Python packages from builder into final image
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY . /app

# Default port for Cloud Run; can be overridden at runtime
ENV PORT=8080
EXPOSE 8080

# Run as non-root user
USER appuser

# Entrypoint: use shell form so $PORT expands. Streamlit listens on $PORT and 0.0.0.0.
CMD ["sh", "-c", "streamlit run src/ui/app.py --server.port=${PORT:-8080} --server.address=0.0.0.0"]

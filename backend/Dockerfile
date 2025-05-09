FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/media /app/staticfiles /app/data && \
    chown -R 1000:1000 /app/media /app/staticfiles /app/data && \
    chmod -R 755 /app/media /app/staticfiles /app/data

# Collect static files
RUN python manage.py collectstatic --noinput

# Make start script executable
COPY start.sh .
RUN chmod +x start.sh

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["./start.sh"] 
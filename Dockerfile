# Use the high-performance Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables for clean logs and no .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system-level dependencies for Postgres and AI libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Learnova project
COPY . .

# Ensure upload directories exist inside the container
RUN mkdir -p app/static/uploads/profile_images app/static/uploads/pdfs

# Expose the port
EXPOSE 5001

# Start with Gunicorn for production-grade threading
CMD ["gunicorn", "--workers", "4", "--threads", "2", "--bind", "0.0.0.0:5001", "run:app"]
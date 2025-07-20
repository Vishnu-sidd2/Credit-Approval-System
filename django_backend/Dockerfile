# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements.txt first, then install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files (excluding requirements.txt which is already copied)
# This will copy manage.py, the inner 'django_backend' folder, 'credit_system' folder, .env etc.
COPY . /app/

# Expose port
EXPOSE 8000

# CMD is handled by docker-compose.yml
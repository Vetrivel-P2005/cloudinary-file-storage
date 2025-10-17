# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (e.g., for Pillow, psycopg2, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY index.html .

# Expose Flask app port
EXPOSE 8080

# Set environment variable (optional)
ENV PORT=8080

# ✅ Use Gunicorn (production server)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]

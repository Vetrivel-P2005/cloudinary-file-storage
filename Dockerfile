# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for packages like Pillow)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY index.html .

# Optional: If you use templates or static folders
# COPY templates/ ./templates/
# COPY static/ ./static/

# Expose the port Flask is running on
EXPOSE 8080

# Environment variable for Flask port (if needed)
ENV PORT=8080

# Use gunicorn in production (better than Flask’s built-in server)
# You can also stick with `CMD ["python", "app.py"]` for simplicity
CMD ["python", "app.py"]

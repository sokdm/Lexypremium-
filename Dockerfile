FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create upload directory
RUN mkdir -p static/uploads

# Expose port
EXPOSE 10000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]

# Use the latest Python 3.11 image (matches other services)
FROM python:3.11

# Set environment variables for better performance and logging
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (including SQLite if needed)
RUN apt-get update && apt-get install -y \
    sqlite3 libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*  # Cleanup to reduce image size

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 8000

# Run FastAPI application with Uvicorn
CMD ["uvicorn", "backend_main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]


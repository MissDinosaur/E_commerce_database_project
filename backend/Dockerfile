FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*  # Cleanup

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application files
COPY . .

# Add `data_pipeline/` to Python path
ENV PYTHONPATH="/app:/app/data_pipeline"

# Expose the application port
EXPOSE 8000

# Run FastAPI with Uvicorn correctly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]


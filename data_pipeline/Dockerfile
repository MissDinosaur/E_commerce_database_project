# Use an official Python image as the base image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Install system dependencies (including SQLite if needed)
RUN apt-get update && apt-get install -y \
    sqlite3 libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*  # Cleanup to reduce image size

# Copy the requirements file (if any) and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Define the entry point (modify based on actual script names)
CMD ["python", "processing/main.py"]


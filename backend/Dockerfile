FROM python:3.10

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port for FastAPI
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend_main:app", "--host", "0.0.0.0", "--port", "8000"]

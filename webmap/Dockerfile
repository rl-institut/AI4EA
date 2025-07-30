# Use official Python image as a base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install dependencies
COPY webmap/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY webmap/ ./webmap/

# Run the FastAPI app with gunicorn
CMD ["gunicorn", "webmap.main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "4",  "--bind", "0.0.0.0:8000"]
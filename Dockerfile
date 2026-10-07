# Standard lightweight Python 3.11 image for Hugging Face Spaces
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy codebase and assets
COPY . .

# Expose default Hugging Face Spaces port
EXPOSE 7860

# Launch FastAPI with dynamic port fallback
CMD ["sh", "-c", "uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-7860}"]

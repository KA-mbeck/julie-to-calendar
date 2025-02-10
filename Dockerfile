FROM python:3.9.7-slim-buster

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.23.5 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for static files
RUN mkdir -p static

# Expose both the main app port and OAuth callback port
EXPOSE 5000 8080

ENV FLASK_APP=app.py
ENV FLASK_ENV=development

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]

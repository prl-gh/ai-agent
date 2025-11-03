FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY src/ ./

# Environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Make sure to set OPENAI_API_KEY at runtime or through docker-compose
ENV OPENAI_API_KEY=""

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
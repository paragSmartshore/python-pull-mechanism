# Use the official Python image
FROM python:3.12-slim

# Set working directory to the project root 
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code (main.py) to the container's /app directory
COPY main.py /app/main.py

# Expose  default port
EXPOSE 8000

# Command to run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


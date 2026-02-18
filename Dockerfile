
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for dlib and opencv
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Set environment variables to limit build parallelism and prevent OOM
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV MAX_JOBS=1

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (Run on 8090 to avoid conflicts)
EXPOSE 8090

# Define environment variables
ENV FLASK_APP=run_web_server.py
ENV PYTHONUNBUFFERED=1

# Run the production server on port 8090
CMD ["python", "run_web_server.py"]

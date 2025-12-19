# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/ ./src/
COPY config/ ./config/

# (Optional) Create data directories so they exist
RUN mkdir -p data/inputs data/outputs

# Define the entry point
ENTRYPOINT ["python", "-m", "src.main"]
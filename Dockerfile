# Use an official Python runtime as a parent image
FROM python:3.10-slim

LABEL description="campquest, campsite finder"
LABEL version="1.0"
LABEL maintainer="Ravindu Udugampola"
LABEL email="ravindu365@gmail.com"

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Ensure cli.py has execute permissions
RUN chmod +x /app/cli.py

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Set cli.py as the entrypoint
ENTRYPOINT ["python", "/app/cli.py"]

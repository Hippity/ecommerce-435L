# Specify the base image
FROM python:3.9-alpine

# Add shared to PYTHONPATH
ENV PYTHONPATH="/app:/app/shared"

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files and the shared module
COPY . /app
COPY ../shared /app/shared

# Expose the service's port
EXPOSE 3003

# Define the command to run the application
CMD ["python", "sales/app.py"]

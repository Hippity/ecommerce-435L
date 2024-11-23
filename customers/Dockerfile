# Start by pulling the Python image
FROM python:3.9-alpine

# Add shared to PYTHONPATH
ENV PYTHONPATH="/app:/app/shared"

# Set the working directory
WORKDIR /app

# Copy the requirements file into the image
COPY requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files
COPY . /app
COPY ../shared /app/shared

# Expose the service's port
EXPOSE 3000  

# Define the command to run the application
CMD ["python", "customers/app.py"]

# Specify the base image
FROM python:3.9-alpine

# Add shared to PYTHONPATH
ENV PYTHONPATH="/app:/app/shared"

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the image
COPY ../requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app files and the shared module
COPY . /app
COPY ../shared /app/shared

# Expose the service's port
EXPOSE 3001

#ENV DATABASE_URL=mysql+pymysql://user:pw@docker.for.mac.host.internal:3306/ecommerce
ENV DATABASE_URL=mysql+pymysql://root:987654321@host.docker.internal:3306/ecommerce
#ENV DATABASE_URL=mysql+pymysql://root:987654321@localhost:3306/ecommerce

#CMD ["pytest"]

# Define the command to run the application
CMD ["python", "inventory/app.py"]

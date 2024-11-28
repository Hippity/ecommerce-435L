# Microservices Setup Guide

This repository contains multiple microservices that together make up the e-commerce platform. Each service can be built and run independently using Docker. Follow the instructions below to build and run the services.

## Prerequisites

1. [Docker](https://www.docker.com/) must be installed on your machine.
2. Ensure a Docker network named `ecommerce-network` exists. If not, create it using the command:
   ```bash
   docker network create ecommerce-network
   ```

## Building and Running the Services

### Customers Service

1. Build the Docker image for the customers service:
   ```bash
   docker build -t customers_service -f customers/Dockerfile .
   ```
2. Run the customers service:
   ```bash
   docker run -d --network ecommerce-network --name customers-service -p 3000:3000 customers_service
   ```

### Inventory Service

1. Build the Docker image for the inventory service:
   ```bash
   docker build -t inventory_service -f inventory/Dockerfile .
   ```
2. Run the inventory service:
   ```bash
   docker run -d --network ecommerce-network --name inventory-service -p 3001:3001 inventory_service
   ```

### Reviews Service

1. Build the Docker image for the reviews service:
   ```bash
   docker build -t reviews_service -f reviews/Dockerfile .
   ```
2. Run the reviews service:
   ```bash
   docker run -d --network ecommerce-network --name reviews-service -p 3002:3002 reviews_service
   ```

### Sales Service

1. Build the Docker image for the sales service:
   ```bash
   docker build -t sales_service -f sales/Dockerfile .
   ```
2. Run the sales service:
   ```bash
   docker run -d --network ecommerce-network --name sales-service -p 3003:3003 sales_service
   ```

### Auth Service

1. Build the Docker image for the auth service:
   ```bash
   docker build -t auth_service -f auth/Dockerfile .
   ```
2. Run the auth service:
   ```bash
   docker run -d --network ecommerce-network --name auth-service -p 3004:3004 auth_service
   ```

## Notes

- All services are configured to communicate through the `ecommerce-network` Docker network.
- Ensure all the Dockerfiles are correctly placed in their respective directories before running the commands.
- Adjust port mappings if any of the specified ports (3000-3004) are already in use.

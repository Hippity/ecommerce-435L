# Microservices Setup Guide

This README explains how to set up and run the E-Commerce Project using Docker Compose. The project consists of multiple microservices, including `auth-service`, `customer-service`, `sales-service`, `review-service`, `inventory-service`, and a MySQL database.

## Prerequisites

1. Install Docker and Docker Compose on your machine.
2. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/Hippity/ecommerce-435L.git
   cd ecommerce-435L
   ```
3. Ensure `docker-compose.yml`, `requirements.txt`, and all service directories (`auth`, `customer`, `sales`, `review`, `inventory`) are present in the root directory.

## Setting Up the Project

### Step 1: Build and Start Services
1. Run the following command to build and start all services:
   ```bash
   docker-compose up --build
   ```

### Step 2: Verify Running Services
1. Check the running containers:
   ```bash
   docker-compose ps
   ```
   Example output:
   ```
   Name                          Command               State           Ports
   ecommerce-435l-db-1                  mysql:8.0                          "docker-entrypoint.s…"   db                  6 minutes ago    Up 9 seconds   33060/tcp, 0.0.0.0:3307->3306/tcp
   ecommerce-435l-auth-service-1        ecommerce-435l-auth-service        "python auth/app.py"     auth-service        11 seconds ago   Up 9 seconds   0.0.0.0:3004->3004/tcp
   ecommerce-435l-customer-service-1    ecommerce-435l-customer-service    "python customers/ap…"   customer-service    11 seconds ago   Up 9 seconds   0.0.0.0:3000->3000/tcp
   ecommerce-435l-inventory-service-1   ecommerce-435l-inventory-service   "python inventory/ap…"   inventory-service   11 seconds ago   Up 8 seconds   0.0.0.0:3001->3001/tcp
   ecommerce-435l-review-service-1      ecommerce-435l-review-service      "python reviews/app.…"   review-service      11 seconds ago   Up 9 seconds   0.0.0.0:3002->3002/tcp   
   ecommerce-435l-sales-service-1       ecommerce-435l-sales-service       "python sales/app.py"    sales-service       8 seconds ago   Up 6 seconds   0.0.0.0:3003->3003/tcp
   ```

### Step 3: Access the Services
Access each service through its exposed port:

- **Auth Service**: `http://localhost:3004`
- **Customer Service**: `http://localhost:3000`
- **Sales Service**: `http://localhost:3003`
- **Review Service**: `http://localhost:3002`
- **Inventory Service**: `http://localhost:3001`

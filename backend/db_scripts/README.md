# Database Initialization Scripts

This directory contains SQL scripts used to initialize the PostgreSQL database when the Docker `db` service starts.

## `00_schema.sql`

This file defines the schema for the hardware-related tables, including `hardware`, `categories`, `use_cases`, `hardware_category_map`, `hardware_use_case_map`, `software`, and `hardware_software_map`.

## Initialization Order

The PostgreSQL Docker image executes all scripts in `/docker-entrypoint-initdb.d` in **alphabetical order**. These files have been prefixed with numbers to ensure the following order:


## Rebuilding the Database

To rebuild the `product_db` database in the Docker container, follow these steps:

1.  **Ensure Docker is Running**: Make sure Docker Desktop or your Docker daemon is running.

2.  **Navigate to the `backend` directory**:
    ```bash
    cd backend
    ```

3.  **Bring down existing containers and volumes**: This step is crucial to ensure a clean slate. It will remove any previous database data and allow the initialization scripts to be executed from scratch.
    ```bash
    docker compose -f docker-compose.yml down -v
    ```
    (The `-v` flag removes named volumes associated with the services, ensuring database data is deleted).

4.  **Bring up the `db` service**: This will build the Docker image (if necessary) and start the PostgreSQL container. The `docker-entrypoint.sh` of the PostgreSQL image will detect the files in the mounted `/docker-entrypoint-initdb.d` directory and automatically execute them in order.
    ```bash
    docker compose -f docker-compose.yml up -d db
    ```

5.  **Verify Database Creation (Optional)**:
    You can check the container logs to see the startup process:
    ```bash
    docker logs backend-db-1
    ```
    To connect to the database and list tables, first find the container ID:
    ```bash
    docker ps
    ```
    Then, set up database connection through IntelliJ. 
    You should see a list of tables including `hardware`, `categories`, `use_cases`, `hardware_category_map`, and `hardware_use_case_map`.

# Run test_queries.sql
    docker exec -it backend-db-1 psql -U admin -d product_db -P pager=off -f /docker-entrypoint-initdb.d/05_test_queries.sql

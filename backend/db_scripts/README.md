# Database Initialization Scripts

This directory contains SQL scripts used to initialize the PostgreSQL database when the Docker `db` service starts.

## `hardware_schema.sql`

This file defines the schema for the hardware-related tables, including `hardware`, `categories`, `use_cases`, `hardware_category_map`, and `hardware_use_case_map`.

## Rebuilding the Database

To rebuild the `product_db` database in the Docker container using the schema defined in `hardware_schema.sql`, follow these steps:

1.  **Ensure Docker is Running**: Make sure Docker Desktop or your Docker daemon is running.

2.  **Navigate to the `backend` directory**:
    ```bash
    cd backend
    ```

3.  **Bring down existing containers and volumes**: This step is crucial to ensure a clean slate. It will remove any previous database data and allow the `hardware_schema.sql` script to be executed from scratch.
    ```bash
    docker compose -f docker-compose.yml down -v
    ```
    (The `-v` flag removes named volumes associated with the services, ensuring database data is deleted).

4.  **Bring up the `db` service**: This will build the Docker image (if necessary) and start the PostgreSQL container. The `docker-entrypoint.sh` of the PostgreSQL image will detect the `hardware_schema.sql` file in the mounted `/docker-entrypoint-initdb.d` directory and automatically execute it to create the database schema.
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
    ```
    You should see a list of tables including `hardware`, `categories`, `use_cases`, `hardware_category_map`, and `hardware_use_case_map`.


# Run test_queries.sql
    docker exec -it backend-db-1 psql -U admin -d product_db -P pager=off -f /docker-entrypoint-initdb.d/test_queries.sql    press p to see next result

# Install MinerU to extract information in PDFs
    1. activate virtual machine
    2. download all dependencies for mineru:    
        pip install -U "mineru[all]"

    3. run this to extract information:
    for file in "FOLDER_PATH_OF_DEVICES_PDFS"*.pdf; do
        echo "Processing: $file"
        mineru -p "$file" -o "./raw_extraction" -m auto
    done
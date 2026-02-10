Run init_db.py ONCE to set up the tables.

- setup docker container 
  1. Run: python generate_schema_sql.py > ../db_scripts/01_schema.sql
  2. docker-compose down -v
  3. docker-compose up -d db // create db in the docker container with the schema we have
  you can connect database with IntelliJ IDE and read all tables there.
  4. Use SQLAlchemy to interact with the database


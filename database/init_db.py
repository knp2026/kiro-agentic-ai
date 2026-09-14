
import psycopg2

# Connect to the database
conn = psycopg2.connect(
    dbname="your_database_name",
    user="your_user",
    password="your_password",
    host="your_host"
)

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute the SQL script to create tables and insert initial data
with open("database/schema.sql", "r") as schema_file:
    cur.execute(schema_file.read())

# Commit the changes
conn.commit()

# Close communication with the database
cur.close()
conn.close()
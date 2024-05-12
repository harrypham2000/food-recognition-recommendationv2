import csv
import psycopg2

def create_table_from_csv(csv_file, table_name, database, username, password, host, port):
    # Connect to PostgreSQL
    conn = psycopg2.connect(user=username, database=database, password=password, host=host, port=port)
    cur = conn.cursor()

    # Check database existence
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
    database_exists = cur.fetchone()
    
    # Create database if it doesn't exist
    if not database_exists:
        create_db_query = f"CREATE DATABASE {database}"
        cur.execute(create_db_query)
        conn.commit()

    # Connect to the created database
    conn.close()
    conn = psycopg2.connect(database=database, user=username, password=password, host=host, port=port)
    cur = conn.cursor()

    # Read CSV file
    with open(csv_file, 'r',encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Get the header row

        # Create table
        # create_table_query = f"CREATE TABLE {table_name} ({', '.join([f'{column} TEXT' for column in header])})"
        # Create table and bypass the first column 
        create_table_query = f"CREATE TABLE {table_name} ({', '.join([f'{column} TEXT' for column in header[1:]])})"
        cur.execute(create_table_query)

        # Insert data into table
        # for row in reader:
        #     insert_query = f"INSERT INTO {table_name} VALUES ({', '.join([f'%s' for _ in header[1:]])})"
        #     cur.execute(insert_query, row)
        
        # Fix to bypass the first columns
        for row in reader:
            insert_query = f"INSERT INTO {table_name} ({', '.join(header[1:])}) VALUES ({', '.join(['%s' for _ in header[1:]])})"
            cur.execute(insert_query, row[1:])


    # Commit changes and close connection
    conn.commit()
    cur.close()
    conn.close()
def view(table_name, database, username, password, host, port):
    conn = psycopg2.connect(database=database, user=username, password=password, host=host, port=port)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()
    
# Evaluate db creation and viewing
# csv_file = './db/recipes.csv'
# table_name='recipes'
# database='recipes'
# username='harry'
# password='1309800ok'
# host='localhost'
# port='5432'
# create_table_from_csv(csv_file, table_name, database, username, password, host, port)
# view(table_name, database, username, password, host, port)

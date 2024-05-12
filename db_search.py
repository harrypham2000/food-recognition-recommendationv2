import psycopg2
import psycopg2.extras
import psycopg2.extensions
import ast

# import nltk
# from nltk.tokenize import word_tokenize
# nltk.download('punkt')

def search(conn, table_name, column_name, search_term):
    # Connect to the database
    cur = conn.cursor()
    cur.execute("SELECT name FROM pg_available_extensions WHERE name = 'pg_trgm'")
    extensions=cur.fetchall()
    if not extensions:
        cur.execute("CREATE EXTENSION pg_trgm")
        conn.commit()
    # Try-except block:
    try:
        # Create full-text search index
        cur.execute(f"CREATE INDEX IF NOT EXISTS {column_name}_fts_idx ON {table_name} USING GIN (to_tsvector('english', {column_name}))")
        
        # Convert search term to a tsquery data type
        search_query = f"plainto_tsquery('english',%s)" # Convert search term to tsquery data type
        # Execute the SQL query to search full-text
        cur.execute(f"SELECT * FROM {table_name} WHERE to_tsvector('english',{column_name}) @@ {search_query} LIMIT 2", (search_term,))
        # Execute the SQL query to search simple text
        # cur.execute(f"SELECT * FROM {table_name} WHERE {column_name} LIKE %s LIMIT 2" , (f"%{search_term}%",))
        
        rows = cur.fetchall()
        # results=[]
        sentences=[]
        for row in rows:
            col1,col2,col3,col4,col5,col6=row
            dish_name=col1
            ingredients = col2
            instructions = col3
            link = col4 
            # def format_ingredient(ingredient):
            #     if " " in ingredient:
            #         return "\"" + ingredient + "\""
            #     else:
            #         return ingredient
            
            ingredients = ast.literal_eval(col2)  # Convert string to list
            instructions = ast.literal_eval(col3)  # Convert string to list
            sentence1 = f"Tên món ăn: " + dish_name + "."
            sentence2 = f"Nguyên liệu: " + ", ".join(ingredients) + "."
            sentence3 = f"Cách nấu: " + ", ".join(instructions) + "."
            sentence4 = f"Đường link tới công thức: " + link + "."

            sentences.extend([sentence1, sentence2, sentence3, sentence4])
            # sentence = "The ingredients are: " + ", ".join(ingredients) + "."
            # sentence = "The ingredients are: " + ", ".join([word_tokenize(i) for i in ingredients]) + "."
            # sentence = "The ingredients are: " + ", ".join(map(str, [format_ingredient(i) for i in ingredients])) + "."
            # sentence = "The ingredients are: " + ", ".join(map(str, [i.replace("'", "\\'") for i in ingredients[:-1]])) + ", and " + ingredients[-1] + "."
            
        conn.commit() # Commit the transaction
    except Exception as e:
        conn.rollback() # Rollback the transaction in case error occurs
        raise e # Raise the exception
    
    finally:
        cur.close() # Close the cursor
    return sentences
    
# Test search 
# table_name = 'recipes'
# column_name = 'title'
# search_term = 'pizza'
# database = 'recipes'
# username = 'harry'
# password = '1309800ok'
# host = 'localhost'
# port = '5432'

# search(table_name, column_name, search_term, database, username, password, host, port)

from sqlalchemy import create_engine, MetaData, Table

# Create the engine to connect to keto.db
engine = create_engine('sqlite:///keto.db')

# Initialize metadata object
metadata = MetaData()

# Reflect the recipes table from the database
recipes_table = Table('recipe', metadata, autoload_with=engine)

# Drop the recipes table
recipes_table.drop(engine)

print("Dropped the 'recipes' table.")

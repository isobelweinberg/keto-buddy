from sqlalchemy import create_engine, MetaData, Table

# Create the engine to connect to keto.db
engine = create_engine('sqlite:///keto.db')

# Initialize metadata object
metadata = MetaData()

# Reflect the recipes table from the database
chosen_table = Table('ketone_log_entry', metadata, autoload_with=engine)

# Drop the recipes table
chosen_table.drop(engine)

print(f"Dropped the {chosen_table.name} table.")

import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from dotenv import load_dotenv

# ----------------------------
# LOAD ENVIRONMENT VARIABLES
# ----------------------------
# Load credentials from .env file at the project root
load_dotenv()

# ----------------------------
# CONFIGURATION
# ----------------------------
# Environment variable DB_ENGINE will determine which database to use.
# Set DB_ENGINE=postgres for local testing or DB_ENGINE=mysql for AWS RDS.
DB_ENGINE = os.environ.get("DB_ENGINE", "mysql").lower()  # default to mysql if not specified

DB_HOST = os.environ.get("DB_HOST", "your-rds-endpoint.amazonaws.com")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "insurance_db")
DB_USER = os.environ.get("DB_USER", "your_username")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "your_password")

CSV_FILE = "insurance_data.csv"  # local CSV file; if using S3, adjust accordingly

# ----------------------------
# DATA PREPARATION FUNCTION
# ----------------------------
def preprocess_data(csv_file):
    # Read the CSV data
    df = pd.read_csv(csv_file)
    print("Initial data shape:", df.shape)

    # Handle missing values (if any)
    df = df.ffill()  # Updated from fillna(method='ffill')
    
    # Example feature engineering:
    # One-hot encode the categorical 'policy_type'
    encoder = OneHotEncoder(sparse_output=False)  # Updated parameter name
    policy_encoded = encoder.fit_transform(df[['policy_type']])
    policy_df = pd.DataFrame(policy_encoded, 
                             columns=[f"policy_{cat}" for cat in encoder.categories_[0]])
    df = pd.concat([df.drop("policy_type", axis=1), policy_df], axis=1)

    # Normalize continuous features: age, annual_premium, claims_count
    scaler = StandardScaler()
    df[['age', 'annual_premium', 'claims_count']] = scaler.fit_transform(df[['age', 'annual_premium', 'claims_count']])
    
    print("Processed data shape:", df.shape)
    return df


# ----------------------------
# STORE DATA INTO DATABASE
# ----------------------------
def store_data_to_db(df):
    # Create a connection string based on the DB_ENGINE setting
    if DB_ENGINE in ("postgres", "psql"):
        # Using PostgreSQL; ensure you have installed psycopg2-binary: pip install psycopg2-binary
        connection_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Default to MySQL (AWS RDS); ensure you have installed pymysql: pip install pymysql
        connection_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    engine = create_engine(connection_str)
    
    # Write processed data to the database; table name: processed_insurance_data
    df.to_sql(name='processed_insurance_data', con=engine, if_exists='replace', index=False)
    print("Data stored to the database successfully.")

# ----------------------------
# MAIN EXECUTION
# ----------------------------
if __name__ == "__main__":
    processed_df = preprocess_data(CSV_FILE)
    store_data_to_db(processed_df)

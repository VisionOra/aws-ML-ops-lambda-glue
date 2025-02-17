import os
import pandas as pd
import numpy as np
import boto3
from sqlalchemy import create_engine
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import argparse
from io import StringIO

# ----------------------------
# CONFIGURATION (Set these in AWS Glue Job Parameters)
# ----------------------------
DB_ENGINE = os.environ.get("DB_ENGINE", "postgres").lower()  # Default to postgres
DB_HOST = os.environ.get("DB_HOST", "artilence.c1cciu62iczf.us-east-1.rds.amazonaws.com")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "testtask_abbas")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

S3_BUCKET = os.environ.get("S3_BUCKET", "abbas-mlops-model")  # S3 bucket name
S3_KEY = os.environ.get("S3_KEY", "insurance_data.csv")  # S3 key for the CSV file

# ----------------------------
# DATA PREPARATION FUNCTION
# ----------------------------
def preprocess_data():
    print("Reading CSV data from S3...")

    s3_client = boto3.client('s3')
    obj = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    csv_content = obj['Body'].read().decode('utf-8')
    df = pd.read_csv(StringIO(csv_content))

    print("Initial data shape:", df.shape)

    # Handle missing values
    df = df.ffill()

    # One-hot encode categorical feature 'policy_type'
    encoder = OneHotEncoder(sparse_output=False)
    policy_encoded = encoder.fit_transform(df[['policy_type']])
    policy_df = pd.DataFrame(policy_encoded, columns=[f"policy_{cat}" for cat in encoder.categories_[0]])
    df = pd.concat([df.drop("policy_type", axis=1), policy_df], axis=1)

    # Normalize continuous features
    scaler = StandardScaler()
    df[['age', 'annual_premium', 'claims_count']] = scaler.fit_transform(df[['age', 'annual_premium', 'claims_count']])

    print("Processed data shape:", df.shape)
    return df

# ----------------------------
# STORE DATA INTO DATABASE
# ----------------------------
def store_data_to_db(df):
    if DB_ENGINE == "postgres":
        connection_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        connection_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    engine = create_engine(connection_str)
    
    df.to_sql(name='processed_insurance_data', con=engine, if_exists='replace', index=False)
    print("Data stored to the database successfully.")

# ----------------------------
# SCRIPT EXECUTION
# ----------------------------
if __name__ == "__main__":
    processed_df = preprocess_data()
    store_data_to_db(processed_df)

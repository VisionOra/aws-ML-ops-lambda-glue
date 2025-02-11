import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score
import os
from dotenv import load_dotenv
load_dotenv()

# ----------------------------
# CONFIGURATION
# ----------------------------
DB_ENGINE = os.environ.get("DB_ENGINE", "mysql").lower()  # default to mysql if not specified

DB_HOST = os.environ.get("DB_HOST", "your-rds-endpoint.amazonaws.com")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "insurance_db")
DB_USER = os.environ.get("DB_USER", "your_username")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "your_password")


# Model output file
MODEL_FILE = "models/model.pkl"

# ----------------------------
# LOAD DATA FUNCTION
# ----------------------------
def load_processed_data():
    if DB_ENGINE in ("postgres", "psql"):
        # Using PostgreSQL; ensure you have installed psycopg2-binary: pip install psycopg2-binary
        connection_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Default to MySQL (AWS RDS); ensure you have installed pymysql: pip install pymysql
        connection_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_str)
    df = pd.read_sql_table("processed_insurance_data", engine)
    
    print("Data loaded. Shape:", df.shape)
    return df

# ----------------------------
# MODEL TRAINING FUNCTION
# ----------------------------
def train_model(df):
    # Assume the target is "churn" and the first column "customer_id" is an ID.
    X = df.drop(columns=["customer_id", "churn"])
    y = df["churn"]
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train a Random Forest classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = clf.predict(X_test)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1-Score: {f1:.4f}")
    return clf

# ----------------------------
# SAVE MODEL
# ----------------------------
def save_model(model, model_file):
    joblib.dump(model, model_file)
    print(f"Model saved to {model_file}")

# ----------------------------
# MAIN EXECUTION
# ----------------------------
if __name__ == "__main__":
    # If not using RDS, you can optionally save the processed data locally first.
    df = load_processed_data()
    model = train_model(df)
    save_model(model, MODEL_FILE)
    
    # OPTIONAL: Upload the model to S3 (if deploying from S3)
    # import boto3
    # s3 = boto3.client('s3')
    # BUCKET_NAME = "your-s3-bucket-name"
    # s3.upload_file(MODEL_FILE, BUCKET_NAME, MODEL_FILE)

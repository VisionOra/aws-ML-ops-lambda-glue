import os
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score
import boto3

# ----------------------------
# CONFIGURATION (Set these in AWS Glue Job Parameters)
# ----------------------------
DB_ENGINE = os.environ.get("DB_ENGINE", "postgres").lower()

DB_HOST = os.environ.get("DB_HOST", "artilence.c1cciu62iczf.us-east-1.rds.amazonaws.com")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "testtask_abbas")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

S3_BUCKET = os.environ.get("S3_BUCKET", "abbas-mlops-model")
MODEL_FILE = "/tmp/model.pkl"

# ----------------------------
# LOAD DATA FUNCTION
# ----------------------------
def load_processed_data():
    if DB_ENGINE == "postgres":
        connection_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        connection_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    engine = create_engine(connection_str)
    df = pd.read_sql_table("processed_insurance_data", engine)
    print("Data loaded. Shape:", df.shape)
    return df

# ----------------------------
# MODEL TRAINING FUNCTION
# ----------------------------
def train_model(df):
    X = df.drop(columns=["customer_id", "churn"])
    y = df["churn"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1-Score: {f1:.4f}")
    
    return clf

# ----------------------------
# SAVE MODEL TO S3
# ----------------------------
def save_model(model):
    joblib.dump(model, MODEL_FILE)
    s3 = boto3.client('s3')
    s3.upload_file(MODEL_FILE, S3_BUCKET, "model.pkl")
    print(f"Model uploaded to S3: {S3_BUCKET}/model.pkl")

# ----------------------------
# MAIN EXECUTION
# ----------------------------
if __name__ == "__main__":
    df = load_processed_data()
    model = train_model(df)
    save_model(model)

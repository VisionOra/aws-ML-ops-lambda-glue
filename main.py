import joblib
import numpy as np
import os
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Global model variable to be loaded once per application lifecycle.
MODEL = None
MODEL_FILE = "model.pkl"  # Local path to save the model file
S3_BUCKET = "abbas-mlops-model"
S3_KEY = "abbas-mlops-model/model.pkl"

def download_model_from_s3():
    s3 = boto3.client('s3')
    s3.download_file(S3_BUCKET, S3_KEY, MODEL_FILE)

def load_model():
    """
    Loads the model from the local file if not already loaded.
    Downloads from S3 if the local file is not available.
    """
    global MODEL
    if MODEL is None:
        if not os.path.exists(MODEL_FILE):
            download_model_from_s3()
        MODEL = joblib.load(MODEL_FILE)
    return MODEL

# Define request schema using Pydantic
class Features(BaseModel):
    age: float
    annual_premium: float
    claims_count: float
    policy_auto: float
    policy_home: float
    policy_life: float

class PredictionRequest(BaseModel):
    features: Features

@app.get("/")
def read_root():
    return {"message": "Hello, world!"}

@app.on_event("startup")
def startup_event():
    print("Working directory:", os.getcwd())
    print("Does model file exist?", os.path.exists(MODEL_FILE))
    try:
        load_model()
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")

@app.post("/predict")
def predict(request: PredictionRequest):
    """
    Expects a JSON payload with the following structure:
    {
        "features": {
            "age": <value>,
            "annual_premium": <value>,
            "claims_count": <value>,
            "policy_auto": <value>,   # one-hot encoded for auto
            "policy_home": <value>,   # one-hot encoded for home
            "policy_life": <value>    # one-hot encoded for life
        }
    }
    
    Returns a JSON response with the predicted class and, if available, the prediction probabilities.
    """
    try:
        # Extract the features from the request
        features = request.features

        # Create a numpy array in the order used during training.
        # Ensure that the order here matches the order used during training.
        input_data = np.array([
            features.age,
            features.annual_premium,
            features.claims_count,
            features.policy_auto,
            features.policy_home,
            features.policy_life
        ]).reshape(1, -1)

        # Load the model (will be loaded only once per application lifecycle)
        model = load_model()
        prediction = model.predict(input_data)
        probability = None
        if hasattr(model, "predict_proba"):
            probability = model.predict_proba(input_data).tolist()

        return {"prediction": int(prediction[0]), "probability": probability}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
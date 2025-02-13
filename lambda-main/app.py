from chalice import Chalice
import numpy as np
import os
import boto3
from pydantic import BaseModel
from typing import Dict
import joblib  # Assuming you're using joblib to load your model

app = Chalice(app_name="insurance-predictor")

# Global model variable to be loaded once per application lifecycle.
MODEL = None
S3_BUCKET = "abbas-mlops-model"
S3_KEY = "model.pkl"
MODEL_PATH = "/tmp/model.pkl"  # Use /tmp directory for model file in Lambda

def download_model_from_s3():
    s3 = boto3.client('s3')
    s3.download_file(S3_BUCKET, S3_KEY, MODEL_PATH)  # Download to /tmp directory

def load_model():
    global MODEL
    if MODEL is None:
        download_model_from_s3()  # Ensure the model is downloaded to /tmp
        MODEL = joblib.load(MODEL_PATH)  # Load model from /tmp
    return MODEL

# Pydantic-like class for features (you can also define this schema manually)
class Features(BaseModel):
    age: float
    annual_premium: float
    claims_count: float
    policy_auto: float
    policy_home: float
    policy_life: float

@app.route("/predict", methods=["POST"])
def predict():
    request = app.current_request
    body = request.json_body
    features = Features(**body["features"])

    input_data = np.array([
        features.age,
        features.annual_premium,
        features.claims_count,
        features.policy_auto,
        features.policy_home,
        features.policy_life
    ]).reshape(1, -1)

    try:
        # Load the model (will be loaded only once per application lifecycle)
        model = load_model()
        prediction = model.predict(input_data)
        probability = None
        if hasattr(model, "predict_proba"):
            probability = model.predict_proba(input_data).tolist()

        return {"prediction": int(prediction[0]), "probability": probability}
    except Exception as e:
        return {"error": str(e)}, 400

@app.route("/")
def index():
    return {"message": "Hello from Chalice"}

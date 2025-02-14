import joblib
import numpy as np
import os
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import threading
import pickle
# Load environment variables from .env file
load_dotenv()

# Configure logging first
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
MODEL_LOCK = threading.Lock()
MODEL_PATH = "/tmp/model.pkl"  # Use /tmp in Lambda!

# Global model variable
MODEL = None

S3_BUCKET = os.getenv("BUCKET")
S3_KEY = os.getenv("KEY")
MODEL_FILE = ("model.pkl")

def download_model_from_s3():
    """Download the model from S3 with better error handling"""
    try:
        # Check if environment variables are set
        if not S3_BUCKET:
            logger.error("BUCKET environment variable is not set")
            raise ValueError("BUCKET environment variable must be set")
        
        if not S3_KEY:
            logger.error("KEY environment variable is not set")
            raise ValueError("KEY environment variable must be set")
            
        logger.info(f"Downloading model from S3 bucket: {S3_BUCKET}, key: {S3_KEY}")
        s3 = boto3.client('s3')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        
        s3.download_file(S3_BUCKET, S3_KEY, MODEL_PATH)
        logger.info(f"Model downloaded successfully to {MODEL_PATH}")
    except ValueError as ve:
        # Re-raise validation errors
        raise ve
    except Exception as e:
        logger.error(f"Error downloading model from S3: {str(e)}")
        raise RuntimeError(f"Failed to download model from S3: {str(e)}")


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
async def root():
    return {"message": "Hello World"}

@app.on_event("startup")
async def startup_event():
    """Initialize the model when the app starts"""
    try:
        logger.info("Starting up FastAPI application")
        load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise RuntimeError(f"Failed to initialize the application: {str(e)}")

@app.post("/load-model")
def load_model():
    """Load the model with proper environment variable checking"""
    global MODEL
    
    try:
        # Check if environment variables exist
        S3_BUCKET = os.environ.get("BUCKET")
        S3_KEY = os.environ.get("KEY")
        
        if not S3_BUCKET:
            logger.error("BUCKET environment variable is not set")
            raise ValueError("BUCKET environment variable must be set")
        
        if not S3_KEY:
            logger.error("KEY environment variable is not set")
            raise ValueError("KEY environment variable must be set")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        
        # Download from S3
        logger.info(f"Downloading model from S3 bucket: {S3_BUCKET}, key: {S3_KEY}")
        s3 = boto3.client('s3')
        s3.download_file(S3_BUCKET, S3_KEY, MODEL_PATH)
        
        # Load the model
        logger.info(f"Loading model from {MODEL_PATH}")
        MODEL = joblib.load(MODEL_PATH)
        logger.info("Model loaded successfully!")
        return MODEL
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

@app.post("/predict")
def predict(request: PredictionRequest):
    """
    Make predictions using the loaded model
    """
    try:
        if MODEL is None:
            load_model()

        features = request.features
        input_data = np.array([
            features.age,
            features.annual_premium,
            features.claims_count,
            features.policy_auto,
            features.policy_home,
            features.policy_life
        ]).reshape(1, -1)

        prediction = MODEL.predict(input_data)
        probability = None
        if hasattr(MODEL, "predict_proba"):
            probability = MODEL.predict_proba(input_data).tolist()

        return {
            "prediction": int(prediction[0]),
            "probability": probability
        }
    except StopIteration as e:
        
        raise HTTPException(status_code=400, detail=str(e))

import json


from mangum import Mangum
lambda_handler = Mangum(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)






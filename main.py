import joblib
import numpy as np
import os
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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

# Global model variable
MODEL = None
MODEL_FILE = "model.pkl"
S3_BUCKET = os.getenv("S3_BUCKET")
S3_KEY = os.getenv("S3_KEY")

def download_model_from_s3():
    """Download the model from S3 with better error handling"""
    try:
        logger.info(f"Downloading model from S3 bucket: {S3_BUCKET}, key: {S3_KEY}")
        s3 = boto3.client('s3')
        s3.download_file(S3_BUCKET, S3_KEY, MODEL_FILE)
        logger.info("Model downloaded successfully")
    except Exception as e:
        logger.error(f"Error downloading model from S3: {str(e)}")
        raise RuntimeError(f"Failed to download model from S3: {str(e)}")

def load_model():
    """Load the model into the global variable"""
    global MODEL
    try:
        if not os.path.exists(MODEL_FILE):
            download_model_from_s3()
        MODEL = joblib.load(MODEL_FILE)
        return MODEL
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

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
async def load_model_endpoint():
    """
    Endpoint to manually trigger model download from S3 and load it into RAM
    """
    try:
        logger.info("Manual model reload triggered")
        
        # Remove existing model file to force fresh download
        if os.path.exists(MODEL_FILE):
            os.remove(MODEL_FILE)
            logger.info("Removed existing model file")
        
        # Load model (this will trigger download and load)
        load_model()
        
        return {
            "status": "success",
            "message": "Model successfully downloaded and loaded",
            "details": {
                "model_file": MODEL_FILE,
                "s3_bucket": S3_BUCKET,
                "s3_key": S3_KEY
            }
        }
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
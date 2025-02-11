import json
import joblib
import numpy as np
import os

# Global model variable to be loaded once per container lifecycle (cold start)
MODEL = None
MODEL_FILE = "model.pkl"  # Ensure this file is packaged with your Lambda deployment

def load_model():
    global MODEL
    if MODEL is None:
        # Option 1: Load from local file packaged in the deployment zip
        MODEL = joblib.load(MODEL_FILE)
        
        # Option 2: Alternatively, load from S3 (uncomment and set your parameters)
        # import boto3, tempfile
        # s3 = boto3.client('s3')
        # BUCKET_NAME = os.environ.get("MODEL_S3_BUCKET", "your-s3-bucket")
        # with tempfile.NamedTemporaryFile() as tmp:
        #     s3.download_fileobj(BUCKET_NAME, MODEL_FILE, tmp)
        #     tmp.seek(0)
        #     MODEL = joblib.load(tmp)
    return MODEL

def lambda_handler(event, context):
    """
    Expected input (JSON):
    {
        "features": {
            "age": value,
            "annual_premium": value,
            "claims_count": value,
            "policy_auto": value,   # one-hot encoded for auto
            "policy_home": value,   # one-hot encoded for home
            "policy_life": value    # one-hot encoded for life
        }
    }
    """
    try:
        body = event.get("body")
        if body is None:
            raise ValueError("Missing body in event")
            
        # If API Gateway is configured to pass a JSON string in body, parse it
        if isinstance(body, str):
            body = json.loads(body)
            
        features = body.get("features")
        if features is None:
            raise ValueError("Missing 'features' in request body")
        
        # Convert features to a numpy array with the expected order.
        # Ensure that the order here matches the order used during training.
        feature_order = ["age", "annual_premium", "claims_count", "policy_auto", "policy_home", "policy_life"]
        input_data = np.array([features.get(feat, 0) for feat in feature_order]).reshape(1, -1)
        
        model = load_model()
        prediction = model.predict(input_data)
        probability = model.predict_proba(input_data).tolist() if hasattr(model, "predict_proba") else None
        
        response = {
            "prediction": int(prediction[0]),
            "probability": probability
        }
        
        return {
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }

## Setup Instructions

### 1. AWS RDS (MySQL)
- Launch an RDS MySQL instance.
- Create a database (e.g., `insurance_db`) and configure the security group to allow access.
- Copy `.env.example` to `.env` and update with your credentials:
```sh
cp .env.example .env
```

### 2. Docker Setup (Alternative)

Build the Docker image:
```sh
docker build -t insurance-app .
```

Run the container:
```sh
docker run -p 8000:8000 --env-file .env insurance-app
```
### 3. Deploy on AWS Lmabda

- Build Image:

```sh
docker buildx build --platform linux/amd64 --no-cache -t insurance-app . -f Dockerfile.aws
```

- Tag Image:

```sh
docker tag insurance-app:latest 273354662169.dkr.ecr.us-east-1.amazonaws.com/insurance-app:latest 
```
- Push Image on ec2:

```sh
docker push 273354662169.dkr.ecr.us-east-1.amazonaws.com/insurance-app:latest
```
- Deploy/update code Lambda function:

```sh
aws lambda update-function-code \    --function-name insurance-app \
    --image-uri 273354662169.dkr.ecr.us-east-1.amazonaws.com/insurance-app:latest \
    --region us-east-1
  ```

- Set enviroment variables

```sh
aws lambda update-function-configuration \    --function-name insurance-app \
    --environment "Variables={BUCKET=abbas-mlops-model,KEY=model.pkl}"
  ```

### 4. Use data_preperation.py script as a glue job and set job parameters in job details as 

--additional-python-modules as key
pandas,numpy,SQLAlchemy,scikit-learn,psycopg2-binary as value

### 5. Use model_training.py script as a glue job and set job parameters in job details as 

--additional-python-modules as key
pandas,numpy,SQLAlchemy,scikit-learn,psycopg2-binary as value

### 6. Make lambda function for trigger_data_prep

integerate it with S3, whenever new file **insurance_data.csv** uploaded, the trigger runs the data_preperation job on glue.

### 7. M### 6. Make lambda function for trigger_model_training

Make EventBridge that enabled for Succeeded data-preperation job, in code make a trigger for model_training job.(Allow permissions for Lambda functions and in Lambda function allow permissions for event put and target).

### 8. Flow

- Make S3 bucket and set enviroment variables for lambda function(BUCKET, KEY)
- Make DockerImage, tag and push on ec2
- update or make lambda function
- Make jobs for data_prepration and model_training on AWS Glue(Replace the S3 bucket and key and RDS credentials)
- Upload the new insurance_data.csv on AWS S3
- Test and Run the process. 
- Here is the Detail video link(https://www.loom.com/share/23b58a56a046493fa38daa75171ac83b?sid=69e7ac6e-5d51-4d39-b3d4-b2d2b3dabd15)

### 9. Testing Link(You can test the Lambda Function on postman):

https://jux5ea6bfhuslk6zqvft34ocmi0peiah.lambda-url.us-east-1.on.aws/predict

- Body:
{
  "features": {
    "age": 50,
    "annual_premium": 2000,
    "claims_count": 1,
    "policy_auto": 1,
    "policy_home": 0,
    "policy_life": 0
  }
}


## Setup Instructions

### 1. AWS RDS (MySQL)
- Launch an RDS MySQL instance.
- Create a database (e.g., `insurance_db`) and configure the security group to allow access.
- Copy `.env.example` to `.env` and update with your credentials:
```sh
cp .env.example .env
```

### 2. Data Preparation
- Place the raw CSV file (`insurance_data.csv`) in the project folder.
- Run the data preparation script:

## Python 3.9

```sh
  python training/data_preparation.py
  ```

- Run model_training.py script:
```sh
  python training/model_training.py
  ```

### 3. Deploy through Zappa

```sh
zappa deploy dev
```

- After updation in code:
```sh
zappa update dev
```

### 4. Docker Setup (Alternative)

Build the Docker image:
```sh
docker build -t insurance-app .
```

Run the container:
```sh
docker run -p 8000:8000 --env-file .env insurance-app
```
### 5. Deploy on AWS Lmabda

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

### 6. Use data_preperation.py script as a glue job and set job parameters in job details as 

--additional-python-modules as key
pandas,numpy,SQLAlchemy,scikit-learn,psycopg2-binary as value

### 7. Flow

- Make S3 bucket and set enviroment variables for lambda function(BUCKET, KEY)
- Make DockerImage, tag and push on ec2
- update or make lambda function
- Make jobs for data_prepration and model_training on AWS Glue(Replace the S3 bucket and key and RDS credentials)
- Test and Run the process. 
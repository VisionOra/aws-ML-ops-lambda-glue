#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set variables
AWS_REGION="${AWS_DEFAULT_REGION}"  # Get from .env
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)  # Get account ID automatically
ECR_REPO_NAME="insurance-app"
LAMBDA_FUNCTION_NAME="insurance-app"
IMAGE_TAG="latest"
role="arn:aws:iam::${AWS_ACCOUNT_ID}:role/moiz"

# Construct the ECR repository URI
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}"

# Authenticate Docker with AWS ECR
echo "Authenticating Docker with AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Check if ECR repository exists, if not create it
echo "Checking if ECR repository exists..."
aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ECR repository does not exist. Creating..."
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION
else
    echo "ECR repository already exists."
fi

# Build the Docker image
echo "Building Docker image..."
docker build --platform linux/arm64 -t $ECR_REPO_NAME . -f Dockerfile.aws

# Tag the Docker image
echo "Tagging Docker image..."
docker tag $ECR_REPO_NAME:latest $ECR_REPO_URI

# Push the image to AWS ECR
echo "Pushing Docker image to ECR..."
docker push $ECR_REPO_URI

# Check if Lambda function exists
echo "Checking if Lambda function exists..."
aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $AWS_REGION > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Creating a new AWS Lambda function..."
    aws lambda create-function \
        --function-name $LAMBDA_FUNCTION_NAME \
        --package-type Image \
        --code ImageUri=$ECR_REPO_URI \
        --role $role \
        --region $AWS_REGION
else
    echo "Updating existing AWS Lambda function..."
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --image-uri $ECR_REPO_URI \
        --region $AWS_REGION
fi

# After function creation/update, check the architecture
echo "Checking Lambda function architecture..."
aws lambda get-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --region $AWS_REGION \
    --query 'Architectures'

# Also check if the entrypoint is correctly set
aws lambda get-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --region $AWS_REGION \
    --query 'ImageConfigResponse.ImageConfig'

# Test the Lambda function
echo "Waiting for Lambda function to be ready..."
while true; do
    STATUS=$(aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --query 'Configuration.State' --output text --region $AWS_REGION)
    if [ "$STATUS" = "Active" ]; then
        break
    fi
    echo "Function status: $STATUS. Waiting..."
    sleep 5
done

echo "Invoking Lambda function..."
aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME response.json --region $AWS_REGION

# Display the response
echo "Lambda function response:"
cat response.json
echo ""

# Update Lambda function configuration
aws lambda update-function-configuration \
    --function-name $LAMBDA_FUNCTION_NAME \
    --timeout 30 \
    --memory-size 512 \
    --architectures arm64 \
    --region $AWS_REGION

# Wait for the update to complete
echo "Waiting for function update to complete..."
aws lambda wait function-updated \
    --function-name $LAMBDA_FUNCTION_NAME

echo "Deployment complete! 🚀"
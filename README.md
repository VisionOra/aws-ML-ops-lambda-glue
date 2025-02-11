
## Setup Instructions

### 1. AWS RDS (MySQL)
- Launch an RDS MySQL instance.
- Create a database (e.g., `insurance_db`) and configure the security group to allow access.
- Update the environment variables in `data_preparation.py` and `model_training.py` with your RDS details.

### 2. Data Preparation
- Place the raw CSV file (`insurance_data.csv`) in the project folder or in an S3 bucket.
- Run the data preparation script:
  ```bash
  python data_preparation.py

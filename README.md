
## Setup Instructions

### 1. AWS RDS (MySQL)
- Launch an RDS MySQL instance.
- Create a database (e.g., `insurance_db`) and configure the security group to allow access.
- Update the .env file for Database connection

### 2. Data Preparation
- Place the raw CSV file (`insurance_data.csv`) in the project folder.
- Run the data preparation script:

```sh
  python Training/data_preparation.py
  ```

- Run model_training.py script:
```sh
  python Training/model_training.py
  ```
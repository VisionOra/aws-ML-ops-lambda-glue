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

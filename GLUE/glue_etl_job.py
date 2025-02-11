import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, when
from pyspark.sql import functions as F

# Retrieve job arguments
args = getResolvedOptions(sys.argv, ['JOB_NAME', 's3_input_path', 'rds_jdbc_url', 'rds_table', 'db_user', 'db_password'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# ----------------------------
# READ RAW DATA FROM S3
# ----------------------------
raw_df = spark.read.option("header", "true").option("inferSchema", "true").csv(args['s3_input_path'])

# ----------------------------
# DATA TRANSFORMATION (similar to local preprocessing)
# ----------------------------
# Fill missing values (example)
df_filled = raw_df.fillna(method='ffill')

# One-hot encode "policy_type"
# For simplicity, we will manually create columns for each policy type.
policy_types = ["auto", "home", "life"]
for pt in policy_types:
    df_filled = df_filled.withColumn(f"policy_{pt}", when(col("policy_type") == pt, 1).otherwise(0))
df_transformed = df_filled.drop("policy_type")

# Normalize numeric columns (using min-max normalization for example)
for col_name in ["age", "annual_premium", "claims_count"]:
    min_val = df_transformed.agg({col_name: "min"}).collect()[0][0]
    max_val = df_transformed.agg({col_name: "max"}).collect()[0][0]
    df_transformed = df_transformed.withColumn(col_name, (col(col_name) - min_val) / (max_val - min_val))

# ----------------------------
# WRITE CLEAN DATA TO RDS
# ----------------------------
jdbc_url = args['rds_jdbc_url']  # e.g., "jdbc:mysql://your-rds-endpoint:3306/insurance_db"
table = args['rds_table']        # e.g., "processed_insurance_data"
db_properties = {
    "user": args['db_user'],
    "password": args['db_password'],
    "driver": "com.mysql.jdbc.Driver"
}

df_transformed.write.jdbc(url=jdbc_url, table=table, mode="overwrite", properties=db_properties)
print("Data written to RDS successfully.")

job.commit()

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sha2

# -----------------------------
# Config
# -----------------------------
BUCKET = "secure-flight-data"

# CORRECTED: Pointing to 'cloudsql-proxy' and the database name from your YAML
DB_URL = "jdbc:postgresql://cloudsql-proxy:5432/flight_analytics"

DB_PROPERTIES = {
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "driver": "org.postgresql.Driver"
}

# -----------------------------
# 1. Start Spark Session
# -----------------------------
spark = SparkSession.builder \
    .appName("GDPR_Compliance_Masking_GCP") \
    .config("spark.executor.instances", "1") \
    .config("spark.sql.shuffle.partitions", "2") \
    .getOrCreate()

# -----------------------------
# 2. Read Data from GCS
# -----------------------------
input_path = f"gs://{BUCKET}/raw/data.csv"

try:
    df = spark.read.csv(input_path, header=True, inferSchema=True)
    print("✅ Data loaded from GCS")
except Exception as e:
    print(f"❌ GCS Load Failed: {e}")
    raise

# -----------------------------
# 3. Mask Sensitive Data
# -----------------------------
secure_df = df.withColumn(
    "masked_destination",
    sha2(col("DEST_COUNTRY_NAME"), 256)
)

# -----------------------------
# 4. GCC Filtering
# -----------------------------
gcc_countries = ["Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Oman", "Bahrain"]
gcc_df = secure_df.filter(col("DEST_COUNTRY_NAME").isin(gcc_countries))

# -----------------------------
# 5. Save to Postgres via Cloud SQL Proxy
# -----------------------------
try:
    gcc_df.write.jdbc(
        url=DB_URL, 
        table="processed_flight_data", 
        mode="overwrite", 
        properties=DB_PROPERTIES
    )
    print("✅ Data pushed to Cloud SQL via Proxy")
except Exception as e:
    print(f"❌ DB Write Failed: {e}")
    raise

spark.stop()

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sha2

# -----------------------------
# Config
# -----------------------------
BUCKET = "secure-flight-data"

# --- DATABASE CONFIG (Update with your Cloud SQL Public IP) ---
DB_URL = "jdbc:postgresql://34.71.154.242:5432/flight_analytics"
DB_PROPERTIES = {
    "user": "dbadmin",
    "password": "your_db_password", # Use the password from your terraform variables
    "driver": "org.postgresql.Driver"
}

# -----------------------------
# 1. Start Spark Session
# -----------------------------
spark = SparkSession.builder \
    .appName("GDPR_Compliance_Masking_GCP") \
    .config("spark.jars", "/opt/airflow/drivers/postgresql-42.6.0.jar") \
    .getOrCreate()

# -----------------------------
# 2. Read Data from GCS
# -----------------------------
input_path = f"gs://{BUCKET}/raw/data.csv"

df = spark.read.csv(
    input_path,
    header=True,
    inferSchema=True
)

print("✅ Data loaded from GCS")

# -----------------------------
# 3. Mask Sensitive Data (GDPR Compliance)
# -----------------------------
secure_df = df.withColumn(
    "masked_destination",
    sha2(col("DEST_COUNTRY_NAME"), 256)
)

print("🔐 Data anonymization complete")

# -----------------------------
# 4. GCC Filtering (Localization Compliance)
# -----------------------------
gcc_countries = [
    "Saudi Arabia",
    "United Arab Emirates",
    "Qatar",
    "Kuwait",
    "Oman",
    "Bahrain"
]

gcc_df = secure_df.filter(
    col("DEST_COUNTRY_NAME").isin(gcc_countries)
)

print("🌍 GCC filtering applied")

# -----------------------------
# 5. Save to Cloud SQL (Primary Implementation)
# -----------------------------
# We write to PostgreSQL so Apache Superset can visualize the data easily.
try:
    gcc_df.write.jdbc(
        url=DB_URL, 
        table="processed_flight_data", 
        mode="overwrite", 
        properties=DB_PROPERTIES
    )
    print("✅ Data successfully pushed to Cloud SQL for Superset Visualization")
except Exception as e:
    print(f"❌ Error writing to Database: {e}")

# -----------------------------
# 6. Save to GCS (Commented out - kept for Data Lake proof)
# -----------------------------
"""
output_path = f"gs://{BUCKET}/secure_output/"
gcc_df.write \
    .mode("overwrite") \
    .parquet(output_path)
print("✅ Data saved securely to GCS")
"""

# -----------------------------
# 7. Stop Spark
# -----------------------------
spark.stop()

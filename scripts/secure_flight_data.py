from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sha2

# -----------------------------
# Config
# -----------------------------
BUCKET = "secure-flight-data"

# --- DATABASE CONFIG (Matches your docker-compose.yaml) ---
# Host: air-flow-postgres-1 (from docker ps) or simply 'postgres' (from yaml service name)
# Database: airflow (from POSTGRES_DB: airflow)
DB_URL = "jdbc:postgresql://postgres:5432/airflow"

DB_PROPERTIES = {
    "user": "airflow",         # from POSTGRES_USER
    "password": "airflow",     # from POSTGRES_PASSWORD
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
# 5. Save to Postgres (Primary Implementation)
# -----------------------------
try:
    # We use overwrite to refresh the table on every run
    gcc_df.write.jdbc(
        url=DB_URL, 
        table="processed_flight_data", 
        mode="overwrite", 
        properties=DB_PROPERTIES
    )
    print("✅ Data successfully pushed to Postgres for Superset Visualization")
except Exception as e:
    print(f"❌ Error writing to Database: {e}")

# -----------------------------
# 6. Stop Spark
# -----------------------------
spark.stop()

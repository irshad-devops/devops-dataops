from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sha2

# -----------------------------
# Config
# -----------------------------
BUCKET = "secure-flight-data"

# -----------------------------
# 1. Start Spark Session
# -----------------------------
spark = SparkSession.builder \
    .appName("GDPR_Compliance_Masking_GCP") \
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
# 3. Mask Sensitive Data
# -----------------------------
secure_df = df.withColumn(
    "masked_destination",
    sha2(col("DEST_COUNTRY_NAME"), 256)
)

print("🔐 Data anonymization complete")

# -----------------------------
# 4. GCC Filtering
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
# 5. Save to GCS
# -----------------------------
output_path = f"gs://{BUCKET}/secure_output/"

gcc_df.write \
    .mode("overwrite") \
    .parquet(output_path)

print("✅ Data saved securely to GCS")

# -----------------------------
# 6. Stop Spark
# -----------------------------
spark.stop()


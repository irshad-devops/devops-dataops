from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Create Spark session
spark = SparkSession.builder \
    .appName("Flight Analysis") \
    .getOrCreate()

# Read CSV
flight_data = spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load("/opt/airflow/dags/data.csv")

# Repartition
flight_data_repartition = flight_data.repartition(3)

# Filter Pakistan destination
us_pak_data = flight_data.filter("DEST_COUNTRY_NAME == 'Pakistan'")

# Filter origin Pakistan OR Singapore
us_pak_data_us = flight_data.filter(
    (col("ORIGIN_COUNTRY_NAME") == "Pakistan") |
    (col("ORIGIN_COUNTRY_NAME") == "Singapore")
)

# Group and aggregate
total_flight_pak_sing = us_pak_data_us.groupBy("DEST_COUNTRY_NAME").sum("count")

# Show result
total_flight_pak_sing.show()

# Stop Spark
spark.stop()


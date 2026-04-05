import pytest
from pyspark.sql import SparkSession

def test_spark_session():
    # Setup a local Spark session for testing
    spark = SparkSession.builder.master("local[1]").appName("CI-Test").getOrCreate()
    
    # Create dummy data with PII
    data = [("John Doe", "john@example.com"), ("Jane Smith", "jane@test.com")]
    df = spark.createDataFrame(data, ["name", "email"])
    
    # Assert the dataframe has 2 rows
    assert df.count() == 2
    spark.stop()


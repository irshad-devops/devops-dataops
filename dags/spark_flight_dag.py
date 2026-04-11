from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

# Define the DAG
with DAG(
    'flight_data_pipeline_final', 
    start_date=datetime(2026, 1, 1), 
    schedule='@daily', 
    catchup=False,
    tags=['university_lab', 'spark', 'gcp']
) as dag:

    # Task 1: Data Quality Validation using Great Expectations or Custom Python
    validate = BashOperator(
        task_id='validate_data_quality',
        bash_command='python3 /opt/airflow/scripts/validate_flights.py'
    )

    # Task 2: PII Masking and Security using PySpark
    # Note: We use the absolute path to spark-submit installed in /opt/spark
    secure_data = BashOperator(
        task_id='secure_and_mask_pii',
        bash_command=(
            '/opt/spark/bin/spark-submit '
            '--jars /opt/spark/jars/gcs-connector-hadoop3-2.2.5-shaded.jar '
            '--conf spark.hadoop.fs.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem '
            '--conf spark.hadoop.google.cloud.auth.service.account.enable=true '
            '--conf spark.hadoop.google.cloud.auth.service.account.json.keyfile=/opt/airflow/config/gcp-key.json '
            '/opt/airflow/scripts/secure_flight_data.py'
        )
    )

    # Define Dependency
    validate >> secure_data

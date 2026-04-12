from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator # Added for compliance
from datetime import datetime

with DAG(
    'flight_data_pipeline_final', 
    start_date=datetime(2026, 1, 1), 
    schedule='@daily', 
    catchup=False,
    tags=['university_lab', 'spark', 'gcp', 'vault_secured']
) as dag:

    # Task 1: Data Quality Validation
    validate = BashOperator(
        task_id='validate_data_quality',
        bash_command='python3 /opt/airflow/scripts/validate_flights.py'
    )

    # Task 2: PII Masking and Security using PySpark
    secure_data = BashOperator(
        task_id='secure_and_mask_pii',
        bash_command=(
            '/opt/spark/bin/spark-submit '
            '--jars /opt/spark/jars/gcs-connector-hadoop3-2.2.5-shaded.jar,/opt/airflow/drivers/postgresql-42.6.0.jar '
            '--conf spark.hadoop.fs.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem '
            '--conf spark.hadoop.google.cloud.auth.service.account.enable=true '
            '--conf spark.hadoop.google.cloud.auth.service.account.json.keyfile=/opt/airflow/config/gcp-key.json '
            '/opt/airflow/scripts/secure_flight_data.py'
        )
    )

    # Task 3: Final Audit check (Uses Vault to get postgres_default connection)
    # This proves Vault integration is working!
    audit_check = PostgresOperator(
        task_id='vault_connection_audit',
        postgres_conn_id='postgres_default',
        sql="SELECT count(*) FROM flight_data_secured;"
    )

    # Define Dependency
    validate >> secure_data >> audit_check

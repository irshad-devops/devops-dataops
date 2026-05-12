from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG(
    dag_id='flight_data_pipeline_final',
    start_date=datetime(2026, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=['university_lab', 'spark', 'gcp', 'vault_secured']
) as dag:

    # -----------------------------
    # Task 1: Data Quality Validation
    # -----------------------------
    validate = BashOperator(
        task_id='validate_data_quality',
        bash_command='python3 /opt/airflow/scripts/validate_flights.py'
    )

    # -----------------------------
    # Task 2: Secure + Mask PII (FIXED)
    # -----------------------------
    secure_data = BashOperator(
        task_id='secure_and_mask_pii',
        bash_command=(
            '/opt/spark/bin/spark-submit '
            '--packages com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.11,org.postgresql:postgresql:42.6.0 '
            
            # ✅ FIXED GCS CONFIG
            '--conf spark.hadoop.fs.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem '
            '--conf spark.hadoop.fs.AbstractFileSystem.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS '
            '--conf spark.hadoop.google.cloud.auth.service.account.enable=true '
            '--conf spark.hadoop.google.cloud.auth.service.account.json.keyfile=/opt/airflow/config/gcp-key.json '

            # ✅ Stability configs
            '--conf spark.executor.memory=1g '
            '--conf spark.driver.memory=1g '
            '--conf spark.sql.shuffle.partitions=2 '

            # Prevent dependency conflicts
            '--conf spark.jars.ivy=/tmp/.ivy '

            '/opt/airflow/scripts/secure_flight_data.py'
        )
    )

    # -----------------------------
    # Task 3: Audit DB
    # -----------------------------
    audit_check = PostgresOperator(
        task_id='vault_connection_audit',
        postgres_conn_id='postgres_default',
        sql="SELECT count(*) FROM processed_flight_data;"
    )

    # DAG Flow
    validate >> secure_data >> audit_check


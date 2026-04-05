from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime

with DAG('flight_data_pipeline_final', start_date=datetime(2026, 1, 1), schedule='@daily', catchup=False) as dag:

    validate = BashOperator(
        task_id='validate_data_quality',
        bash_command='python3 /opt/airflow/scripts/validate_flights.py'
    )

    secure_data = BashOperator(
        task_id='secure_and_mask_pii',
        # Removed the extra 'spark-3.5.1-bin-hadoop3' folder level
        bash_command='/opt/spark/bin/spark-submit \
            --jars /opt/spark/jars/gcs-connector-hadoop3-2.2.5-shaded.jar \
            --conf spark.hadoop.fs.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem \
            --conf spark.hadoop.google.cloud.auth.service.account.enable=true \
            --conf spark.hadoop.google.cloud.auth.service.account.json.keyfile=/opt/airflow/config/gcp-key.json \
            /opt/airflow/scripts/secure_flight_data.py'
    )

    validate >> secure_data

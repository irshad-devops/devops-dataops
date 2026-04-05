import pendulum
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator


with DAG(
        dag_id="my_bash_daily",
        start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Karachi"),
        schedule="@daily",
        catchup=False,
        tags=["demo", "bash"],
) as dag:

    say_hello = BashOperator(
            task_id="say_hello",
            bash_command='echo "Hello Airflow!!!!!! Run date is {{ds}}"'
    )

    print_whoami = BashOperator(
            task_id="print_whoami",
            bash_command="whoami"
    )


    say_hello >> print_whoami

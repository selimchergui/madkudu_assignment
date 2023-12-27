from datetime import datetime
from airflow import DAG
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
import boto3

S3_RESOURCE = boto3.resource("s3")
S3_BUCKET = "work-sample-mk-selim"
S3_PREFIX = ""

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'depends_on_past': False,
    'retries': 1,
}


def get_files_list_from_s3(bucket:str, prefix:str) -> list:
    """
    list all files under specific prefix in S3
    Args:
        bucket: S3 bucket containing seeked files
        prefix: prefix used to filter files
    Returns:
        files: list<str>: list of finded files
    """

    airflow_bucket = S3_RESOURCE.Bucket(bucket)
    files_summary = list(airflow_bucket.objects.filter(Prefix=prefix))
    csv_files = [item.key for item in files_summary if item.key.endswith('.csv')]
    return csv_files


with DAG(
    'pipeline_orchestrator',
    default_args=default_args,
    description='Copy data from S3 to Redshift and process data',
    schedule_interval='@monthly',
    catchup=False,
    max_active_runs=1
) as dag:

    start = DummyOperator(task_id="start")


    datawarehouse_pipeline = BashOperator(
        task_id="dwh_run_pipeline",
        bash_command="~/.local/bin/dbt run --project-dir /usr/local/airflow/dbt/madkudu --profiles-dir /usr/local/airflow/dbt --select tag:events",
    )

    datawarehouse_pipeline_tests = BashOperator(
        task_id="dwh_test_pipeline",
        bash_command="~/.local/bin/dbt test --project-dir /usr/local/airflow/dbt/madkudu --profiles-dir /usr/local/airflow/dbt --select tag:events",
    )


    for s3_file in get_files_list_from_s3(bucket=S3_BUCKET , prefix=S3_PREFIX):
        table_name = "src_"+s3_file.replace("/","_").split(".")[0]

        drop_table = SQLExecuteQueryOperator(
            task_id=f"drop_table_{table_name}",
            conn_id="datawarehouse",
            sql=f"""
                DROP TABLE IF EXISTS "source"."{table_name}" CASCADE;
            """
        )

        create_table = SQLExecuteQueryOperator(
            task_id=f"create_table_{table_name}",
            conn_id="datawarehouse",
            sql=f"""
                CREATE TABLE "source"."{table_name}" (
                    id VARCHAR(36) PRIMARY KEY,
                    timestamp DATE,
                    email VARCHAR(100), country VARCHAR(200),
                    ip VARCHAR(50),
                    uri VARCHAR(100),
                    "action" VARCHAR(100),
                    tags VARCHAR(1000)
                );
            """
        )

        copy_data = S3ToRedshiftOperator(
            task_id=f"copy_data_to_{table_name}",
            schema="source",
            table=table_name,
            aws_conn_id="my_aws",
            s3_bucket=S3_BUCKET,
            s3_key=s3_file,
            redshift_conn_id="datawarehouse",
            copy_options=["csv", "IGNOREHEADER 1"],  # Add any additional COPY options here
            autocommit=True,
            dag=dag,
        )

        start >> drop_table >> create_table >> copy_data >> datawarehouse_pipeline >> datawarehouse_pipeline_tests

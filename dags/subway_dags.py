from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta
import subprocess
from pendulum import timezone

KST = timezone("Asia/Seoul")


def run_pipeline():
    # Airflow 컨테이너 내부에서 직접 실행
    result = subprocess.run(
        ["python", "/app/etl/make_pipeline.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise Exception(f"ETL execution failed:\n{result.stderr}")
    print(result.stdout)


with DAG(
    dag_id="subway_pipeline",
    schedule_interval="30 12 4 * *",  # 매월 4일 12시 30분에 실행
    start_date=KST.datetime(2025, 11, 1),
    catchup=False,
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=3)
    }
) as dag:
    run_etl = PythonOperator(
        task_id="run_subway_etl",
        python_callable=run_pipeline
    )
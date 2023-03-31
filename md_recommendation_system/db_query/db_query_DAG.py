"""zfl data pipeline dag"""


import pendulum
from airflow import DAG
from datetime import date, timedelta, datetime
from airflow.operators.bash_operator import BashOperator
from airflow.operators.docker_operator import DockerOperator
from airflow.operators.dummy_operator import DummyOperator

  

 
local_tz = pendulum.timezone("Asia/Taipei")
query_start = str(date.today() - timedelta(days=2))
query_end = str(date.today() - timedelta(days=1))
 
default_args = {
        'owner'                 : 'AI',
        'description'           : 'desc',
        'depend_on_past'        : False,
        'start_date'            : datetime(2021, 8, 5, tzinfo=local_tz),
        'retries'               : 1,
        'retry_delay'           : timedelta(minutes=1)
}


with DAG('ZFL-Data-Pipeline', default_args=default_args, schedule_interval="15 01 * * *", catchup=False) as dag:
    start_dag = DummyOperator(
        task_id='start_dag'
        )
 
    end_dag = DummyOperator(
        task_id='end_dag'
        )
 
    t1 = DockerOperator(
        task_id='ZFL-Data-Pipeline',
        image='zfl_data_pipeline',
        auto_remove=True,
        api_version='auto',
        command=f'python3 db_query/run.py --query_start "{query_start}" --query_end "{query_end}"',
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        volumes=["/home/alberthsu/md_recommendation_system:/tmp/zfl"]
        )

    ts1 = BashOperator(
        task_id='T_sleep1',
        bash_command='sleep 5',
        retries=1
    )

    # dag task
    start_dag >> t1 >> ts1 >> end_dag
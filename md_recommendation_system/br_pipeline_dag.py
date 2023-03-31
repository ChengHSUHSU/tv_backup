"""br pipeline dag"""
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
        'retries'               : 3,
        'retry_delay'           : timedelta(minutes=1)
}


with DAG('BR-Recommend-Head', default_args=default_args, schedule_interval="1 * * * *", catchup=False) as dag:
    start_dag = DummyOperator(
        task_id='start_dag'
        )
 
    end_dag = DummyOperator(
        task_id='end_dag'
        )
 
    db_query_node = DockerOperator(
            task_id='DBQuery',
            image='auto_rs/all_pipeline',
            auto_remove=True,
            api_version='auto',
            command='python3 db_query/run.py',
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            volumes=["/home/ubuntu/md_recommendation_system:/tmp"]
        )

    recommender_node = DockerOperator(
            task_id='Recommender',
            image='auto_rs/all_pipeline',
            auto_remove=True,
            api_version='auto',
            command='python3 recommender/run.py',
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            volumes=["/home/ubuntu/md_recommendation_system:/tmp"]
        )

    ranker_node = DockerOperator(
            task_id='Ranker',
            image='auto_rs/all_pipeline',
            auto_remove=True,
            api_version='auto',
            command='python3 ranker/run.py',
            docker_url="unix://var/run/docker.sock",
            network_mode="bridge",
            volumes=["/home/ubuntu/md_recommendation_system:/tmp"]
        )

    ts1 = BashOperator(
        task_id='T_sleep_DBQuery',
        bash_command='sleep 5',
        retries=1
    )

    ts2 = BashOperator(
        task_id='T_sleep_Recommender',
        bash_command='sleep 5',
        retries=1
    )

    ts3 = BashOperator(
        task_id='T_sleep_Ranker',
        bash_command='sleep 5',
        retries=1
    )

    # dag task
    start_dag >> ts1 >> db_query_node >> ts2 >> recommender_node >> ts3 >> ranker_node>> end_dag





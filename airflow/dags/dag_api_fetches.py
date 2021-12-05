from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator


default_args = {
    'owner': 'moshe',
    'start_date': datetime(2021,10,10),
    'retries': 0,
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}

def prepare_calls():
    output_filename = '/data/state/scrap_links.jsonl'
    
    combinations = [
        {
        "url": "https://api.github.com/search/users?q={query}&sort=stars&page={page}&per_page=100",
            "iterations": [
                {"type": "param", "name": "query", "values": ["language:python", "react python", "react", "javascript", "java", "scala", "scala data", "javascript lib", "lib", "aws", "cloud"]},
                {"type": "param", "name": "page", "values": [1,2,3,4,5,6,7,8,9,10]}
            ]
        }
    ]

dag = DAG('api_fetcher',
          default_args=default_args,
          description='',
          schedule_interval=False,
          catchup=False,
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

preparation = PythonOperator(
        task_id='preparation',
        python_callable=prepare_calls,
    )
end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)


start_operator  >> load_rss >> end_operator
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
import itertools
import operator
from helpers.ioutils import jsonl_dump
import hashlib


default_args = {
    'owner': 'moshe',
    'start_date': datetime(2019,1,1),
    'retries': 0,
    'catchup': False,
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}


def scrap_links_gen():
    target_apis = [
        
        {
            "schema": "github-repos",
            "rate_control_group": "github",
            "url": "https://api.github.com/search/repositories?q={query}&page={page}&per_page=100",
            "iterations": [
                {"type": "param", "name": "query", "values": ["language:python", "react python", "react", "javascript", "java", "scala", "scala data", "javascript lib", "lib", "aws", "cloud"]},
                {"type": "param", "name": "page", "values": [1,2,3,4,5,6,7,8,9,10]}
            ]
        },
        {
            "schema": "github-users",
            "rate_control_group": "github",
            "url": "https://api.github.com/search/users?q={query}&page={page}&per_page=100",
            "iterations": [
                {"type": "param", "name": "query", "values": ["language:python", "react python", "react", "javascript", "java", "scala", "scala data", "javascript lib", "lib", "aws", "cloud"]},
                {"type": "param", "name": "page", "values": [1,2,3,4,5,6,7,8,9,10]}
            ]
        },
    ]

    for target_api in target_apis:
        param_names = tuple(
            map(
                lambda it: it['name'], 
                target_api['iterations']))

        for param_values in itertools.product(
            *(tuple(map(
                lambda it: it['values'],  
                target_api['iterations'])))):
            url = target_api['url'].format(**dict(zip(param_names, param_values)))
            yield dict(
                url=url,
                rate_control_group=target_api['rate_control_group'],
                schema=target_api['schema'],
                id=hashlib.md5(url.encode()).hexdigest()
            )

def write_links_file():
    output_filename = '/data/scrap_jobs/scrap_links.jsonl'
    jsonl_dump(output_filename, scrap_links_gen())


dag = DAG('api_fetcher',
          default_args=default_args,
          description='',
          schedule_interval=None
          )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

step_preparation = PythonOperator(
        task_id='preparation',
        python_callable=write_links_file,
        dag=dag
    )
end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)


start_operator  >> step_preparation >> end_operator
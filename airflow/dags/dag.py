from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from operators import (BinanceTradesOperator,)

AWS_CONNECTION_ID = 'aws_credentials'
BINANCE_CONNECTION_ID = 'binance'
default_args = {
    'owner': 'moshe',
    'start_date': datetime(2019,1,1),
    'retries': 0,
    # 'retry_delay': timedelta(minutes=1),
    'catchup': False,
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}

dag = DAG('trader',
          default_args=default_args,
          description='',
          schedule_interval=None
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

load_trades_to_s3 = BinanceTradesOperator(
    task_id='binance_trades',
    dag=dag,
    symbol= 'BTCUSDT',
    binance_connection_id=BINANCE_CONNECTION_ID,
    aws_connection_id=AWS_CONNECTION_ID,
    s3_bucket='pc360-test-bucket4',
)

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)


start_operator  >> load_trades_to_s3 >> end_operator
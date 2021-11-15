from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from operators import (
    BinanceTradesOperator,)

from helpers.config import (
    AWS_CONNECTION_ID,
    BINANCE_CONNECTION_ID,
)

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

symbols = (
    'ETH',
    # 'DOGE',
    # 'BNB',
    # 'XRP',
    # 'AVAX',
    # 'SOL',
    # 'TRX',
    # 'LRC'
)

load_trades_to_s3 = tuple(
    BinanceTradesOperator(
        task_id=f'fetch_trades_{symbol}',
        dag=dag,
        symbol=f'{symbol}BTC',
        binance_connection_id=BINANCE_CONNECTION_ID,
        aws_connection_id=AWS_CONNECTION_ID,
        s3_bucket='dummy-bucket',
    )
    for symbol in symbols)

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)


start_operator  >> load_trades_to_s3 >> end_operator
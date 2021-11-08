from airflow.hooks.base_hook import BaseHook
from typing import Tuple

AWS_CONNECTION_ID = 'aws'
BINANCE_CONNECTION_ID = 'binance'

def get_connection_credentials(id: str)->Tuple[str,str]:
    conn = BaseHook.get_connection(id)
    return conn.login, conn.password
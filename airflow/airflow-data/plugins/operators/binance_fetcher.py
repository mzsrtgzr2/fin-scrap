import os
import time
from datetime import datetime
import itertools
from collections import OrderedDict
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.contrib.hooks.aws_hook import AwsHook
from typing import *
from binance.exceptions import BinanceAPIException
from binance.client import Client
from helpers import ioutils
from helpers.pyutils import is_non_empty_iterator, batches
from helpers.config import get_connection_credentials
import tempfile
import pandas as pd
from tenacity import retry, wait_random, stop_after_attempt
from ratelimit import limits


# https://github.com/airflow-plugins/mssql_plugin/blob/master/operators/mssql_to_s3_operator.py
# https://dev.to/aws/reading-and-writing-data-across-different-aws-accounts-with-amazon-managed-workflows-for-apache-airflow-v2-x-3319



class BinanceTradesOperator(BaseOperator):
    version = 1
    ui_color = '#dd42f5'

    @apply_defaults
    def __init__(self,
                binance_connection_id: str,
                symbol: str,
                aws_connection_id: str,
                s3_bucket: str,
                 *args, **kwargs):

        super(BinanceTradesOperator, self).__init__(*args, **kwargs)
        
        self.symbol = symbol
        self.aws_connection_id = aws_connection_id
        self.binance_connection_id = binance_connection_id
        self.s3_bucket = s3_bucket

    def execute(self, context):
        # aws_hook = AwsHook(aws_conn_id=self.aws_connection_id, client_type='s3')
        # credentials = aws_hook.get_credentials()

        self.binance_api_key, self.binance_api_secret = get_connection_credentials(
            self.binance_connection_id
        )
        
        binance_client = self._safe_get_client(self.binance_api_key, self.binance_api_secret)

        # rootdir = f's3://{self.s3_bucket}'
        rootdir = '/data'

        marker = os.path.join(rootdir, f'raw/markers/marker-trades-{self.symbol}.json')

        ioutils.mkdir(os.path.join(rootdir, 'raw/markers/'), exist_ok=True)

        self.log.info('trying to check marker file %s', marker)
        
        if ioutils.is_file_exists(marker):
            self.log.info('marker exists')
            earliest_id = (ioutils.json_load(marker) or {}
            ).get('earliest_id', -1)
        else:
            self.log.info('marker not exist')
            earliest_id = None

        dt_to_dfs = OrderedDict()
        while True:
            trades = self._safe_get_trades(
                binance_client,
                symbol=self.symbol,
                limit=1000,
                fromId=(earliest_id-1001) if earliest_id else None
            )

            df = pd.DataFrame(trades)
            df.index = pd.to_datetime(df.time, unit='ms')

            for key, group in df.groupby([(df.index.year),(df.index.month), (df.index.day)]):

                agg_df = dt_to_dfs.get(key, None)
                if agg_df is None:
                    dt_to_dfs[key] = group
                else:
                    dt_to_dfs[key] = pd.concat([agg_df, group])

            keys = tuple(dt_to_dfs.keys())

            for key in keys:
                other_keys = set(keys) - {key}
                if other_keys and any(other<key for other in other_keys):
                    # persist this df
                    year, month, day = key

                    dest = os.path.join(
                        rootdir,
                        f'raw/trades/year={year}/month={month:02}/day={day:02}/',
                        f'trades__{self.version}__{self.symbol}__{year}-{month:02}-{day:02}__.parquet'
                    )

                    ioutils.mkdir(os.path.dirname(dest), exist_ok=True)

                    self.log.info('writing to %s', dest)

                    group = dt_to_dfs[key]
                    # persist
                    group.to_parquet(
                        dest,
                        index=False,
                        # storage_options={
                        #     'key': credentials.access_key,
                        #     'secret': credentials.secret_key
                        # },
                    )

                    earliest_id_in_group = group.id.min()
                    ioutils.json_dump(marker, {'earliest_id': int(earliest_id_in_group)})

                    # remove df from memory
                    dt_to_dfs.pop(key)

            earliest_id = df.id.min()
            self.log.info(
                'earliest id to update is %d, in mem keys: %s', 
                earliest_id, tuple(dt_to_dfs.keys())
            )
            

    
    @retry(wait=wait_random(min=60, max=180), stop=stop_after_attempt(100))
    @limits(calls=100, period=60)
    def _safe_get_trades(self, binance_client: Client, *args, **kwargs):
        try:
            return binance_client.get_historical_trades(*args, **kwargs)
        except BinanceAPIException as exp:
            self.log.info('binance-exception while api %s', exp)
            raise
        except Exception as exp:
            self.log.info('generic-exception while api %s', exp)
            raise

    @retry(wait=wait_random(min=60, max=180), stop=stop_after_attempt(100))
    @limits(calls=100, period=60)
    def _safe_get_client(self, *args, **kwargs):
        try:
            return Client(*args, **kwargs)
        except BinanceAPIException as exp:
            self.log.info('binance-exception while api %s', exp)
            raise
        except Exception as exp:
            self.log.info('generic-exception while api %s', exp)
            raise


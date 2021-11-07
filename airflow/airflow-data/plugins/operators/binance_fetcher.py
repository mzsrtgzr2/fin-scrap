import os
import time
from datetime import datetime
import itertools
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.contrib.hooks.aws_hook import AwsHook
from typing import *
from binance.client import Client
from helpers import ioutils
from helpers.pyutils import is_non_empty_iterator
import tempfile
import pandas as pd


# https://github.com/airflow-plugins/mssql_plugin/blob/master/operators/mssql_to_s3_operator.py
# https://dev.to/aws/reading-and-writing-data-across-different-aws-accounts-with-amazon-managed-workflows-for-apache-airflow-v2-x-3319
from itertools import islice, chain

def batches(iterable, size):
    sourceiter = iter(iterable)
    while True:
        batchiter = islice(sourceiter, size)
        yield chain([batchiter.next()], batchiter)
    
class BinanceTradesOperator(BaseOperator):
    version = 1
    ui_color = '#dd42f5'

    @apply_defaults
    def __init__(self,
                binance_api_key: str,
                binance_api_secret: str,
                symbol: str,
                aws_connection_id: str,
                s3_bucket: str,
                 *args, **kwargs):

        super(BinanceTradesOperator, self).__init__(*args, **kwargs)
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret
        self.symbol = symbol
        self.aws_connection_id = aws_connection_id
        self.s3_bucket = s3_bucket

    def execute(self, context):
        aws_hook = AwsHook(aws_conn_id=self.aws_connection_id, client_type='s3')
        credentials = aws_hook.get_credentials()

        marker_key = f'raw/markers/marker-trades-{self.symbol}.json'
    
        self.log.info('trying to check marker file %s', marker_key)
        if ioutils.is_s3_key_exists(self.aws_connection_id, self.s3_bucket, marker_key):
            self.log.info('marker exists')
            last_id = (ioutils.read_s3_json(
                self.aws_connection_id, self.s3_bucket, marker_key) or {}
            ).get('last_id', -1)
        else:
            self.log.info('marker not exist')
            last_id = -1

        dt, stream = self._get_symbol_next_dt_trades(last_id)

        if not dt:
            self.log.info('no trades found after trade %d', last_id)
            return
        self.log.info('found trades stream for %s', dt)

        dest = (
            f's3://{self.s3_bucket}/'
            f'raw/trades/year={dt.year}/month={dt.month:02}/day={dt.day:02}/'
            f'trades__{self.version}__{self.symbol}__{dt.year}-{dt.month:02}-{dt.day:02}.csv'
        )
        self.log.info('writing to %s', dest)
        df = pd.DataFrame(stream)
        df.to_csv(
            dest,
            index=False,
            storage_options={
                'key': credentials.access_key,
                'secret': credentials.secret_key
            },
        )

        max_id = df.id.max()
        self.log.info('last id to update is %d', max_id)
        ioutils.write_s3_json(
            self.aws_connection_id, self.s3_bucket, marker_key, {'last_id': int(max_id)})

    def _get_symbol_trades(self, start_id=0)->Iterable[Dict]:
        client = Client(self.binance_api_key, self.binance_api_secret)

        id = start_id
        
        while True:
            self.log.info("getting trades from id %s", id)
            trades = client.get_historical_trades(symbol=self.symbol, limit=1000, fromId=id)
            for trade in trades:
                yield trade
                id = max(id, trade['id'])
    
    def _get_symbol_next_dt_trades(self, last_id: int)->Tuple[datetime, Iterable[Dict]]:
        def _it(start_id: int):
            dt = None
            counter = 0
            id = 0
            for trade in self._get_symbol_trades(start_id+1):

                trade_dt = datetime.fromtimestamp(trade['time']/1000).date()
                if not dt:
                    dt = trade_dt

                if trade_dt != dt:
                    self.log.info('found the next date trade %s', trade)
                    break

                yield trade
                counter+=1
                id = max(id, trade['id'])
            
        data = _it(last_id)

        first_trade = next(data, None)
        if not first_trade:
            self.log.info('failed to fetch trades')
            return None, None
        
        # what dt are we looking at?
        dt = datetime.fromtimestamp(first_trade['time']/1000).date()

        stream = itertools.chain([first_trade], data)
        return dt, stream
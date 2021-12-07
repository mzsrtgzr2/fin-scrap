
from io import BytesIO, StringIO
import os
import json
import pyarrow as pa
import pyarrow.parquet as pq
from typing import *
from datetime import datetime
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from contextlib import closing

AWS_CONNECTION_ID = 'aws'

s3 = S3Hook(aws_conn_id=AWS_CONNECTION_ID)


def mkdir(path, exist_ok=False):
    """creates recursively the directory for both local filesystem an S3"""
    # no need to create dirs on s3 ahead
    if _is_s3path(path):
        return
    return os.makedirs(path, exist_ok=exist_ok)


def s3_upload_file(s3_conn_id: str, s3_bucket:str, s3_key:str, filename: str):
    with closing(S3Hook(s3_conn_id=s3_conn_id)) as s3:
        s3.load_file(
            filename=filename,
            bucket_name=s3_bucket,
            key=s3_key,
            replace=True
        )

def s3_upload_bytes(s3_conn_id: str, s3_bucket:str, s3_key:str, bytes: BytesIO):
    with closing(S3Hook(s3_conn_id=s3_conn_id)) as s3:
        s3.load_bytes(
            bytes_data=bytes,
            bucket_name=s3_bucket,
            key=s3_key,
            replace=True
        )

def write_file_parquet(it: Iterable, dest: str, compression='SNAPPY'):
    pq.write_table(it, dest, compression=compression)

def write_parquet_bytes(stream: Iterable[Dict])->BytesIO:
    """ Assumes path starts with s3:// """
    writer = pa.BufferOutputStream()
    pq.write_table(stream, writer)
    return bytes(writer.getvalue())

def split_s3_path(s3_path):
    path_parts=s3_path.replace('s3://','').split('/')
    bucket=path_parts.pop(0)
    key='/'.join(path_parts)
    return bucket, key

def _is_s3path(path):
    return path.lower().startswith('s3://')

def is_file_exists(fname):
    """returns True if file exists, false otherwise"""
    if _is_s3path(fname):
        bucket, key = split_s3_path(fname)
        return s3.check_for_key(key, bucket_name=bucket)
    return os.path.isfile(fname)


def json_load(fname: str)->Dict:
    if _is_s3path(fname):
        bucket, key = split_s3_path(fname)
        return json.loads(s3.read_key(key, bucket_name=bucket))
    with open(fname, 'r') as fp:
        return json.load(fp)

def json_dump(fname: str, data: dict):
    if _is_s3path(fname):
        bucket, key = split_s3_path(fname)
        s3.load_string(json.dumps(data), key, bucket_name=bucket, replace=True)
    with open(fname, 'w') as fp:
        json.dump(data, fp)

def jsonl_dump(fname: str, data: Iterable[dict]):
    with open(fname, 'w') as fp:
        for it in data:
            json.dump(it, fp)
            fp.write('\n')


def lookup_latest_date_partition(
    aws_conn_id: str, s3_bucket:str, path: str
        )->Optional[Tuple[datetime, str]]:
    
    with closing(S3Hook(aws_conn_id=aws_conn_id)) as s3:
        lookfor = os.path.join(
            path, 'year='
        )
        year_paths = tuple(s3.list_keys(bucket_name=s3_bucket, prefix=lookfor))
        print(s3_bucket, lookfor)
        print(year_paths)
        max_year = max(*(
            int(_y_p.split('/')[-1].split('=')[1])
            for _y_p in year_paths
        ))

        lookfor = os.path.join(
            path, f'year={max_year}', 'month='
        )
        month_paths = s3.list_keys(bucket_name=s3_bucket, prefix=lookfor)
        max_month = max(*(
            int(_y_p.split('/')[-1].split('=')[1])
            for _y_p in month_paths
        ))

        lookfor = os.path.join(
            path, f'year={max_year}', f'month={max_month}', 'day='
        )

        days_paths = s3.list_keys(bucket_name=s3_bucket, prefix=lookfor)
        max_day = max(*(
            int(_y_p.split('/')[-1].split('=')[1])
            for _y_p in days_paths
        ))

        return datetime(
            max_year, max_month, max_day
        ), os.path.join(
            path, f'year={max_year}', f'month={max_month}', f'day={max_day}'
        )
        


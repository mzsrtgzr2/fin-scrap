import os
from datetime import datetime, timedelta
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from typing import *
from helpers import ioutils
import pandas as pd
from tenacity import retry, wait_random, stop_after_attempt
from ratelimit import limits
import feedparser

MINUTE = timedelta(minutes=1)

class RssOperator(BaseOperator):
    version = 1
    ui_color = '#dd42f5'

    @apply_defaults
    def __init__(self,
                urls,
                 *args, **kwargs):

        super(RssOperator, self).__init__(*args, **kwargs)
        self.urls = urls

    def execute(self, context):
        
        rootdir = '/data'

        marker = os.path.join(rootdir, f'raw/markers/marker-rss.json')

        ioutils.mkdir(os.path.join(rootdir, 'raw/markers/'), exist_ok=True)

        self.log.info('trying to check marker file %s', marker)
        
        latest_date = None
        if ioutils.is_file_exists(marker):
            self.log.info('marker exists')
            marker_data = ioutils.json_load(marker)
            if 'latest_date' in marker_data:
                latest_date = datetime.fromtimestamp(marker_data['latest_date'])

        self.log.info('latest date to fetch entries is %s', latest_date)
        results = []
        
        for url in self.urls:
            self.log.info('fetching from %s', url)
            
            feed = self._safe_get_feed(url)

            skipped_no_date = 0
            skipped_old = 0
            for e in feed.entries:
                
                self.log.debug('%s', e)

                if 'published_parsed' not in e or e.published_parsed is None:
                    skipped_no_date += 1
                    continue
                
                dt = datetime(*e.published_parsed[:6])

                if latest_date > dt:
                    skipped_old += 1
                    continue

                results.append(
                    (dt, e.title, e.get('summary') or e.title, e.link) 
                )
        
            self.log.info('total entries skipped - no date %d, old %d', 
                skipped_no_date, skipped_old)


        df = pd.DataFrame(results, columns=('time', 'title', 'summary', 'link'))

        if df.empty:
            self.log.info('no relevant results to write. quitting.')
            return

        latest_date = df.time.max()
        year = latest_date.year
        month = latest_date.month
        day = latest_date.day
        epoch = latest_date.timestamp()

        dest = os.path.join(
            rootdir,
            f'raw/rss/year={year}/month={month:02}/day={day:02}/',
            f'rss__{self.version}__{year}-{month:02}-{day:02}-{epoch}__.parquet'
        )

        ioutils.mkdir(os.path.dirname(dest), exist_ok=True)

        self.log.info('writing to %s', dest)

        df.to_parquet(
            dest,
            index=False,
        )

        ioutils.json_dump(marker, {'latest_date': epoch})

        self.log.info('latest_date to update is %s', latest_date)
            
    
    @retry(wait=wait_random(min=60, max=180), stop=stop_after_attempt(100))
    @limits(calls=100, period=60)
    def _safe_get_feed(self, url: str):
        try:
            return feedparser.parse(url)
        except Exception as exp:
            self.log.info('generic-exception while api %s', exp)
            raise


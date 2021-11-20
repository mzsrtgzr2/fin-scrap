from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from operators import RssOperator


default_args = {
    'owner': 'moshe',
    'start_date': datetime(2021,10,10),
    'retries': 0,
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}

dag = DAG('rss_fetcher',
          default_args=default_args,
          description='',
          schedule_interval='*/5 * * * *',
          catchup=False,
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)


RSS_FEEDS = (
    'http://rss.cnn.com/rss/edition_world.rss',
    'http://rss.cnn.com/rss/edition_us.rss',
    'http://rss.cnn.com/rss/edition_africa.rss',
    'http://rss.cnn.com/rss/edition_americas.rss',
    'http://rss.cnn.com/rss/edition_europe.rss',
    'http://rss.cnn.com/rss/edition_meast.rss',
    'http://rss.cnn.com/rss/moeny_news_international.rss',
    'http://rss.cnn.com/rss/edition_technology.rss',
    'http://rss.cnn.com/rss/edition_space.rss',
    'http://www.chinadaily.com.cn/rss/china_rss.xml',
    'http://www.chinadaily.com.cn/rss/bizchina_rss.xml',
    'http://www.chinadaily.com.cn/rss/opinion_rss.xml',
    'https://news.google.com/rss/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNREZqY0hsNUVnSmxiaWdBUAE', # covid news
    'https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JXVnVMVWRDR2dKSlRDZ0FQAQ', # business news    
    'https://news.google.com/rss/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGRqTVhZU0JXVnVMVWRDR2dKSlRDZ0FQAQ', # tech news
    'https://news.google.com/rss/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNR3QwTlRFU0JXVnVMVWRDS0FBUAE', # health news
    'https://www.rt.com/rss/',
    'https://russia-insider.com/en/all-content/rss',
    'http://feeds.foxnews.com/foxnews/national',
    'http://feeds.foxnews.com/foxnews/world',
    'http://feeds.foxnews.com/foxnews/politics',
    'http://feeds.foxnews.com/foxnews/scitech',
    'https://cointelegraph.com/rss',
    'https://www.newsbtc.com/feed',
    'https://www.cryptoninjas.net/feed/',
    'https://goldsilver.com/blog/rss/',
    'http://www.koreatimes.co.kr/www/rss/northkorea.xml',
    'http://www.koreatimes.co.kr/www/rss/tech.xml',
    'http://www.koreatimes.co.kr/www/rss/rss.xml',
    'https://irandaily.ir/News/Feed',
    'https://irandaily.ir/News/Feed?id=-3'    
)

load_rss = RssOperator(
        task_id=f'rss_fetcher',
        dag=dag,
        urls = RSS_FEEDS
    )

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)


start_operator  >> load_rss >> end_operator
FROM apache/airflow:2.2.1
USER root
RUN apt-get update \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir --user python-binance==1.0.15 binance==0.3 pandas==1.3.4
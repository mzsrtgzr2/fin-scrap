
from pyspark.sql.functions import from_json, to_json, col, unbase64, base64, split, expr

def load_kafka_stream(spark, topic, schema):
    df = spark.readStream\
        .format('kafka')\
        .option("kafka.bootstrap.servers", "kafka:19092") \
        .option("subscribe", topic) \
        .option("startingOffsets", "earliest") \
        .load()
    
    return df.select(
        col('key'),
        from_json(col('value').cast('string'), schema).alias('value_json')
    ).selectExpr('key', 'value_json.*')

def write_stream_to_console(df):
    df\
    .writeStream.format('console').outputMode("update")\
        .start()\
            .awaitTermination()

def to_table(table_name: str, df):
    return df\
    .writeStream.format('memory').queryName(table_name).outputMode("complete")\
        .start()
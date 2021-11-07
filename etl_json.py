from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.avro.functions import from_avro
from utils.schemas import get_trade_schema
from utils.spark import write_stream_to_console
from pyspark.sql.types import (
    StructField, StructType, StringType, BooleanType, ArrayType, DateType, FloatType)


spark = SparkSession.builder\
    .appName('trades-5m-snapshots').getOrCreate()
    # .config("spark.packages", packages_str)\
    # .master("spark://127.0.0.1:7077")\
spark.sparkContext.setLogLevel('WARN')


broker_url = "kafka:19092"

trades_rx_schema = 'time long, symbol string, buyer string, seller string,price float,quantity float'
trades_rx_dstream = spark.readStream\
  .format("kafka")\
  .option("kafka.bootstrap.servers", broker_url)\
  .option("subscribe", 'trades-rx')\
  .option("mode","PERMISSIVE")\
  .load()\
  .select(
    F.from_json(
      F.col('value').cast('string'), trades_rx_schema).alias('value')
  )\
  .selectExpr('value.*')\
  .withColumn('time', F.expr('cast((time/1000) as timestamp)'))

# .option("startingOffsets", "earliest")\

# count10s_dstream = trades_rx_dstream\
#   .withWatermark("time", "1 minute")\
#   .groupBy(
#     'buyer',
#     F.window("time", "5 minutes")
# ).agg(
#   F.count('*').alias('transactions'),
#   F.sum('quantity').alias('total_quantity'),
#   F.avg('price').alias('avg_price'),
# ).select(
#   'window.*',
#   'buyer',
#   'transactions',
#   'total_quantity',
#   'avg_price'
# )



write_stream = trades_rx_dstream.repartition(1).writeStream\
    .format('csv')\
    .option("checkpointLocation", "/tmp/kafka-checkpoint-4") \
    .option("failOnDataLoss", "false").start('/home/workspace/output/')

write_stream_to_console(trades_rx_dstream)

write_stream.awaitTermination()

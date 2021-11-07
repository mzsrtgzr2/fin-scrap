from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.avro.functions import from_avro
# import findspark
from utils.schemas import get_trade_schema
from utils.spark import write_stream_to_console

# packages = [
#     "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2",
#     "org.apache.spark:spark-avro_2.12:3.1.2"
#     ] 
# findspark.add_packages(packages)

# packages_str = ','.join(packages)
# import os

# os.environ['PYSPARK_SUBMIT_ARGS'] = f'--packages {packages_str} pyspark-shell'

spark = SparkSession.builder\
    .appName('trades-5m-snapshots').getOrCreate()
    # .config("spark.packages", packages_str)\
    # .master("spark://127.0.0.1:7077")\
spark.sparkContext.setLogLevel('WARN')


broker_url = "kafka:19092"

# trades_schema = get_trade_schema("/home/workspace/trade.avsc")
trades_schema = """
{
   "namespace": "default",
   "name": "TradeReceived",
   "type": "record",
   "fields" : [
     {
       "name" : "symbol",
       "type" : "string"
     },
     {
       "name" : "price",
       "type" : "float"
     },
     {
       "name" : "quantity",
       "type" : "float"
     },
     {
       "name" : "buyer",
       "type" : "string"
     },
     {
       "name" : "seller",
       "type" : "string"
     }
   ]
}
"""

trades_rx_dstream = spark.readStream\
  .format("kafka")\
  .option("kafka.bootstrap.servers", broker_url)\
  .option("subscribe", 'trades-rx')\
  .option("mode","PERMISSIVE")\
  .option("startingOffsets", "latest")\
  .load()\
  .select(
    # from_avro(F.col('value'), trades_schema, {"mode":"PERMISSIVE"}).alias('value_')
    from_avro(F.col('value'), trades_schema, {"mode":"PERMISSIVE"}).alias('value_')
  )\
  .selectExpr('value_.*')

#   .option("maxOffsetsPerTrigger", 20)\
#   .option("startingOffsets", "earliest")\


write_stream_to_console(trades_rx_dstream)
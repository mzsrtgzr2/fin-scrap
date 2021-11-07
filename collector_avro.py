import structlog
from binance import ThreadedWebsocketManager
from kafkian import Producer
from confluent_kafka import avro

from kafkian.serde.avroserdebase import AvroRecord
from kafkian.serde.serialization import AvroSerializer, AvroStringKeySerializer

from utils.schemas import get_trade_schema

logger = structlog.get_logger()

api_key = 'xxx'
api_secret = 'yyy'

BROKER='127.0.0.1:9092'
SCHEMA_REGISTRY_URL='http://localhost:7070'


value_schema_str = get_trade_schema('trade.avsc')


class TradeReceived(AvroRecord):
    _schema = avro.loads(value_schema_str)

def main():

    symbol = 'BNBBTC'

    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()

    PRODUCER_CONFIG = {
        'bootstrap.servers': BROKER
    }
    producer = Producer(
        PRODUCER_CONFIG,
        key_serializer=AvroStringKeySerializer(SCHEMA_REGISTRY_URL),
        value_serializer=AvroSerializer(SCHEMA_REGISTRY_URL)
    )

    def handle_socket_message(msg):
        # print(f"message type: {msg.get('data', {}).get('e')}")

        data = msg['data']

        message = TradeReceived(dict(
            quantity=float(data['q']),
            price=float(data['p']),
            symbol=data['s'],
            buyer=str(data['b']),
            seller=str(data['a']),
            time=int(data['T']),
        ))

        # logger.info("rx", **msg.get('data', {}))
        logger.info("rx", **message)

        key = f"{data['E']}_{data['a']}_{data['b']}"

        try:
            producer.produce('trades-rx', key, message, sync=True)
        except Exception:
            logger.exception("Failed to produce event")
        
    # twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

    # multiple sockets can be started
    # twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

    # or a multiplex socket can be started like this
    # see Binance docs for stream names

    # https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#trade-streams
    streams = ['bnbbtc@trade']
    twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)

    twm.join()


if __name__ == "__main__":
   main()
from utils.binance import get_binance_rest_client
from utils.config import load_config
import structlog
import time
import json
from datetime import datetime

logger = structlog.get_logger()


config = load_config()
client = get_binance_rest_client(config)

asset = 'BTCUSDT'


id = 0

while True:
    logger.info("getting trades", id=id)
    trades = client.get_historical_trades(symbol=asset, limit=1000, fromId=id)
    for trade in trades:
        dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(trade['time']/1000))
        logger.info("trade", **trade, dt=dt)
        id = max(id, trade['id'])

    
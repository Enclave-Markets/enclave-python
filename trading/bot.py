import simplejson as json
import websocket
from decimal import *
from datetime import datetime
from collections import namedtuple
from typing import NamedTuple
import traceback
import logging
import hmac
import hashlib
import time
import dotenv
import argparse
import uuid

from enclave.client import Client

getcontext().prec = 6

class BookLevel(NamedTuple):
    price: Decimal
    size: Decimal

class Config(NamedTuple):
    market: str
    bid_size: Decimal
    ask_size: Decimal
    min_edge_bps: Decimal
    max_position: Decimal
    price_increment: Decimal
    market_making_enabled: bool
    sniping_enabled: bool
    check_secs: Decimal
    sniper_edge_bps: Decimal = Decimal("5")

avaxConfig = Config(
    market="AVAX-USD.P",
    bid_size=Decimal("41.111"),
    ask_size=Decimal("41.222"),
    min_edge_bps=Decimal("10"),
    max_position=Decimal("100"),
    price_increment=Decimal("0.01"),
    market_making_enabled=True,
    sniping_enabled=True,
    check_secs=Decimal("1"),
)

ethConfig = Config(
    market="ETH-USD.P",
    bid_size=Decimal("0.5111"),
    ask_size=Decimal("0.5222"),
    min_edge_bps=Decimal("10"),
    max_position=Decimal("1"),
    price_increment=Decimal("1"),
    market_making_enabled=True,
    sniping_enabled=True,
    check_secs=Decimal("1"),
)

btcConfig = Config(
    market="BTC-USD.P",
    bid_size=Decimal("0.10123"),
    ask_size=Decimal("0.10123"),
    min_edge_bps=Decimal("10"),
    max_position=Decimal("0.3"),
    price_increment=Decimal("1"),
    market_making_enabled=False,
    sniping_enabled=True,
    check_secs=Decimal("0.005"),
    sniper_edge_bps=Decimal("1.3"),
)

parser = argparse.ArgumentParser(description="Example program with flags.")
parser.add_argument('-c', '--config', type=str, help='Which config to use', required=True)

args = parser.parse_args()

conf = None
if args.config.lower() == "avax":
    conf = avaxConfig
elif args.config.lower() == "eth":
    conf = ethConfig
elif args.config.lower() == "btc":
    conf = btcConfig
else:
    raise SystemExit("Please provide a valid config")

envs = dotenv.dotenv_values()
if envs is None or "key" not in envs or "secret" not in envs:
    raise SystemExit("Please provide API key and secret in .env file")
key = str(envs["key"])
secret = str(envs["secret"])

mainLogger = logging.getLogger("main")
fillLogger = logging.getLogger("fill")
tradeLogger = logging.getLogger("trade")

mainLogger.setLevel(logging.DEBUG)
fillLogger.setLevel(logging.DEBUG)
tradeLogger.setLevel(logging.DEBUG)

mainHandler = logging.FileHandler(args.config.lower() + ".log")
fillsHandler = logging.FileHandler(args.config.lower() + "_fills.log")
tradeHandler = logging.FileHandler(args.config.lower() + "_trades.log")

formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)-5s %(message)s', '%Y-%m-%d %H:%M:%S')
mainHandler.setFormatter(formatter)
fillsHandler.setFormatter(formatter)
emptyFormatter = logging.Formatter('%(message)s')
tradeHandler.setFormatter(emptyFormatter)

mainLogger.addHandler(mainHandler)
fillLogger.addHandler(fillsHandler)
tradeLogger.addHandler(tradeHandler)

# TODO
# ✔️ Add logging and output timestamp
# ✔️ Do websocket ping
# ✔️ Subscribe to fill messages and mainLogger.info out theoretical PnL
# ✔️ Make it hedge if it can do so with no slippage
# ✔️ Make it handle multiple markets
# ✔️ Make it be smart for api keys
# ✔️ Log to files
# ✔️ Print fills to separate file
# Track orders by order IDs so I can understand fills better
# Allow closing position


class TradingBot:
    def __init__(self, client: Client, config: Config):
        self.client = client
        self.last_update = datetime.now()
        self.mark_price = None
        self.current_bid = None
        self.current_ask = None
        self.config = config
        self.total_theoretical_pnl = Decimal("0")
        self.position = {'direction': 'long', 'netQuantity': '0'}
        
        self.order_info_by_client_order_id = {}

        res = self.client.authed_hello()
        mainLogger.info(res.status_code)

    def update_mark_price(self, mark_price: Decimal):
        mainLogger.info("====Mark Price====")
        mainLogger.info(f"Mark price: {mark_price}")
        self.mark_price = mark_price
        self.process()

    def update_top_of_book(self, best_bid: BookLevel, best_ask: BookLevel):
        mainLogger.info("====Top of Book====")
        mainLogger.info(f"Best bid: {best_bid}, best ask: {best_ask}")
        self.best_bid = best_bid
        self.best_ask = best_ask
        self.process()

    def update_position(self, position):
        self.position = position

    def update_trade(self, trade):
        mainLogger.info("====Trade====")
        mainLogger.info(f"Trade: {trade}")
        edge = self.calculate_edge(trade['aggressor_side'], Decimal(trade['price']))
        trade['edge'] = edge
        tradeLogger.info(json.dumps(trade))
        mainLogger.info(json.dumps(trade))

    def calculate_edge(self, side, price):
        if side == "buy":
            edge = self.mark_price - price
        else:
            edge = price - self.mark_price
        return edge

    def report_fill(self, fill):
        mainLogger.info("====Fill====")
        mainLogger.info(f"Fill: {fill}")
        price = Decimal(fill['price'])
        size = Decimal(fill['size'])
        side = fill['side']

        # Print out the edge we got
        edge = self.calculate_edge(side, price)
        theoretical_pnl = size * edge
        self.total_theoretical_pnl += theoretical_pnl

        # calculate edge in basis points
        edge_in_basis_points = edge / self.mark_price * Decimal("10000")

        fillInfo = {'market': self.config.market, 'side': side, 'price': price, 'mark_price': self.mark_price, 'size': size, 'edge': edge, 'edge_in_basis_points': edge_in_basis_points, 'theoretical_pnl': theoretical_pnl, 'total_theoretical_pnl': self.total_theoretical_pnl}
        try:
            original_info = self.order_info_by_client_order_id[fill['clientOrderId']]
            fillInfo.update(original_info)
        except KeyError:
            mainLogger.info(f"Original order info not found for clientOrderId: {fill['clientOrderId']}")

        fillLogger.info(json.dumps(fillInfo))

        mainLogger.info(f"FillInfo: {json.dumps(fillInfo)}")
        

        # Clear current orders to force a redo
        self.current_bid = None
        self.current_ask = None
    
    def process(self):
        diff = datetime.now() - self.last_update
        if diff.total_seconds() < self.config.check_secs:
            # mainLogger.info(f"Not enough time since last update {diff.total_seconds()} < {self.config.check_secs}")
            return
        self.last_update = datetime.now()

        try:
            if self.config.market_making_enabled:
                self.process_market_making()

            if self.config.sniping_enabled:
                self.process_sniper()
        except Exception as e:
            mainLogger.info(f"An error occured when processing: {e}")
            mainLogger.exception("Exception occurred")


    def process_market_making(self):
        mainLogger.info("====Market Making====")
        mainLogger.info(f"Mark price: {self.mark_price}")
        mainLogger.info(f"Best bid: {self.best_bid}")
        mainLogger.info(f"Best ask: {self.best_ask}")
        
        if self.best_bid.size == self.config.bid_size:
            my_bid = self.best_bid.price
        else:
            my_bid = self.best_bid.price + self.config.price_increment

        if self.best_ask.size == self.config.ask_size:
            my_ask = self.best_ask.price
        else:
            my_ask = self.best_ask.price - self.config.price_increment

        mainLogger.info(f"My bid: {my_bid}")
        mainLogger.info(f"My ask: {my_ask}")
        bid_edge_bps = (self.mark_price - my_bid)/self.mark_price * Decimal("10000")
        ask_edge_bps = (my_ask - self.mark_price)/self.mark_price * Decimal("10000")
        mainLogger.info(f"Bid edge bps: {bid_edge_bps}")
        mainLogger.info(f"Ask edge bps: {ask_edge_bps}")

        if bid_edge_bps < self.config.min_edge_bps:
            mainLogger.info(f"Not enough edge for bid {bid_edge_bps} < {self.config.min_edge_bps}")
            my_bid = None
        if ask_edge_bps < self.config.min_edge_bps:
            mainLogger.info(f"Not enough edge for ask {ask_edge_bps} < {self.config.min_edge_bps}")
            my_ask = None

        if not self.position_limits_allow_order("buy"):
            mainLogger.info(f"Position too long {self.position['netQuantity']} > {self.config.max_position}")
            my_bid = None

        if not self.position_limits_allow_order("sell"):
            mainLogger.info(f"Position too short {self.position['netQuantity']} > {self.config.max_position}")
            my_ask = None

        self.place_market_making_orders(my_bid, bid_edge_bps, my_ask, ask_edge_bps)  

    def position_limits_allow_order(self, side):
        if self.position is None:
            return True
        if side == "buy" and self.position['direction'] == "long" and Decimal(self.position['netQuantity']) > self.config.max_position:
            return False
        if side == "sell" and self.position['direction'] == "short" and Decimal(self.position['netQuantity']) > self.config.max_position:
            return False
        return True

    def calculate_sniper_edge_bps(self, position):
        myPosition = Decimal(position['netQuantity'])
        if myPosition < self.config.max_position:
            return self.config.sniper_edge_bps
        
        if self.config.market == "AVAX-USD.P" and myPosition > Decimal(2.5) * self.config.max_position:
            return Decimal("99999")
        
        if myPosition > Decimal(5) * self.config.max_position:
            return Decimal("99999")
        
        return myPosition/self.config.max_position * self.config.sniper_edge_bps


    def process_sniper(self):
        bid_edge_bps = (self.mark_price - self.best_ask.price)/self.mark_price * Decimal("10000")
        ask_edge_bps = (self.best_bid.price - self.mark_price)/self.mark_price * Decimal("10000")

        min_bid_edge_bps = self.config.sniper_edge_bps
        min_ask_edge_bps = self.config.sniper_edge_bps

        if self.position is not None:
            if self.position['direction'] == "long":
                min_ask_edge_bps = Decimal("0")
                min_bid_edge_bps = self.calculate_sniper_edge_bps(self.position)

            else:
                min_bid_edge_bps = Decimal("0")
                min_ask_edge_bps = self.calculate_sniper_edge_bps(self.position)

        mainLogger.info("====Sniping====")
        mainLogger.info(f"Position: {self.position['direction']} {self.position['netQuantity']}, min_bid_edge_bps: {min_bid_edge_bps}, min_ask_edge_bps: {min_ask_edge_bps}")
        mainLogger.info(f"Evaluating sniper, my bid edge bps: {bid_edge_bps}, my ask edge bps: {ask_edge_bps}")

        if bid_edge_bps > min_bid_edge_bps:
            self.place_order(self.config.market, self.best_ask.price, "buy", self.config.bid_size, memo="sniper", expected_edge_bps=bid_edge_bps, time_in_force="IOC")

        if ask_edge_bps > min_ask_edge_bps:
            self.place_order(self.config.market, self.best_bid.price, "sell", self.config.ask_size, memo="sniper", expected_edge_bps=ask_edge_bps, time_in_force="IOC")

    def place_order(self, market, price, side, size, memo, expected_edge_bps, time_in_force="GTC"):
        client_order_id = str(uuid.uuid4())
        
        order_info = {
            'market': market, 
            'price': price,
            'side': side,
            'placed_size': size,
            'memo': memo,
            'expected_edge_bps': expected_edge_bps,
            'time_in_force': time_in_force,
            'client_order_id': client_order_id,
        }

        self.order_info_by_client_order_id[client_order_id] = order_info

        mainLogger.info(f"Placing order: {json.dumps(order_info)}")
        res = self.client.perps.new_order(market, price, side, size, client_order_id=client_order_id, time_in_force=time_in_force)
        mainLogger.info(f"Response: code={res.status_code}, result={res.json()}")

    def place_market_making_orders(self, my_bid: Decimal, bid_edge_bps: Decimal, my_ask: Decimal, ask_edge_bps: Decimal):
        if my_bid == self.current_bid and my_ask == self.current_ask:
            mainLogger.info(f"No change in orders, bid: {my_bid}, ask: {my_ask}")
            return
        
        res = self.client.perps.cancel_orders(market=self.config.market)
        mainLogger.info(f"Cancel order response: {res.status_code}")

        if my_bid is not None:
            self.place_order(self.config.market, my_bid, "buy", self.config.bid_size, memo="market_making", expected_edge_bps=bid_edge_bps)
        self.current_bid = my_bid
        
        if my_ask is not None:
            self.place_order(self.config.market, my_ask, "sell", self.config.ask_size, memo="market_making", expected_edge_bps=ask_edge_bps)
        self.current_ask = my_ask  


client = Client(key, secret, base_url="https://api-sandbox.enclave.market")
bot = TradingBot(client, conf)

last_ping_time = datetime.now()


def generate_signature(api_secret):
    # Current time as a string
    current_time = str(int(time.time()*1000))

    # Message to be hashed
    message = current_time + "enclave_ws_login"

    # Create the HMAC object using the API secret and SHA256
    hmac_obj = hmac.new(api_secret.encode(), message.encode(), hashlib.sha256)

    # Generate the hex representation of the HMAC
    signature = hmac_obj.hexdigest()

    return signature

def send_ping_if_needed(ws):
    global last_ping_time
    diff = datetime.now() - last_ping_time
    if diff.total_seconds() < 15:
        return
    last_ping_time = datetime.now()
    mainLogger.info("Sending ping")
    ws.send(json.dumps({"op":"ping"}))

def on_message(ws, message):
    # mainLogger.info("Received message:")
    

    # Deserialize the message
    data = json.loads(message)


    try:
        if data['type'] == 'update':
            mainLogger.info(f"Received update: {data['channel']}")

            if data['channel'] == 'markPricesPerps':
                # {"type":"update","channel":"markPricesPerps","data":[{"market":"AVAX-USD.P","markPrice":"22.8376378316913383"}]}
                mark_price_info = data['data'][0]
                # mainLogger.info(mark_price_info['market'], mark_price_info['markPrice'])
                bot.update_mark_price(Decimal(mark_price_info['markPrice']))
            elif data['channel'] == 'topOfBooksPerps':
                # {"type":"update","channel":"topOfBooksPerps","data":[{"market":"AVAX-USD.P","bids":[["20.82","130.104"]],"asks":[["24.04","130.104"]],"time":"2023-11-16T16:25:13.482765715Z"}]}
                top_of_book_info = data['data'][0]
                if len(top_of_book_info['bids']) == 0:
                    best_bid = BookLevel(Decimal("0.001"), Decimal("1"))
                else:
                    best_bid = BookLevel(Decimal(top_of_book_info['bids'][0][0]), Decimal(top_of_book_info['bids'][0][1]))

                if len(top_of_book_info['asks']) == 0:
                    best_ask = BookLevel(Decimal("100000"), Decimal("1"))
                else:
                    best_ask = BookLevel(Decimal(top_of_book_info['asks'][0][0]), Decimal(top_of_book_info['asks'][0][1]))

                bot.update_top_of_book(best_bid, best_ask)
            elif data['channel'] == 'fillsPerps':
                bot.report_fill(data['data'][0])
            elif data['channel'] == 'positionsPerps':
                for position in data['data']:
                    if position['market'] == bot.config.market:
                        bot.update_position(position)
            elif data['channel'] == 'tradesPerps':
                for t in data['data']:
                    if t['market'] == bot.config.market:
                        bot.update_trade(t)
            

    except IndexError as e:
        mainLogger.info("An index error occurred XXX:", e)
        mainLogger.info("Data:", data)
        mainLogger.exception(e)
    
    send_ping_if_needed(ws)



def on_error(ws, error):
    mainLogger.info("Error occurred:")
    mainLogger.exception(error)

def on_close(ws, close_status_code, close_msg):
    mainLogger.info("### WebSocket closed ###")

def on_open(ws):
    def run(*args):
        mainLogger.info("Websocket opened")

        subscribe_message = {"op":"subscribe","channel":"markPricesPerps","markets":[bot.config.market]}
        ws.send(json.dumps(subscribe_message))

        subscribe_message = {"op":"subscribe","channel":"topOfBooksPerps","markets":[bot.config.market]}
        ws.send(json.dumps(subscribe_message))

        ws.send(json.dumps({"op":"subscribe","channel":"tradesPerps"}))

        signature = generate_signature(secret)
        current_time = str(int(time.time() * 1000))

        msg = {"op": "login","args": {"key": f"{key}","time": f"{current_time}","sign": f"{signature}"}}
        mainLogger.info(f"Going to send {msg}")
        ws.send(json.dumps(msg))

        subscribe_message = {"op":"subscribe","channel":"fillsPerps","markets":[bot.config.market]}
        ws.send(json.dumps(subscribe_message))

        ws.send(json.dumps({"op":"subscribe","channel":"positionsPerps"}))

    run()

if __name__ == "__main__":
    while True:
        mainLogger.info("Starting websocket")
        ws = websocket.WebSocketApp("wss://api-sandbox.enclave.market/ws",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

        ws.run_forever()



import json
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


from enclave.client import Client

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)-5s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

getcontext().prec = 6

class BookLevel(NamedTuple):
    price: Decimal
    size: Decimal

# TODO
# ✔️ Add logging and output timestamp
# ✔️ Do websocket ping
# ✔️ Subscribe to fill messages and logging.info out theoretical PnL
# - Make it hedge if it can do so with no slippage
# - Make it handle multiple markets
# - Make it be smart for api keys



class TradingBot:
    def __init__(self, key, secret):
        self.client = Client(key, secret, base_url="https://api-sandbox.enclave.market")
        self.last_update = datetime.now()
        self.current_bid = None
        self.current_ask = None

        res = self.client.authed_hello()
        logging.info(res.status_code)

    def update_mark_price(self, mark_price: Decimal):
        self.mark_price = mark_price
        self.process()

    def update_top_of_book(self, best_bid: BookLevel, best_ask: BookLevel):
        self.best_bid = best_bid
        self.best_ask = best_ask
        self.process()

    def report_fill(self, fill):
        logging.info(f"Fill: {fill}")
        price = Decimal(fill['price'])
        size = Decimal(fill['size'])
        side = fill['side']

        # Print out the edge we got
        if side == "buy":
            edge = self.mark_price - price
        else:
            edge = price - self.mark_price
        theoretical_pnl = size * edge

        # calculate edge in basis points
        edge_in_basis_points = edge / self.mark_price * Decimal("10000")

        logging.info(f"Edge: {edge}, Edge in bp: {edge_in_basis_points}, Theoretical PnL: ${theoretical_pnl}")

        # Clear current orders to force a redo
        self.best_bid = None
        self.best_ask = None
    
    def process(self):
        diff = datetime.now() - self.last_update
        if diff.total_seconds() < 5:
            return
        self.last_update = datetime.now()

        my_bid_size = Decimal("17.32")
        my_ask_size = Decimal("17.33")

        logging.info("====Summary====")
        logging.info(f"Mark price: {self.mark_price}")
        logging.info(f"Best bid: {self.best_bid}")
        logging.info(f"Best ask: {self.best_ask}")
        
        
        logging.info(f"comparison {self.best_bid.size} {my_bid_size} {self.best_bid.size == my_bid_size}")
        if self.best_bid.size == my_bid_size:
            my_bid = self.best_bid.price
        else:
            my_bid = self.best_bid.price + Decimal("0.01")

        if self.best_ask.size == my_ask_size:
            my_ask = self.best_ask.price
        else:
            my_ask = self.best_ask.price - Decimal("0.01")

        logging.info(f"My bid: {my_bid}")
        logging.info(f"My ask: {my_ask}")
        bid_edge = self.mark_price - my_bid
        ask_edge = my_ask - self.mark_price
        logging.info(f"Bid edge: {bid_edge}")
        logging.info(f"Ask edge: {ask_edge}")

        min_edge = Decimal(0.05)
    
        if bid_edge < min_edge:
            logging.info(f"Not enough edge for bid {bid_edge} < {min_edge}")
            my_bid = None
        if ask_edge < min_edge:
            logging.info(f"Not enough edge for ask {ask_edge} < {min_edge}")
            my_ask = None
        self.place_orders(my_bid, my_ask)  

        logging.info("====End Summary====")
    
    def place_orders(self, my_bid: Decimal, my_ask: Decimal):
        if my_bid == self.current_bid and my_ask == self.current_ask:
            logging.info("No change in orders, abort")
            return
        
        res = self.client.perps.cancel_orders()
        logging.info(f"Cancel order response: {res.status_code}")

        if my_bid is not None:
            logging.info("Placing bid order")
            res = self.client.perps.new_order("AVAX-USD.P", my_bid, "buy", "17.32")
            logging.info(f"Placed order status code {res.status_code}")
            logging.info(res.json())
            self.current_bid = my_bid
        
        if my_ask is not None:
            logging.info("Placing ask order")
            res = self.client.perps.new_order("AVAX-USD.P", my_ask, "sell", "17.33")
            logging.info(f"Placed order status code {res.status_code}")
            logging.info(res.json())
            self.current_ask = my_ask  


bot = TradingBot("enclaveKeyId_654b8de580e2ec192236593f48b04ed3", "enclaveApiSecret_05b07d2caedb7edebbea5d27e31d9a3c78043a2ef06b736a2b86c56417c33667")

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
    logging.info("Sending ping")
    ws.send(json.dumps({"op":"ping"}))

def on_message(ws, message):
    # logging.info("Received message:")
    # logging.info(message)

    # Deserialize the message
    data = json.loads(message)

    try:
        if data['type'] == 'update':
            if data['channel'] == 'markPricesPerps':
                # {"type":"update","channel":"markPricesPerps","data":[{"market":"AVAX-USD.P","markPrice":"22.8376378316913383"}]}
                mark_price_info = data['data'][0]
                # logging.info(mark_price_info['market'], mark_price_info['markPrice'])
                bot.update_mark_price(Decimal(mark_price_info['markPrice']))
            if data['channel'] == 'topOfBooksPerps':
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
            if data['channel'] == 'fillsPerps':
                bot.report_fill(data['data'][0])
    except IndexError as e:
        logging.info("An index error occurred:", e)
        logging.info("Data:", data)
        traceback.logging.info_exc()
    
    send_ping_if_needed(ws)



def on_error(ws, error):
    logging.info("Error occurred:")
    logging.info(error)

def on_close(ws, close_status_code, close_msg):
    logging.info("### WebSocket closed ###")

def on_open(ws):
    def run(*args):
        logging.info("opened")
        # subscribe_message = {
        #     "op": "subscribe",
        #     "channel": "prices",
        # }
        # ws.send(json.dumps(subscribe_message))

        subscribe_message = {"op":"subscribe","channel":"markPricesPerps","markets":["AVAX-USD.P"]}
        ws.send(json.dumps(subscribe_message))

        subscribe_message = {"op":"subscribe","channel":"topOfBooksPerps","markets":["AVAX-USD.P"]}
        ws.send(json.dumps(subscribe_message))

        signature = generate_signature("enclaveApiSecret_05b07d2caedb7edebbea5d27e31d9a3c78043a2ef06b736a2b86c56417c33667")
        current_time = str(int(time.time() * 1000))
        key_id = "enclaveKeyId_654b8de580e2ec192236593f48b04ed3"

        msg = {"op": "login","args": {"key": f"{key_id}","time": f"{current_time}","sign": f"{signature}"}}
        logging.info(f"Going to send {msg}")
        ws.send(json.dumps(msg))

        subscribe_message = {"op":"subscribe","channel":"fillsPerps","markets":["AVAX-USD.P"]}
        ws.send(json.dumps(subscribe_message))

    run()

def process_data(mark_price, best_bid, best_ask):
    logging.info("Mark price:", mark_price)
    logging.info("Best bid:", best_bid)
    logging.info("Best ask:", best_ask)

if __name__ == "__main__":
    ws = websocket.WebSocketApp("wss://api-sandbox.enclave.market/ws",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()


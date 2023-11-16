import json
import websocket
from decimal import *
from datetime import datetime
from collections import namedtuple
from typing import NamedTuple
import traceback

from enclave.client import Client

getcontext().prec = 6

class BookLevel(NamedTuple):
    price: Decimal
    size: Decimal

class TradingBot:
    def __init__(self, key, secret):
        self.client = Client(key, secret, base_url="https://api-sandbox.enclave.market")
        self.last_update = datetime.now()
        self.current_bid = None
        self.current_ask = None

        res = self.client.authed_hello()
        print(res.status_code)

        # res = self.client.authed_hello()

    def update_mark_price(self, mark_price: Decimal):
        self.mark_price = mark_price
        self.process()

    def update_top_of_book(self, best_bid: BookLevel, best_ask: BookLevel):
        self.best_bid = best_bid
        self.best_ask = best_ask
        self.process()
    
    def process(self):
        diff = datetime.now() - self.last_update
        if diff.total_seconds() < 5:
            return
        self.last_update = datetime.now()

        my_bid_size = Decimal("17.32")
        my_ask_size = Decimal("17.33")

        print("====Summary====")
        print("Mark price:", self.mark_price)
        print("Best bid:", self.best_bid)
        print("Best ask:", self.best_ask)
        
        
        print("comparison",  self.best_bid.size, my_bid_size, self.best_bid.size == my_bid_size)
        if self.best_bid.size == my_bid_size:
            my_bid = self.best_bid.price
        else:
            my_bid = self.best_bid.price + Decimal("0.01")

        if self.best_ask.size == my_ask_size:
            my_ask = self.best_ask.price
        else:
            my_ask = self.best_ask.price - Decimal("0.01")

        print("My bid:", my_bid)
        print("My ask:", my_ask)
        bid_edge = self.mark_price - my_bid
        ask_edge = my_ask - self.mark_price
        print("Bid edge:", bid_edge)
        print("Ask edge:", ask_edge)

        min_edge = Decimal(0.05)
    
        if bid_edge < min_edge:
            print("Not enough edge for bid", bid_edge, "<", min_edge)
            my_bid = None
        if ask_edge < min_edge:
            print("Not enough edge for ask", ask_edge, "<", min_edge)
            my_ask = None
        self.place_orders(my_bid, my_ask)  

        print("====End Summary====")
    
    def place_orders(self, my_bid: Decimal, my_ask: Decimal):
        if my_bid == self.current_bid and my_ask == self.current_ask:
            print("No change in orders, abort")
            return
        
        res = self.client.perps.cancel_orders()
        print("Cancel order response: ", res.status_code)

        if my_bid is not None:
            print("Placing bid order")
            res = self.client.perps.new_order("AVAX-USD.P", my_bid, "buy", "17.32")
            print("Placed order status code", res.status_code)
            print(res.json())
            self.current_bid = my_bid
        
        if my_ask is not None:
            print("Placing ask order")
            res = self.client.perps.new_order("AVAX-USD.P", my_ask, "sell", "17.33")
            print("Placed order status code", res.status_code)
            print(res.json())
            self.current_ask = my_ask  

bot = TradingBot("enclaveKeyId_654b8de580e2ec192236593f48b04ed3", "enclaveApiSecret_05b07d2caedb7edebbea5d27e31d9a3c78043a2ef06b736a2b86c56417c33667")

def on_message(ws, message):
    # print("Received message:")
    # print(message)

    # Deserialize the message
    data = json.loads(message)

    try:
        if data['type'] == 'update':
            if data['channel'] == 'markPricesPerps':
                # {"type":"update","channel":"markPricesPerps","data":[{"market":"AVAX-USD.P","markPrice":"22.8376378316913383"}]}
                mark_price_info = data['data'][0]
                # print market and markPrice on one line
                # print(mark_price_info['market'], mark_price_info['markPrice'])
                bot.update_mark_price(Decimal(mark_price_info['markPrice']))
            if data['channel'] == 'topOfBooksPerps':
                # {"type":"update","channel":"topOfBooksPerps","data":[{"market":"AVAX-USD.P","bids":[["20.82","130.104"]],"asks":[["24.04","130.104"]],"time":"2023-11-16T16:25:13.482765715Z"}]}
                # call bot.update_top_of_book() with best bid and best ask
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
    except IndexError as e:
        print("An index error occurred:", e)
        print("Data:", data)
        traceback.print_exc()



def on_error(ws, error):
    print("Error occurred:")
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### WebSocket closed ###")

def on_open(ws):
    def run(*args):
        print("opened")
        # subscribe_message = {
        #     "op": "subscribe",
        #     "channel": "prices",
        # }
        # ws.send(json.dumps(subscribe_message))

        subscribe_message = {"op":"subscribe","channel":"markPricesPerps","markets":["AVAX-USD.P"]}
        ws.send(json.dumps(subscribe_message))

        subscribe_message = {"op":"subscribe","channel":"topOfBooksPerps","markets":["AVAX-USD.P"]}
        ws.send(json.dumps(subscribe_message))

    run()

def process_data(mark_price, best_bid, best_ask):
    print("Mark price:", mark_price)
    print("Best bid:", best_bid)
    print("Best ask:", best_ask)

if __name__ == "__main__":
    ws = websocket.WebSocketApp("wss://api-sandbox.enclave.market/ws",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()

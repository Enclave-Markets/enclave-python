import simplejson as json
from decimal import Decimal
import argparse

parser = argparse.ArgumentParser(description="Example program with flags.")
parser.add_argument('-c', '--config', type=str, help='Which config to use', required=True)
parser.add_argument('-p', '--price', type=str, help='Current price of token', required=True)

args = parser.parse_args()

# open a file, read each line, and calculate the pnl
def calculate_pnl(filename):
    total_volume = Decimal(0)
    base_quantity = Decimal(0)
    quote_quantity = Decimal(0)
    theo_pnl = Decimal(0)
    num_trades = 0

    with open(filename, 'r') as f:
        for line in f:
            # split on "INFO" and only take characters after INFO
            line = line.split("INFO")[1]
            # read JSON
            obj = json.loads(line)

            num_trades += 1

            size = Decimal(obj['size'])

            if obj['side'] == 'buy':
                base_quantity += size
                quote_quantity -= size * Decimal(obj['price'])
            elif obj['side'] == 'sell':
                base_quantity -= size
                quote_quantity += size * Decimal(obj['price'])
            theo_pnl += Decimal(obj['theoretical_pnl'])
            
            total_volume += size

    print("Number of Trades: {}".format(num_trades))
    print("Total Volume: {}".format(total_volume))
    print("Base Quantity: {}".format(base_quantity))
    print("Quote Quantity: {}".format(quote_quantity))
    print("Current Price: {}".format(args.price))

    value_of_base = base_quantity * Decimal(args.price)
    pnl = quote_quantity + value_of_base
    print("PnL: {}".format(pnl))
    print("Theoretical PnL: {}".format(theo_pnl))

calculate_pnl(args.config + '_fills.log')
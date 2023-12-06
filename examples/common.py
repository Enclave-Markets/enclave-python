# %% [markdown]
# # Common REST API Demo
#
# [Common REST API Docs](https://enclave-markets.notion.site/Common-REST-API-9d546fa6282b4bad87ef43d189b9071b)
#
# ## Getting started
#
# Note that for many of the endpoints such as deposit and withdrawal to work,
# you cannot use the sandbox environment.
#
# ### Auth
#
# Before using, please read the
# [overview docs](https://enclave-markets.notion.site/REST-API-Overview-57966a627e5445bba573fd66475a553d)
# as well as the
# [authentication docs](https://enclave-markets.notion.site/Rest-API-Authentication-3956dcfecbdc48269031cf052926c90d)
# to get an API key with View + Transfer to use the full demo,
# or just make a key with View to ensure no funds are moved.
#
# ### Prepare account
#
# After following the instruction to get an API key and secret,
# for all the endpoints to work as shown, do the following:
#
# 1.  provision a deposit address for AVAX
# 2.  deposit (not from a smart wallet!) some AVAX to the address
# 3.  add a withdrawal address to your address book
#
# Now you're all set :)
#

# %% [markdown]
# ## Setup
#
# Install dependencies.

# %% [markdown]
# ### Janky fix import
#
# And add the enclave module's path to the system path so we can import the local module in jupyter.
# Alternatively in VSCode you can follow [this tutorial](https://stackoverflow.com/a/73954768),
# or from the command line generally [this tutorial](https://stackoverflow.com/a/65182353).
#
# If you follow the above, feel free to remove the next cell.

# %%
import os
import sys

module_path = os.path.abspath(os.path.join(".."))
if module_path not in sys.path:
    sys.path.append(module_path)

# %% [markdown]
# ### Dependencies
#
# Continue installing and importing dependencies normally.

# %%
# %pip install requests
import enclave
import enclave.models

# %% [markdown]
# ## Environment variables
#
# Set the following variables for auth and to set the base url.

# change to the env of your choice that matches the API keys: PROD, DEV, SANDBOX etc.
BASE_URL = enclave.models.DEV

### three ways to get API key and secret, tried in order.

# 1. as hardcoded strings
API_KEY: str = ""
API_SECRET: str = ""

# 2. as environment variables
if not (all([API_KEY, API_SECRET])):
    # try:
    env_key, env_secret = os.getenv("ENCLAVE_API_KEY"), os.getenv("ENCLAVE_API_SECRET")
    API_KEY = env_key if env_key else ""
    API_SECRET = env_secret if env_secret else ""

# 3. from a .env file with `key` and `secret` set.
if not (all([API_KEY, API_SECRET])):
    import dotenv

    envs = dotenv.dotenv_values("dev.env")
    if envs and "key" in envs and "secret" in envs:
        API_KEY, API_SECRET = str(envs["key"]), str(envs["secret"])

if not (all([API_KEY, API_SECRET])):
    raise ValueError("Please provide API_KEY and API_SECRET")

# %% [markdown]
# ## Create client
#
# Create a client with the variables and get authed hello.
#
# If you get anything other than a 200 status code and the hello message with `"success": True`
# and your Enclave Account ID, then there is an issue -- <br>
# either with auth or connection permissions to the URL.

# %%
from enclave.client import Client

client = Client(api_key=API_KEY, api_secret=API_SECRET, base_url=BASE_URL)

hello_res = client.authed_hello()
if 200 <= hello_res.status_code < 300:
    print(hello_json := hello_res.json())
    assert hello_json["success"] == True
else:
    print(f"Could not connect:\n{hello_res.text=}")

# %% [markdown]
# ## Common API
#
# Demonstrate common API endpoints.
# %% [markdown]
# ### Market info
# %%
markets = client.get_markets().json()
print("available markets")
import json

print(json.dumps(markets["result"], indent=2))


# %% [markdown]
# ### Wallet
#
# Demonstrate wallet endpoints such as getting balances, deposit addresses, and withdrawal addresses.
# %%
balances = client.get_balances().json()
print("available balances")
print(json.dumps(balances["result"], indent=2))

# %% [markdown]
# Per coin either manually or with get_balance
# %%
print(f'AVAX balance:\n{[x for x in balances["result"] if x["coin"] == "AVAX"]}')

balance_avax = client.get_balance("AVAX").json()
print(f'\n\nAVAX balance:\n{balance_avax["result"]=}')


# %% [markdown]
# Deposits and deposit addresses
# %%
deposit_addrs = client.get_deposit_addresses(["AVAX"]).json()
print(f"provisioned addresses:\n{json.dumps(deposit_addrs['result'], indent=2)}")

# %% [markdown]
# Provision a new address and see it come up
# %%
provision_res = client.provision_address("AVAX").json()
print(f"provisioned address:\n{json.dumps(provision_res['result'], indent=2)}")

new_deposit_addrs = client.get_deposit_addresses(["AVAX"]).json()

# there is one more address now
assert len(new_deposit_addrs["result"]) > len(deposit_addrs["result"])

from io import StringIO

# %%
# %pip install pandas -q
import pandas as pd

deposits_csv = client.get_deposits_csv().text
print(f"raw csv: {deposits_csv=}")

x = pd.read_csv(StringIO(deposits_csv))
print(x)

# %% [markdown]
# Address book and withdrawals
#
# Get one of the addresses and withdraw to it
# %%
# no current withdrawals
withdrawals = client.get_withdrawals().json()
print(f"withdrawals: {withdrawals=}")

# %%
addr_book = client.get_address_book().json()
print(f"address book: {addr_book}")

withdrawal_addr = addr_book["result"]["addressBook"][0]["withdrawalAddress"]
print(f"\n a {withdrawal_addr=}")

# %% [markdown]
# Withdraw to it
# %%
import decimal
import time

WITHDRAW_AMOUNT = decimal.Decimal(0.01)

withdrawal_res = client.withdraw(withdrawal_addr, WITHDRAW_AMOUNT, str(int(time.time())), "AVAX").json()
print(f"withdrawal: {withdrawal_res}")


# %%
# there is a withdrawal now
withdrawals = client.get_withdrawals().json()
print(f"withdrawals: {withdrawals=}")
# get by txid
txid_withdrawal = withdrawals["result"][0]["txid"]
withdrawal_res = client.get_withdrawal(txid_withdrawal).json()
print(f"\nwithdrawal by txid: {withdrawal_res}")

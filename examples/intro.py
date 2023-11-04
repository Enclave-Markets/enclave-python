# %%
"""Getting started with the Enclave Python SDK
Run from base folder using `python -m examples.intro`"""
from enclave.client import Client

if __name__ == "__main__":
    c = Client.from_api_file("/Users/ben.zuckier/Documents/enclave-python/bot.env", "https://api-dev.enclavemarket.dev")
    res = c.base_client._request("GET", "/hello")
    if res.status_code == 200:
        print(res.json())
    else:
        print(res.text)

    res = c.base_client._request("GET", "/authedHello")
    if res.status_code == 200:
        print(res.json())
    else:
        print(res.text)

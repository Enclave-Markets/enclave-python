# %%
"""Getting started with the Enclave Python SDK
Run from base folder using `python -m examples.intro`"""
import dotenv

import enclave.models
from enclave.client import Client

if __name__ == "__main__":

    def hello_requests(c: Client) -> None:
        """Uses a provided client to make some requests to the Enclave API."""
        res = c.bc.get("/hello")  # would break execution if throws error
        if res.ok:
            print(res.json())
        else:
            print(res.text)

        res = c.authed_hello()
        if res.ok:
            print(res.json())
        else:
            print(res.text)

    # First way to make a client: from key and secret
    # Load environment variables from .env file
    # .env file should contain key=enclaveKeyId_... on one line and secret=enclaveApiSecret_... on another
    envs = dotenv.dotenv_values()
    if envs and "key" in envs and "secret" in envs:
        api_key, api_secret = str(envs["key"]), str(envs["secret"])
    else:
        api_key, api_secret = input("Provide API key: "), input("Provide API secret: ")  # or hardcode here

    c0 = Client(api_key, api_secret, enclave.models.DEV)
    hello_requests(c0)

    # Second way to make a client: from an API file
    PATH_TO_ENV_FILE = input(
        "Provide full path to API file containing key and secret separated by newline: "
    )  # or hardcode here
    c1 = Client.from_api_file(PATH_TO_ENV_FILE, enclave.models.DEV)
    hello_requests(c1)

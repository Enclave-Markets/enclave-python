# Enclave Python

<p align="center">
    <a href="https://github.com/Enclave-Markets/enclave-python" alt="enclave python">
        <img src="https://edent.github.io/SuperTinyIcons/images/svg/github.svg" width="50" /></a>
    <a href="https://pypi.org/project/enclave/">
        <img src="https://pypi.org/static/images/logo-small.2a411bc6.svg" width="50"/></a>
    <a href="https://twitter.com/enclavemarkets" alt="Enclave Twitter">
        <img src="https://edent.github.io/SuperTinyIcons/images/svg/x.svg" width="50"/></a>
    <a href="https://www.enclave.market/" alt="Enclave Market">
        <img src="https://pbs.twimg.com/profile_images/1650572649284931585/rbv_Z4Lr_400x400.jpg" width="50"/></a>
        
</p>

This is the official Python SDK for
[Enclave Markets](https://enclave.market/).

It provides a simple interface for interacting with the
[Enclave API](https://docs.enclave.market/).

## Installation

```bash
pip install enclave
```

## Usage

```python
from enclave.client import Client
import enclave.models

client = Client("", "", enclave.models.PROD)
print(client.wait_until_ready()) # should print True
```

### Perps Order

```python
buy_order = client.perps.add_order(
    "BTC-USD.P",
    enclave.models.BUY,
    Decimal(42_000),
    Decimal(0.1),
    order_type=enclave.models.LIMIT,
)
```

## Examples

See the [examples](examples) directory for more examples.

Rest API examples can be found in [intro.py](examples/intro.py).
Run from the root directory with `python -m examples.intro`.

Websocket API examples can be found in [wsintro.py](examples/wsintro.py).
Run from the root directory with `python -m examples.wsintro`.

## Support

Supports Python 3.8+.

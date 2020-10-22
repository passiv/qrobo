# qrobo

This is a simple wrapper for the Questrade API and a script for implementing a balanced fund on top of your brokerage account.

## Disclaimer

No part of this project should be taken as investment advice. This is for educational purposes only. Code has not been thoroughly tested and may have bugs. Use at your own risk. Author accepts no liability for any way in which this code is used.

## Usage

Clone the repo:

```bash
git clone https://github.com/passiv/qrobo.git
```

Install the dependencies into a Python virtualenv:

```bash
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

Create a personal app under your Questrade account and generate a token. Input that token into qrobo like so:

```bash
./wrapper.py -t "[my_secret_token]"
```

Edit the `target_portfolio` and `target_account` in `balance.py` to reflect your desired portfolio and target account. For example:

```python
target_portfolio = { 
    'VXC.TO': 0.50,
    'VCN.TO': 0.25,
    'VAB.TO': 0.25,
}

target_account = 'TFSA'
```

Run the balance calculation:

```bash
./balance.py
```

If there are trades to make, you'll see output like this:

```
To rebalance your TFSA, perform the following trades:
 - SELL 12 units of VXC.TO
 - BUY 2 units of VCN.TO
 - BUY 11 units of VAB.TO
```

Now just go and make those trades.

## Things to note

* All calculations are performed in CAD.
* There is no support for USD or USD-denominated securities...roll your own Forex. 
* Target assets are calculated using a simple equity split and the market ask price. This is not appropriate in all cases, since the price you pay/receive will depend on whether you are buying or selling, the liquidity of the market, etc.
* USD and CAD are treated in equivalent CAD for the calculation purposes, not including Forex costs.
* This is really just a prototype. Please be careful if you actually use it.


#!/usr/bin/env python

from wrapper import *

# couch potato assertive model portfolio
target_portfolio = {
    'VXC.TO': 0.50,
    'VCN.TO': 0.25,
    'VAB.TO': 0.25,
}

target_account = 'RRSP'

q = QuestradeWrapper()

# let's balance my account
accounts = q.accounts()
for account in accounts:
    if account.type == target_account:
        break

# get the total equity in my account
balances = q.accounts_balances(account)
for balance in balances:
    if balance.currency == 'CAD':
        break
total_equity = balance.totalEquity

# get symbol information for target assets
symbols = q.symbols(target_portfolio.keys())

# get quotes for target assets
quotes = q.markets_quotes(symbols)

# calculate target equity by asset
target_equity = {symbol:total_equity * target_portfolio[symbol] for symbol in target_portfolio}

# calculate target units by asset
target_units = {quote.symbol:target_equity[quote.symbol] // quote.askPrice for quote in quotes}

# get current positions in my account
positions = q.accounts_positions(account)

# calculate trades
trades = {position.symbol:target_units[position.symbol] - position.openQuantity for position in positions}

# print results
print()
if all([t == 0 for t in trades.values()]):
    print('Congrats, you are already perfectly balanced!')
else:
    print('To rebalance your %s, perform the following trades:' % account.type)
    for symbol,units in sorted(trades.items(), key=lambda x: x[1]):
        if units < 0:
            print(' - SELL %d units of %s' % (abs(units), symbol))
        elif units == 0:
            pass
        else:
            print(' - BUY %d units of %s' % (units, symbol))


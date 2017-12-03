#!/usr/bin/env python3

import gdax
import argparse
import sys
from coinmarketcap import Market

parser = argparse.ArgumentParser(description='Buy coins!')
parser.add_argument('--mode',
                    help='mode (deposit or buy)', required=True)
parser.add_argument('--amount', type=float, help='amount to deposit')
parser.add_argument('--key', help='API key', required=True)
parser.add_argument('--b64secret', help='API secret', required=True)
parser.add_argument('--passphrase', help='API passphrase', required=True)
parser.add_argument('--api-url', help='API URL',
                    default='https://api.gdax.com')
parser.add_argument('--payment-method-id',
                    help='Payment method ID for USD deposit')
parser.add_argument('--btc-addr', help='BTC withdrawal address')
parser.add_argument('--eth-addr', help='ETH withdrawal address')
parser.add_argument('--ltc-addr', help='LTC withdrawal address')

args = parser.parse_args()

coins = {
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum',
    'LTC': 'Litecoin',
}
minimum_order_size = {
    'BTC': 0.0001,
    'ETH': 0.001,
    'LTC': 0.01,
}

client = gdax.AuthenticatedClient(args.key, args.b64secret, args.passphrase,
                                  args.api_url)


def get_weights():
    coinmarketcap = Market()

    market_cap = {}
    for c in coins:
        ticker = coinmarketcap.ticker(currency=coins[c])
        market_cap[c] = float(ticker[0]['market_cap_usd'])

    total_market_cap = sum(market_cap.values())

    weights = {}
    for c in coins:
        weights[c] = market_cap[c] / total_market_cap
    print('Coin weights:')
    for w in weights:
        print('  {0}: {1:.4f}'.format(w, weights[w]))
    print()
    return weights


def deposit():
    if args.amount is None:
        print('Please specify deposit amount with `--amount`')
        sys.exit(1)
    if args.payment_method_id is None:
        print('Please provide a bank ID with `--payment-method-id`')
        sys.exit(1)
    print('Performing deposit, amount={} USD'.format(args.amount))
    result = client.deposit(payment_method_id=args.payment_method_id,
                            amount=args.amount,
                            currency='USD')
    print(result)


def get_balance_for(accounts, coin):
    for a in accounts:
        if a['currency'] == coin:
            return float(a['balance'])
    return 0


def get_prices():
    prices = {}
    for c in coins:
        ticker = client.get_product_ticker(product_id=c + '-USD')
        prices[c] = float(ticker['price'])
    return prices


def get_usd_balances(accounts, prices):
    balances = {}
    for a in accounts:
        if a['currency'] == 'USD':
            balances['USD'] = float(a['balance'])
        elif a['currency'] in coins:
            balances[a['currency']] = \
                float(a['balance']) * prices[a['currency']]
    for c in coins:
        if c not in balances:
            balances[c] = 0
    return balances


def get_account(accounts, currency):
    for a in accounts:
        if a['currency'] == currency:
            return a

def set_buy_order(coin, price, size):
    order = client.buy(
        price='{0:.2f}'.format(price),
        size='{0:.8f}'.format(size),
        type='limit',
        product_id=coin + '-USD',
    )
    print('order={}'.format(order))
    return order


def place_buy_orders(balance_difference_usd, coin, price):
    if balance_difference_usd <= 0.1:
        print('Difference for {} is <= 0.1, skipping'.format(coin))
        return

    remaining_usd = balance_difference_usd
    # If the size is <= minimum * 5, set a single buy order, because otherwise
    # it will get rejected
    if remaining_usd / price <= minimum_order_size[coin] * 5:
        discount = 0.995
        amount = remaining_usd
        discounted_price = price * discount
        size = amount / (discounted_price)
        set_buy_order(coin, discounted_price, size)
    else:
        # Set 5 buy orders, in 1% discount increments, starting from 5.5% off
        amount = remaining_usd / 5.0
        discount = 0.945
        for i in range(0, 5):
            discount = discount + 0.01
            discounted_price = price * discount
            size = amount / (discounted_price)
            set_buy_order(coin, discounted_price, size)
            if remaining_usd <= 0.01:
                break


def start_buy_orders(accounts, prices, usd_balances):
    weights = get_weights()

    # Determine amount of each coin, in USD, to buy
    usd_balance_sum = sum(usd_balances.values())
    print('usd_balance_sum={}'.format(usd_balance_sum))

    target_amount_usd = {}
    for c in coins:
        target_amount_usd[c] = usd_balance_sum * weights[c]
    print('target_amount_usd={}'.format(target_amount_usd))

    balance_differences_usd = {}
    for c in coins:
        balance_differences_usd[c] = target_amount_usd[c] - usd_balances[c]
    print('balance_differences_usd={}'.format(balance_differences_usd))

    for c in coins:
        place_buy_orders(balance_differences_usd[c], c, prices[c])


def withdraw(accounts):
    # Check that we've got addresses
    if args.btc_addr is None:
        print('No BTC withdraw address specified with `--btc-addr`')
    if args.eth_addr is None:
        print('No ETH withdraw address specified with `--eth-addr`')
    if args.ltc_addr is None:
        print('No LTC withdraw address specified with `--ltc-addr`')

    # BTC
    btc_account = get_account(accounts, 'BTC')
    if float(btc_account['balance']) < 0.01:
        print('BTC balance only {}, not withdrawing'.format(
            btc_account['balance']))
    else:
        transaction = client.crypto_withdraw(
            amount=btc_account['balance'],
            currency='BTC',
            crypto_address=args.btc_addr
        )
        print('transaction={}'.format(transaction))

    # ETH
    eth_account = get_account(accounts, 'ETH')
    if float(eth_account['balance']) < 0.01:
        print('ETH balance only {}, not withdrawing'.format(
            eth_account['balance']))
    else:
        transaction = client.crypto_withdraw(
            amount=eth_account['balance'],
            currency='ETH',
            crypto_address=args.eth_addr
        )
        print('transaction={}'.format(transaction))

    # LTC
    ltc_account = get_account(accounts, 'LTC')
    if float(ltc_account['balance']) < 0.01:
        print('LTC balance only {}, not withdrawing'.format(
            ltc_account['balance']))
    else:
        transaction = client.crypto_withdraw(
            amount=ltc_account['balance'],
            currency='LTC',
            crypto_address=args.ltc_addr
        )
        print('transaction={}'.format(transaction))


def buy():
    print('Starting buy and (maybe) withdrawal')
    print('First, cancelling orders')
    for c in coins:
        client.cancel_all(product=c + '-USD')
    # Check if there's any USD available to execute a buy
    accounts = client.get_accounts()
    prices = get_prices()
    print('accounts={}'.format(accounts))
    print('prices={}'.format(prices))

    usd_balances = get_usd_balances(accounts, prices)
    print('usd_balances={}'.format(usd_balances))

    if usd_balances['USD'] > 100:
        print('USD balance above $100, buying more')
        start_buy_orders(accounts, prices, usd_balances)
    else:
        print('Only {} USD balance remaining, withdrawing'
              ' coins without buying'.format(usd_balances['USD']))
        withdraw(accounts)


if args.mode == 'deposit':
    deposit()
elif args.mode == 'buy':
    buy()

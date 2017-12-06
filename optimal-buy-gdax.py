#!/usr/bin/env python3

import gdax
import argparse
import sys
import math
from coinmarketcap import Market

parser = argparse.ArgumentParser(description='Buy coins!')
parser.add_argument('--mode',
                    help='mode (deposit or buy)', required=True)
parser.add_argument('--amount', type=float, help='amount to deposit')
parser.add_argument('--key', help='API key', required=True)
parser.add_argument('--b64secret', help='API secret', required=True)
parser.add_argument('--passphrase', help='API passphrase', required=True)
parser.add_argument('--api-url',
                    help='API URL (default: https://api.gdax.com)',
                    default='https://api.gdax.com')
parser.add_argument('--payment-method-id',
                    help='Payment method ID for fiat deposits')
parser.add_argument('--btc-addr', help='BTC withdrawal address')
parser.add_argument('--eth-addr', help='ETH withdrawal address')
parser.add_argument('--ltc-addr', help='LTC withdrawal address')
parser.add_argument('--starting-discount', type=float,
                    help='starting discount (default: 0.005)', default=0.005)
parser.add_argument('--discount-step', type=float,
                    help='discount step between orders (default: 0.01)',
                    default=0.01)
parser.add_argument('--order-count', type=float,
                    help='number of orders (default: 5)', default=5)
parser.add_argument('--fiat-currency', help='Fiat currency (default: USD)',
                    default='USD')
parser.add_argument('--withdrawal-amount', help='withdraw when fiat balance'
                    'drops below this amount (default: 100)',
                    type=float, default=100)

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
    print('Performing deposit, amount={} {}'.format(args.amount,
                                                    args.fiat_currency))
    result = client.deposit(payment_method_id=args.payment_method_id,
                            amount=args.amount,
                            currency=args.fiat_currency)
    print(result)


def get_balance_for(accounts, coin):
    for a in accounts:
        if a['currency'] == coin:
            return float(a['balance'])
    return 0


def get_products():
    products = client.get_products()
    for p in products:
        if p['base_currency'] in coins \
                and p['quote_currency'] == args.fiat_currency:
            minimum_order_size[p['base_currency']] = float(p['base_min_size'])
    return products


def get_prices():
    prices = {}
    for c in coins:
        ticker = client.get_product_ticker(
            product_id='{}-{}'.format(c, args.fiat_currency))
        prices[c] = float(ticker['price'])
    return prices


def get_fiat_balances(accounts, prices):
    balances = {}
    for a in accounts:
        if a['currency'] == args.fiat_currency:
            balances[args.fiat_currency] = float(a['balance'])
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
    print('placing order coin={0} price={1:.2f} size={2:.8f}'.format(
        coin, price, size))
    order = client.buy(
        price='{0:.2f}'.format(price),
        size='{0:.8f}'.format(size),
        type='limit',
        product_id='{}-{}'.format(coin, args.fiat_currency),
        post_only='true',
    )
    print('order={}'.format(order))
    return order


def place_buy_orders(balance_difference_fiat, coin, price):
    # If the size is <= minimum * 5, set a single buy order, because otherwise
    # it will get rejected
    if balance_difference_fiat / price <= \
            minimum_order_size[coin] * args.order_count:
        discount = 1 - args.starting_discount
        amount = balance_difference_fiat
        discounted_price = price * discount
        size = amount / discounted_price
        set_buy_order(coin, discounted_price, size)
    else:
        # Set 5 buy orders, in 1% discount increments, starting from 0.5% off
        amount = math.floor(
            100 * balance_difference_fiat / args.order_count) / 100.0
        discount = 1 - args.starting_discount
        for i in range(0, 5):
            discounted_price = price * discount
            size = amount / discounted_price
            set_buy_order(coin, discounted_price, size)
            discount = discount - args.discount_step


def start_buy_orders(accounts, prices, fiat_balances):
    weights = get_weights()

    # Determine amount of each coin, in fiat, to buy
    fiat_balance_sum = sum(fiat_balances.values())
    print('fiat_balance_sum={}'.format(fiat_balance_sum))

    target_amount_fiat = {}
    for c in coins:
        target_amount_fiat[c] = fiat_balance_sum * weights[c]
    print('target_amount_fiat={}'.format(target_amount_fiat))

    balance_differences_fiat = {}
    for c in coins:
        balance_differences_fiat[c] = math.floor(
            100 * (target_amount_fiat[c] - fiat_balances[c])) / 100.0
    print('balance_differences_fiat={}'.format(balance_differences_fiat))

    for c in coins:
        place_buy_orders(balance_differences_fiat[c], c, prices[c])


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
    if float(btc_account['balance']) < minimum_order_size['BTC']:
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
    if float(eth_account['balance']) < minimum_order_size['ETH']:
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
    if float(ltc_account['balance']) < minimum_order_size['LTC']:
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
    products = get_products()
    print('products={}'.format(products))
    for c in coins:
        client.cancel_all(product='{}-{}'.format(c, args.fiat_currency))
    # Check if there's any fiat available to execute a buy
    accounts = client.get_accounts()
    prices = get_prices()
    print('accounts={}'.format(accounts))
    print('prices={}'.format(prices))

    fiat_balances = get_fiat_balances(accounts, prices)
    print('fiat_balances={}'.format(fiat_balances))

    if fiat_balances[args.fiat_currency] > args.withdrawal_amount:
        print('fiat balance above 100 {}, buying more'.format(
            args.fiat_currency))
        start_buy_orders(accounts, prices, fiat_balances)
    else:
        print('Only {} {} balance remaining, withdrawing'
              ' coins without buying'.format(
                  fiat_balances[args.fiat_currency], args.fiat_currency))
        withdraw(accounts)


if args.mode == 'deposit':
    deposit()
elif args.mode == 'buy':
    buy()

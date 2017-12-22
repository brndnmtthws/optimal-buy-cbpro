# optimal-buy-gdax

Scheduled buying of BTC, ETH, and LTC from GDAX optimally! Be your own index/hedge fund, and stop paying those greasy management fees.

![crypto](crypto.gif)

# What is this?

This is a Python script you can use to automatically buy Bitcoin, Ethereum,
and Litecoin using the GDAX API. It buys these 3 currencies, weighted by market
cap (as reported by [coinmarketcap.com](https://coinmarketcap.com/)), using a form of [dollar cost averaging](https://www.bogleheads.org/wiki/Dollar_cost_averaging). according
to the following logic:

1. Check current balances of fiat (USD by default), BTC, ETH, and LTC
1. If the fiat balance is above $100, buy BTC, ETH, and LTC weighted by market cap, as follows:
    * If there's enough fiat available, place 5 discounted limit orders at the current price
    minus 0.5% up to 4.5%, each order with 1/5th of the remaining amount to buy for each coin
    (see "[Details on the orders placed](#details-on-the-orders-placed)", below)
    * If there isn't enough USD available, place 1 buy order at 0.5% off the current price (see "[Order Minimums](https://support.gdax.com/customer/portal/articles/2725970-trading-rules)")
1. If the fiat account balance is below $100 (or whatever you specify),
withdraw coins to desired addresses

You can also use the same script to schedule deposits from your bank account
periodically, such as when you're paid.

Orders, deposits, and withdrawals are tracked in a SQLite DB, and the withdrawn
balances are added to the balances on GDAX to make sure the weights are
maintained over time. The SQLite DB can be swapped out for any DB that
SQLAlchemy supports.

Ideally, this script would help to make sure that when we dip—

![dip](buy-the-dip.gif)

**we buy**.

# USE AT OWN RISK

Duh. Not my fault if you lose everything.

Unless you place **absolute trust** in me, some guy from the Internet, I
suggest you clone the repo and build your own container to protect yourself
from any sort of funny business.

# How do I use it?

1. Get yourself a hardware wallet, such as a
[Ledger](https://www.ledgerwallet.com/) or [TREZOR](https://trezor.io/).
1. Set up a GDAX account, and link your bank account
1. Create the necessary API credentials for GDAX, with permissions to
manage funds, withdraw without 2FA, and trade
1. Determine the payment_method_id value by using the
[GDAX API](https://docs.gdax.com/#payment-methods) (you can use your browser's
developer toolbar,
[here's a quick video showing how](https://youtu.be/NmSEBGbn7Mc))
1. Get a machine somewhere (GCE, EC2, Digital Ocean) with Docker and systemd
1. Copy systemd files over:

        $ sudo cp optimal-buy-gdax-*.{service,timer} /etc/systemd/system
1. Edit [`/etc/systemd/system/optimal-buy-gdax-buy.service`](optimal-buy-gdax-buy.service),
[`/etc/systemd/system/optimal-buy-gdax-buy.timer`](optimal-buy-gdax-buy.timer),
[`/etc/systemd/system/optimal-buy-gdax-deposit.service`](optimal-buy-gdax-deposit.service), and
[`/etc/systemd/system/optimal-buy-gdax-deposit.timer`](optimal-buy-gdax-deposit.timer) to your liking. Make sure you:

    * Change the BTC, ETH, and LTC withdrawal addresses to deposit the coins into
    your wallet (use a Ledger or TREZOR)
    * Pop in the correct API keys
    * Check the deposit amount (start with something small, like $150, to make
    sure it actually works first)
    * Check the timer dates (it would be sensible to change the hh:mm so your
    script doesn't run the same time as everyone else's), make sure the deposit
    timer fires according to your deposit schedule (keeping in mind that ACH
    takes 2-5 business days to clear, typically)
    * Consider specifying your external balances in order to accurately
    calculate the weights and amounts to purchase

1. Enable the systemd units:

        $ sudo systemctl enable optimal-buy-gdax-buy.service
        $ sudo systemctl enable optimal-buy-gdax-buy.timer
        $ sudo systemctl enable optimal-buy-gdax-deposit.service
        $ sudo systemctl enable optimal-buy-gdax-deposit.timer

1. Start the systemd timers:
        $ sudo systemctl start optimal-buy-gdax-buy.timer
        $ sudo systemctl start optimal-buy-gdax-deposit.timer

1. Enjoy!

# Configuration

    usage: optimal-buy-gdax.py [-h] --mode MODE [--amount AMOUNT] --key KEY
                               --b64secret B64SECRET --passphrase PASSPHRASE
                               [--api-url API_URL]
                               [--payment-method-id PAYMENT_METHOD_ID]
                               [--starting-discount STARTING_DISCOUNT]
                               [--discount-step DISCOUNT_STEP]
                               [--order-count ORDER_COUNT]
                               [--fiat-currency FIAT_CURRENCY]
                               [--withdrawal-amount WITHDRAWAL_AMOUNT]
                               [--db-engine DB_ENGINE] [--max-retries MAX_RETRIES]
                               [--coins COINS]

    Buy coins!

    optional arguments:
      -h, --help            show this help message and exit
      --mode MODE           mode (deposit or buy)
      --amount AMOUNT       amount to deposit
      --key KEY             API key
      --b64secret B64SECRET
                            API secret
      --passphrase PASSPHRASE
                            API passphrase
      --api-url API_URL     API URL (default: https://api.gdax.com)
      --payment-method-id PAYMENT_METHOD_ID
                            Payment method ID for fiat deposits
      --starting-discount STARTING_DISCOUNT
                            starting discount (default: 0.005)
      --discount-step DISCOUNT_STEP
                            discount step between orders (default: 0.01)
      --order-count ORDER_COUNT
                            number of orders (default: 5)
      --fiat-currency FIAT_CURRENCY
                            Fiat currency (default: USD)
      --withdrawal-amount WITHDRAWAL_AMOUNT
                            withdraw when fiat balancedrops below this amount
                            (default: 10)
      --db-engine DB_ENGINE
                            SQLAlchemy DB engine (default:
                            sqlite:///gdax_history.db)
      --max-retries MAX_RETRIES
                            Maximum number of times to retry if there are any
                            failures, such as API issues (default: 3)
      --coins COINS         Coins to trade, minimum trade size, withdrawal
                            addresses and external balances. Accepts a JSON
                            string.

    Default coins are as follows:
    {
      "BTC":{
        "name":"Bitcoin",
        "withdrawal_address":null,
        "external_balance":0
      },
      "ETH":{
        "name":"Ethereum",
        "withdrawal_address":null,
        "external_balance":0
      },
      "LTC":{
        "name":"Litecoin",
        "withdrawal_address":null,
        "external_balance":0
      }
    }

# Details on the orders placed

By default, there are 5 orders placed (for each currency) in steps of 1%,
starting at a 0.5% discount from the current price. To illustrate, if the
current price was $100 (per LTC, let's say), and you had $100 to buy,
the orders would look like this:

Order | Size      | Price
------|-----------|------
1 | 0.2010 LTC | $99.5
2 | 0.2030 LTC | $98.5
3 | 0.2051 LTC | $97.5
4 | 0.2072 LTC | $96.5
5 | 0.2094 LTC | $95.5

Furthermore, the amount of each currency to buy will be based on the current
market cap weighting of each coin. For example, at the time of writing the
weights are:

Coin | Market Cap (USD) | Weight
-----|------------------|-------
BTC | $195,824,365,435 | 0.791
ETH | $46,080,472,372 | 0.186
LTC | $5,592,776,540 | 0.023

So if your USD account had $1000 to invest, the amount invested in each would
become:

Coin | Weight | Amount Invested
-----|--------|----------------
BTC | 0.791 | $791
ETH | 0.186 | $186
LTC | 0.023 | $23

# Caveats/limitations

* If you try to trade manually or using some other bot at the same time,
you're probably going to have a bad time
* You might have a few dollars (<$10, you can change this with
`--withdrawal-amount`) sitting in your account at all times,
even when all orders have been filled because it's not always possible to
fill all orders and there may be small rounding errors (on the order of cents)
* It makes a best effort with minimal complexity to invest all of your fiat,
but it may not be possible to fill all orders right away
* It may take a few days for the market to drop enough for the buys to fill
* If the market experiences a significant bull run, your orders won't be
filled, but it will reset every 24h (using the default buy timer)

# Tip jar

If you got some value out of this, please send some coins my way so I can
retire from my day job:

* BTC: 3EEAE1oKEMnmHGU5Qxibv9mBQyNnes8j8N
* LTC: 3MxmLzTf4sPsFBGYUnX9MMMbTMeaUSox46

#!/usr/bin/env python3
import pytest
import math
import json
import cbpro

from optimal_buy_cbpro import optimal_buy_cbpro


@pytest.fixture
def coins():
    coins = """
    {
      "BTC":{
        "name":"Bitcoin",
        "withdrawal_address":null,
        "external_balance":0
      }
    }"""
    return json.loads(coins)


@pytest.fixture
def args():
    class Args:
        order_count = 5
        starting_discount = 0.005
        discount_step = 0.001
    return Args()


def test_get_weights(coins):
    weights = optimal_buy_cbpro.get_weights(coins, 'USD')
    assert 'BTC' in weights
    assert weights['BTC'] == 1


def test_get_products(coins):
    cbpro_client = cbpro.PublicClient()
    products = optimal_buy_cbpro.get_products(cbpro_client, coins, 'USD')
    assert len(products) >= 0
    assert 'BTC' in [product['base_currency'] for product in products]


def test_get_prices(coins):
    cbpro_client = cbpro.PublicClient()
    prices = optimal_buy_cbpro.get_prices(cbpro_client, coins, 'USD')
    assert len(prices) >= 0
    assert 'BTC' in prices
    assert prices['BTC'] >= 1


def test_generate_orders(coins, args):
    orders = optimal_buy_cbpro.generate_buy_orders(coins,
                                                   'BTC', args, 500, 5000)
    assert len(orders) == 5
    assert orders[0]['price'] == 4975.0
    assert orders[1]['price'] == 4970.0
    assert orders[2]['price'] == 4965.0
    assert orders[3]['price'] == 4960.0
    assert orders[4]['price'] == 4955.0

    assert math.isclose(orders[0]['size'], 0.020100502, abs_tol=0.0000001)
    assert math.isclose(orders[1]['size'], 0.020120724, abs_tol=0.0000001)
    assert math.isclose(orders[2]['size'], 0.020140987, abs_tol=0.0000001)
    assert math.isclose(orders[3]['size'], 0.020161290, abs_tol=0.0000001)
    assert math.isclose(orders[4]['size'], 0.020181634, abs_tol=0.0000001)

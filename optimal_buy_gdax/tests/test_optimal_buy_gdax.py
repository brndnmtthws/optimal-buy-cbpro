#!/usr/bin/env python3
import pytest
import json
import gdax

from .context import optimal_buy_gdax


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


def test_get_weights(coins):
    weights = optimal_buy_gdax.get_weights(coins, 'USD')
    assert 'BTC' in weights
    assert weights['BTC'] == 1


def test_get_products(coins):
    gdax_client = gdax.PublicClient()
    products = optimal_buy_gdax.get_products(gdax_client, coins, 'USD')
    assert len(products) >= 0
    assert 'BTC' in [product['base_currency'] for product in products]


def test_get_prices(coins):
    gdax_client = gdax.PublicClient()
    prices = optimal_buy_gdax.get_prices(gdax_client, coins, 'USD')
    assert len(prices) >= 0
    assert 'BTC' in prices
    assert prices['BTC'] >= 1

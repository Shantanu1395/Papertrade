#!/bin/bash

# Set up request
BASE_URL="https://testnet.binance.vision/api"
ENDPOINT="/v3/ticker/price"
SYMBOL="BTCUSDT"

# Send request
curl -X GET "$BASE_URL$ENDPOINT?symbol=$SYMBOL"
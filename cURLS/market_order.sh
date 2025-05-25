#!/bin/bash

# Set up authentication
API_KEY="05XHmPsHJxQ4rkilyW4NLFYVw0rKZ9sqnn7hKTrbwfYB3WLvh37TME1ZkLaj9uZ7"
API_SECRET="0i7u1uUw97OLmpIuzN2xRna1IN3rwL4S3k3AqsHp2YUBTmA2YHQz9DPiNgo2vNei"

# Set up request
BASE_URL="https://testnet.binance.vision/api"
ENDPOINT="/v3/order"
SYMBOL="BTCUSDT"
SIDE="BUY"
TYPE="MARKET"
QUOTE_ORDER_QTY="1000"  # Spend 1000 USDT
TIMESTAMP=$(date +%s000)
QUERY_STRING="symbol=$SYMBOL&side=$SIDE&type=$TYPE&quoteOrderQty=$QUOTE_ORDER_QTY&newOrderRespType=FULL&recvWindow=5000&timestamp=$TIMESTAMP"
SIGNATURE=$(echo -n "$QUERY_STRING" | openssl dgst -sha256 -hmac "$API_SECRET" | cut -d' ' -f2)

# Send request with verbose output
curl -v -H "X-MBX-APIKEY: $API_KEY" -X POST "$BASE_URL$ENDPOINT?$QUERY_STRING&signature=$SIGNATURE"
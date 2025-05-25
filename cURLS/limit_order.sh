#!/bin/bash

# Set up authentication
API_KEY="05XHmPsHJxQ4rkilyW4NLFYVw0rKZ9sqnn7hKTrbwfYB3WLvh37TME1ZkLaj9uZ7"
API_SECRET="0i7u1uUw97OLmpIuzN2xRna1IN3rwL4S3k3AqsHp2YUBTmA2YHQz9DPiNgo2vNei"

# Set up request
BASE_URL="https://testnet.binance.vision/api"
ENDPOINT="/v3/order"
SYMBOL="BTCUSDT"
SIDE="BUY"
TYPE="LIMIT"
PRICE="107500.00000000"  # Limit price (from entry_price in script)
QUANTITY="0.00930000"  # ~1000 USDT at 107500 (capital / price)
TIMESTAMP=$(date +%s000)
QUERY_STRING="symbol=$SYMBOL&side=$SIDE&type=$TYPE&timeInForce=GTC&quantity=$QUANTITY&price=$PRICE&newOrderRespType=FULL&recvWindow=5000×tamp=$TIMESTAMP"
SIGNATURE=$(echo -n "$QUERY_STRING" | openssl dgst -sha256 -hmac "$API_SECRET" | cut -d' ' -f2)

# Send request
curl -H "X-MBX-APIKEY: $API_KEY" -X POST "$BASE_URL$ENDPOINT?$QUERY_STRING&signature=$SIGNATURE"
#!/bin/bash

# Set up authentication
API_KEY="05XHmPsHJxQ4rkilyW4NLFYVw0rKZ9sqnn7hKTrbwfYB3WLvh37TME1ZkLaj9uZ7"
API_SECRET="0i7u1uUw97OLmpIuzN2xRna1IN3rwL4S3k3AqsHp2YUBTmA2YHQz9DPiNgo2vNei"

# Set up request
BASE_URL="https://testnet.binance.vision/api"
ENDPOINT="/v3/account"
TIMESTAMP=$(date +%s000)  # Current timestamp in milliseconds
QUERY_STRING="recvWindow=5000&timestamp=$TIMESTAMP"
SIGNATURE=$(echo -n "$QUERY_STRING" | openssl dgst -sha256 -hmac "$API_SECRET" | cut -d' ' -f2)

# Send request
curl -s -H "X-MBX-APIKEY: $API_KEY" -X GET "$BASE_URL$ENDPOINT?$QUERY_STRING&signature=$SIGNATURE"
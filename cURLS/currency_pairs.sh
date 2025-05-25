BASE_URL="https://testnet.binance.vision/api"
curl -s -X GET "$BASE_URL/v3/exchangeInfo" | jq -r '.symbols[] | select(.status == "TRADING" and .quoteAsset == "USDT") | .symbol' > usdt_pairs.txt
cat usdt_pairs.txt
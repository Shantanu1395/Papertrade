# 🧪 Real API Integration Test Setup

This guide helps you set up and run **real API integration tests** that make actual calls to Binance Testnet.

## 🎯 **What This Test Does**

The real API integration test performs a complete trading workflow:

1. **📊 Check Initial State** - Gets portfolio and USDT balance
2. **📈 Buy ETH** - Places market buy order for ETH/USDT
3. **✅ Verify Purchase** - Confirms ETH in portfolio, USDT decreased
4. **📉 Sell ETH** - Places market sell order for 100% of ETH
5. **✅ Verify Sale** - Confirms ETH removed, USDT increased
6. **📋 Check History** - Verifies 2 trades in last 15 minutes
7. **📈 Calculate P&L** - Shows profit/loss from the round trip

## 🔧 **Prerequisites**

### 1. Binance Testnet Account
- Go to [Binance Testnet](https://testnet.binance.vision/)
- Create an account (free)
- Get testnet funds (fake USDT for testing)

### 2. API Keys
- In Binance Testnet, go to API Management
- Create new API key with trading permissions
- **Important**: These are TESTNET keys (not real money)

### 3. Environment Variables
Set your testnet API credentials:

```bash
# Add to your ~/.bashrc, ~/.zshrc, or .env file
export TRADING_API_KEY="your_testnet_api_key_here"
export TRADING_API_SECRET="your_testnet_api_secret_here"
```

Or create a `.env` file in the project root:
```env
TRADING_API_KEY=your_testnet_api_key_here
TRADING_API_SECRET=your_testnet_api_secret_here
```

## 🚀 **Running the Test**

### Option 1: Easy Runner Script
```bash
python run_real_api_test.py
```

### Option 2: Direct pytest
```bash
# Set environment variables first
export TRADING_API_KEY="your_key"
export TRADING_API_SECRET="your_secret"

# Run the test
pytest tests/test_integration_trading.py::TestTradingWorkflow::test_complete_trading_workflow_real_api -v -s
```

## 💰 **Funding Your Testnet Account**

1. Go to [Binance Testnet Faucet](https://testnet.binance.vision/)
2. Login to your testnet account
3. Go to "Wallet" → "Faucet"
4. Request testnet USDT (usually 1000 USDT)
5. Wait a few minutes for funds to appear

## 📊 **Expected Test Output**

```
🚀 Starting REAL API Integration Test
============================================================
⚠️  This test makes ACTUAL calls to Binance Testnet API
⚠️  Ensure you have valid testnet API credentials
============================================================

📊 Initial portfolio: []
💰 Initial USDT balance: $10,000.00

📈 Placing BUY order...
✅ Buy order placed: {'symbol': 'ETHUSDT', 'orderId': 123456, ...}
🪙 ETH acquired: 0.4024 ETH

📊 Portfolio after buy: [{'asset': 'ETH', 'free': 0.4024, 'locked': 0.0}]
💰 USDT balance after buy: $9,000.00
💸 USDT spent: $1,000.00

📉 Placing SELL order...
✅ Sell order placed: {'symbol': 'ETHUSDT', 'orderId': 123457, ...}
🪙 ETH sold: 0.4024 ETH

📊 Portfolio after sell: []
💰 Final USDT balance: $9,950.00
💵 USDT received: $950.00
📈 Net P&L: $-50.00 (-0.50%)

📋 Checking trade history...
📊 Recent trades found: 2
✅ BUY trade: 0.4024 ETH @ $2484.61
✅ SELL trade: 0.4024 ETH @ $2484.30

🎉 Complete trading workflow test passed!
============================================================
```

## 🔍 **Troubleshooting**

### API Key Issues
```
❌ TRADING_API_KEY environment variable not set
```
**Solution**: Set your environment variables correctly

### Insufficient Balance
```
⚠️ Warning: Low USDT balance (100). Test may fail.
```
**Solution**: Request more testnet USDT from the faucet

### Order Failures
```
❌ Buy order failed: {"code":-1013,"msg":"Filter failure: MIN_NOTIONAL"}
```
**Solution**: The test automatically adjusts order size based on your balance

### Network Issues
```
❌ API request failed: Connection timeout
```
**Solution**: Check your internet connection and try again

## 🛡️ **Safety Notes**

- ✅ **Uses Testnet Only** - No real money involved
- ✅ **Fake Funds** - All USDT is testnet currency
- ✅ **Safe Testing** - Cannot affect real trading accounts
- ✅ **Isolated Environment** - Completely separate from live trading

## 📈 **What Success Means**

If the test passes, it means:
- ✅ Your API credentials work
- ✅ Your trading client can connect to Binance
- ✅ Order placement works correctly
- ✅ Portfolio tracking works
- ✅ Trade history recording works
- ✅ All API endpoints are functional

## 🔄 **Running Multiple Times**

You can run this test multiple times. Each run will:
- Use your current balance
- Place new orders
- Add to your trade history
- Show cumulative P&L over time

## 📞 **Getting Help**

If you encounter issues:
1. Check the error messages in the test output
2. Verify your API keys are correct
3. Ensure you have sufficient testnet balance
4. Check Binance Testnet status
5. Review the troubleshooting section above

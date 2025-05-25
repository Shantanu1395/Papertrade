# 🧪 Workflow Testing Endpoint

A dedicated API endpoint for testing the complete trading workflow with real Binance API calls.

## 🎯 **What It Does**

The `/workflow-test/run` endpoint performs the exact same 9-step workflow as your integration tests:

1. **📊 Get Initial Portfolio** - Calls `trading_client.view_account_balance()`
2. **💰 Get Initial USDT Balance** - Calls `trading_client.get_usdt_balance()`
3. **📈 Place BUY Order** - Calls `trading_client.place_market_order()`
4. **✅ Verify Portfolio** - Calls `trading_client.view_account_balance()`
5. **💸 Verify USDT Spent** - Calls `trading_client.get_usdt_balance()`
6. **📉 Place SELL Order** - Calls `trading_client.sell_asset_by_percentage()`
7. **🧹 Verify Portfolio Clean** - Calls `trading_client.view_account_balance()`
8. **💵 Verify USDT Received** - Calls `trading_client.get_usdt_balance()`
9. **📋 Check Trade History** - Calls `trading_client.get_trades_in_time_range()`

## 🚀 **How to Use**

### 1. Start Your Server
```bash
uvicorn app.main:app --reload
```

### 2. Test the Endpoint

#### Option A: Using the Test Script
```bash
export TRADING_API_KEY="your_testnet_key"
export TRADING_API_SECRET="your_testnet_secret"
python test_workflow_endpoint.py
```

#### Option B: Direct HTTP Request
```bash
curl -X POST "http://localhost:8000/workflow-test/run" \
  -H "Content-Type: application/json" \
  -d '{
    "order_amount_usdt": 50.0,
    "symbol": "ETH/USDT",
    "dry_run": true
  }'
```

#### Option C: Using FastAPI Docs
1. Go to `http://localhost:8000/docs`
2. Find `/workflow-test/run` endpoint
3. Click "Try it out"
4. Enter your parameters
5. Execute

## 📋 **Request Parameters**

```json
{
  "order_amount_usdt": 50.0,    // Amount to trade (default: 100.0)
  "symbol": "ETH/USDT",         // Trading pair (default: "ETH/USDT")
  "dry_run": true               // Simulate orders (default: false)
}
```

### Parameters Explained:
- **`order_amount_usdt`**: How much USDT to use for the buy order
- **`symbol`**: Which trading pair to test (ETH/USDT, BTC/USDT, etc.)
- **`dry_run`**: If `true`, simulates orders without real API calls

## 📊 **Response Format**

```json
{
  "test_id": "workflow_test_1748170123",
  "status": "completed",
  "total_steps": 9,
  "completed_steps": 9,
  "start_time": "2024-01-25T10:30:00",
  "end_time": "2024-01-25T10:31:30",
  "steps": [
    {
      "step_number": 1,
      "step_name": "Get Initial Portfolio Balance",
      "status": "success",
      "data": {"portfolio": [...]},
      "message": "Retrieved portfolio with 2 assets",
      "timestamp": "2024-01-25T10:30:05"
    }
    // ... 8 more steps
  ],
  "summary": {
    "initial_usdt_balance": 10000.0,
    "final_usdt_balance": 9975.0,
    "net_pnl": -25.0,
    "pnl_percentage": -0.25,
    "order_amount": 50.0,
    "symbol": "ETH/USDT",
    "dry_run": false,
    "duration_seconds": 90.5,
    "success_rate": 100.0
  }
}
```

## 🎭 **Dry Run vs Real Trading**

### Dry Run Mode (`dry_run: true`)
- ✅ **Safe testing** - No real orders placed
- ✅ **Fast execution** - Simulated responses
- ✅ **No API limits** - No rate limiting concerns
- ✅ **Predictable results** - Same simulated data
- ❌ **Not real validation** - Doesn't test actual API integration

### Real Trading Mode (`dry_run: false`)
- ✅ **Real validation** - Tests actual Binance integration
- ✅ **True confidence** - Proves everything works
- ✅ **Real market data** - Uses live prices and conditions
- ⚠️ **Uses testnet funds** - Consumes fake USDT
- ⚠️ **Slower execution** - Real API calls take time
- ⚠️ **Rate limits apply** - Binance API limits

## 🔧 **Error Handling**

The endpoint handles errors gracefully:

### Common Errors:
- **Insufficient Balance**: Automatically adjusts order size
- **API Key Issues**: Returns clear error message
- **Network Problems**: Retries and reports failures
- **Order Failures**: Continues to next steps when possible

### Response Status:
- **`completed`**: All 9 steps succeeded
- **`partial`**: Some steps succeeded, some failed
- **`failed`**: Critical early steps failed

## 📈 **Example Successful Response**

```json
{
  "test_id": "workflow_test_1748170123",
  "status": "completed",
  "total_steps": 9,
  "completed_steps": 9,
  "summary": {
    "initial_usdt_balance": 10000.0,
    "final_usdt_balance": 9975.0,
    "net_pnl": -25.0,
    "pnl_percentage": -0.25,
    "success_rate": 100.0
  }
}
```

## 🚨 **Safety Features**

1. **Balance Checks**: Won't place orders larger than available balance
2. **Testnet Only**: Only works with testnet API credentials
3. **Error Recovery**: Continues testing even if some steps fail
4. **Detailed Logging**: Every step is logged for debugging
5. **Dry Run Default**: Safer testing by default

## 🎯 **Use Cases**

### Development Testing
```bash
# Quick validation during development
curl -X POST "localhost:8000/workflow-test/run" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true, "order_amount_usdt": 10}'
```

### Pre-Production Validation
```bash
# Full real API test before going live
curl -X POST "localhost:8000/workflow-test/run" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false, "order_amount_usdt": 50}'
```

### Continuous Integration
```python
# In your CI/CD pipeline
response = requests.post("http://api:8000/workflow-test/run", 
                        json={"dry_run": True})
assert response.json()["status"] == "completed"
```

## 🔍 **Monitoring & Debugging**

### Check Endpoint Status
```bash
curl http://localhost:8000/workflow-test/status
```

### View Detailed Logs
The endpoint logs every step:
```
INFO: Step 1: Getting initial portfolio balance
INFO: Step 1 completed: 2 assets in portfolio
INFO: Step 2: Getting initial USDT balance
INFO: Step 2 completed: USDT balance = $10,000.00
```

### FastAPI Automatic Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🎉 **Benefits Over Test Files**

1. **HTTP Accessible**: Test from any language/tool
2. **No Test Framework**: No pytest/unittest dependencies
3. **Real-time Results**: Immediate JSON response
4. **CI/CD Friendly**: Easy to integrate in pipelines
5. **Production-like**: Tests through actual API endpoints
6. **Detailed Reporting**: Step-by-step results with timing
7. **Flexible Parameters**: Customize order size and symbol

This endpoint gives you the same confidence as integration tests but through a simple HTTP API! 🚀

# Trading API Integration Tests

This directory contains comprehensive integration tests for the Paper Trading API, with **two different testing approaches**:

1. **🎭 Mocked Tests** - Fast, isolated tests using fake API responses
2. **🌐 Real API Tests** - End-to-end tests making actual calls to Binance Testnet

## Test Scenarios

### Main Integration Test (`test_complete_trading_workflow`)

Tests the complete trading workflow as specified:

1. **Get initial portfolio balance** - Verify starting state
2. **Get initial USDT balance** - Record starting USDT amount
3. **Place market BUY order** - ETH/USDT with quote-quantity=1000
4. **Verify portfolio has ETH** - Confirm ETH was purchased
5. **Verify USDT balance decreased** - Confirm USDT was spent
6. **Sell 100% of ETH** - Market sell order with percentage=100
7. **Verify portfolio is empty** - Confirm no ETH remaining
8. **Verify USDT balance increased** - Confirm USDT was received
9. **Verify 2 trades in last 15 minutes** - Confirm both trades are recorded

### Additional Tests

- **Insufficient Balance Test** - Tests behavior with insufficient USDT
- **Portfolio State Transitions** - Verifies portfolio changes correctly

## Running the Tests

### 🎭 **Mocked Tests (Fast & Safe)**

These tests use fake API responses and don't require real API keys.

#### Option 1: Test Runner Script
```bash
python run_tests.py
```

#### Option 2: Direct pytest
```bash
pip install pytest pytest-asyncio httpx
pytest tests/test_integration_trading.py -v -k "not real_api"
```

### 🌐 **Real API Tests (End-to-End)**

These tests make actual calls to Binance Testnet API.

#### Prerequisites
1. Get Binance Testnet API keys from [testnet.binance.vision](https://testnet.binance.vision/)
2. Fund your testnet account with USDT
3. Set environment variables:
   ```bash
   export TRADING_API_KEY="your_testnet_api_key"
   export TRADING_API_SECRET="your_testnet_api_secret"
   ```

#### Option 1: Real API Test Runner (Recommended)
```bash
python run_real_api_test.py
```

#### Option 2: Direct pytest
```bash
pytest tests/test_integration_trading.py::TestTradingWorkflow::test_complete_trading_workflow_real_api -v -s
```

#### Setup Guide
See [REAL_API_TEST_SETUP.md](../REAL_API_TEST_SETUP.md) for detailed setup instructions.

## Test Architecture

### Mocking Strategy

The tests use comprehensive mocking to simulate Binance API responses:

- **Exchange Info** - Symbol precision and trading rules
- **Account Balance** - Different states (initial, after buy, after sell)
- **Order Responses** - Realistic buy/sell order confirmations
- **Price Data** - Current market prices

### Test Fixtures

- `client` - FastAPI test client for API calls
- `clean_test_environment` - Ensures clean state before/after tests
- `test_config` - Configuration for test trading client
- `temp_trade_history` - Temporary file for trade history

### Mock Responses

The tests simulate realistic trading scenarios:

- Initial balance: 10,000 USDT
- ETH purchase: ~0.5 ETH for 1,000 USDT at $2,000/ETH
- ETH sale: 0.5 ETH for ~950 USDT at $1,900/ETH (simulating price movement)
- Trading fees: Realistic commission structure

## Expected Test Output

When tests pass, you should see:

```
✅ Complete trading workflow test passed!
✅ All integration tests passed!
🎉 Integration tests completed successfully!
```

The tests verify:
- ✅ Portfolio starts empty (except USDT)
- ✅ USDT balance decreases after buy order (~1000 USDT spent)
- ✅ ETH appears in portfolio after buy order
- ✅ ETH disappears from portfolio after sell order
- ✅ USDT balance increases after sell order
- ✅ Exactly 2 trades recorded in last 15 minutes
- ✅ Trade details are correct (symbol, side, quantities)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **API Key Issues**: Tests use mocked responses, so real API keys aren't needed
4. **File Permissions**: Ensure write permissions for temporary test files

### Debug Mode

Run tests with extra verbosity:
```bash
pytest tests/test_integration_trading.py -v -s --tb=long
```

### Test Isolation

Each test runs in isolation with:
- Clean trade history
- Fresh mock responses
- Temporary files that are cleaned up

## Extending the Tests

To add new test scenarios:

1. Add new test methods to `TestTradingWorkflow` class
2. Create appropriate mock responses in `_setup_mock_responses()`
3. Update the mock request handler if needed
4. Follow the existing pattern for API calls and assertions

Example:
```python
def test_limit_order_workflow(self, client: TestClient, clean_test_environment):
    """Test limit order placement and execution."""
    # Your test implementation here
```

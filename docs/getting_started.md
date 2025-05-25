# Getting Started with Paper Trading API

This guide will help you set up and run the Paper Trading API on your local machine.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

1. Clone the repository or download the source code:

```bash
git clone <repository-url>
cd Trade
```

2. Create a virtual environment (optional but recommended):

```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory with your API credentials:

```
TRADING_API_KEY=your_api_key_here
TRADING_API_SECRET=your_api_secret_here
```

If you don't have API credentials, you can use the default testnet credentials for Binance, but functionality will be limited.

## Running the API

1. Start the FastAPI server:

```bash
python run_api.py
```

This will start the server on `http://0.0.0.0:8000` with auto-reload enabled.

2. Access the API documentation:

Open your browser and navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

The API is organized into the following categories:

### Account Endpoints

- `GET /account/balance` - Get all account balances
- `GET /account/usdt-balance` - Get USDT balance
- `GET /account/portfolio` - Get portfolio (non-USDT assets)

### Market Endpoints

- `GET /market/pairs` - Get all available trading pairs
- `GET /market/price/{symbol}` - Get current price for a symbol (e.g., BTC/USDT)

### Order Endpoints

- `GET /orders/fulfilled` - Get all fulfilled orders
- `GET /orders/open` - Get all open orders
- `POST /orders/limit` - Place a limit order
- `POST /orders/market` - Place a market order
- `POST /orders/sell-percentage` - Sell a percentage of an asset
- `POST /orders/sell-all-to-usdt` - Sell all assets to USDT

### Trade Endpoints

- `POST /trades/time-range` - Get trades in a specific time range
- `POST /trades/pnl/calculate` - Calculate PnL for a specific time range

## Example API Requests

Here are some example curl commands to interact with the API:

### Get Account Balance

```bash
curl -X GET "http://localhost:8000/account/balance" -H "accept: application/json"
```

### Get Current Price

```bash
curl -X GET "http://localhost:8000/market/price/BTC%2FUSDT" -H "accept: application/json"
```

### Place Market Order

```bash
curl -X POST "http://localhost:8000/orders/market" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETH/USDT",
    "side": "BUY",
    "quote_order_qty": 1000
  }'
```

### Sell Asset by Percentage

```bash
curl -X POST "http://localhost:8000/orders/sell-percentage" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETH/USDT",
    "percentage": 50
  }'
```

### Calculate PnL

```bash
curl -X POST "http://localhost:8000/trades/pnl/calculate" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2023-01-01 00:00:00",
    "end_time": "2023-12-31 23:59:59"
  }'
```

## Project Structure

The project follows a layered architecture:

- **Models Layer** (`app/models/`): Defines data models using Pydantic
- **Service Layer** (`app/services/`): Contains business logic with the PaperTradingClient
- **Router Layer** (`app/routers/`): Defines API endpoints and routes
- **Main Application** (`app/main.py`): Entry point for the FastAPI application

## Troubleshooting

If you encounter any issues:

1. Make sure your API credentials are correctly set in the `.env` file
2. Check that all dependencies are installed correctly
3. Verify that you're using a supported Python version
4. Look for error messages in the console output

## Contributing

If you'd like to contribute to this project, please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
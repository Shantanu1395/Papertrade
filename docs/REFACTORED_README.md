# 🚀 Paper Trading API - Refactored

A comprehensive FastAPI-based paper trading system for cryptocurrency exchanges with Binance integration.

## 📁 **New Project Structure**

```
/
├── app/                          # Main application
│   ├── core/                     # Core functionality
│   │   ├── config.py            # Configuration management
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── utils.py             # Utility functions
│   │   └── __init__.py          # Core exports
│   ├── routers/                  # API route handlers
│   ├── services/                 # Business logic
│   ├── dependencies.py          # FastAPI dependencies
│   └── main.py                  # FastAPI application
├── tests/                        # All test files
├── docs/                         # Documentation
├── generated/                    # Generated files (JSON, logs)
├── scripts/                      # Utility scripts
└── config/                       # Configuration files
```

## 🔧 **Setup & Installation**

### 1. **Environment Configuration**
```bash
# Copy example config
cp config/.env.example .env

# Set your credentials
export TRADING_API_KEY="your_binance_testnet_key"
export TRADING_API_SECRET="your_binance_testnet_secret"
```

### 2. **Start Server**
```bash
# Using the new startup script
python scripts/start_server.py

# Or traditional way
uvicorn app.main:app --reload
```

## 🎯 **Key Improvements**

### **Code Organization**
- ✅ **Centralized Configuration** - All settings in `app/core/config.py`
- ✅ **Proper Folder Structure** - Organized by functionality
- ✅ **Removed Duplicate Code** - DRY principles applied
- ✅ **Thread-Safe File Operations** - Using `FileManager` class

### **File Management**
- ✅ **Generated Files** → `generated/` folder
- ✅ **Test Files** → `tests/` folder  
- ✅ **Documentation** → `docs/` folder
- ✅ **Scripts** → `scripts/` folder

### **Enhanced Features**
- ✅ **Workflow Testing Endpoint** - `/workflow-test/run`
- ✅ **Better Error Handling** - Custom exceptions
- ✅ **Improved PnL Calculation** - Fixed calculation logic
- ✅ **Asset Exclusion** - Automatic filtering of problematic assets

## 📊 **API Endpoints**

### **Account Management**
- `GET /account/balance` - Get account balance (filtered)
- `GET /account/portfolio` - Get non-USDT holdings
- `GET /account/usdt-balance` - Get USDT balance only

### **Order Management**
- `POST /orders/market` - Place market order
- `POST /orders/limit` - Place limit order
- `POST /orders/sell-percentage` - Sell by percentage
- `POST /orders/sell-all-to-usdt` - Sell all assets to USDT

### **Trade Analysis**
- `GET /trades/history` - Get trade history
- `POST /trades/pnl/calculate` - Calculate PnL for time range

### **🆕 Workflow Testing**
- `POST /workflow-test/run` - Run complete trading workflow
- `GET /workflow-test/status` - Get testing capability status

## 🧪 **Testing**

### **Integration Tests**
```bash
cd tests
python test_integration.py
```

### **Workflow Testing**
```bash
# Test complete workflow via API
curl -X POST "http://localhost:8000/workflow-test/run" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true, "order_amount_usdt": 50}'

# Or use the test script
python tests/test_workflow_endpoint.py
```

## 🔧 **Configuration System**

### **Centralized Settings**
All configuration is now managed in `app/core/config.py`:

```python
from app.core import settings

# Access any setting
print(settings.binance_api_key)
print(settings.generated_dir)
print(settings.trade_history_file)
```

### **Environment Variables**
```bash
TRADING_API_KEY=your_key
TRADING_API_SECRET=your_secret
TRADING_HOST=0.0.0.0
TRADING_PORT=8000
TRADING_GENERATED_DIR=generated
```

## 📁 **File Management**

### **Thread-Safe Operations**
```python
from app.core import file_manager

# Read JSON file
data = file_manager.read_json("trade_history.json", [])

# Write JSON file
file_manager.write_json("config.json", {"key": "value"})

# Append to JSON list
file_manager.append_json_list("trades.json", new_trade)
```

### **Generated Files Location**
- `generated/trade_history.json` - Trade records
- `generated/excluded_currencies.json` - Excluded assets

## 🚀 **Quick Start**

```bash
# 1. Set credentials
export TRADING_API_KEY="your_testnet_key"
export TRADING_API_SECRET="your_testnet_secret"

# 2. Start server
python scripts/start_server.py

# 3. Test workflow
curl -X POST "localhost:8000/workflow-test/run" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# 4. View docs
open http://localhost:8000/docs
```

## 📈 **Benefits of Refactoring**

1. **🏗️ Better Organization** - Clear separation of concerns
2. **🔧 Easier Maintenance** - Centralized configuration
3. **🧪 Better Testing** - Dedicated workflow endpoint
4. **📁 Clean File Structure** - Everything in its place
5. **🔒 Thread Safety** - Safe concurrent operations
6. **⚡ Improved Performance** - Removed duplicate code
7. **📊 Better Monitoring** - Enhanced logging and error handling

## 🔍 **What Was Refactored**

### **Before**
- Scattered configuration across files
- Duplicate file operations
- JSON files in root directory
- Test files mixed with source code
- Hard-coded file paths

### **After**
- Centralized configuration system
- Thread-safe file manager
- Organized folder structure
- Separated test files
- Configurable file paths

The refactored codebase is now production-ready with proper structure, configuration management, and comprehensive testing capabilities! 🎉

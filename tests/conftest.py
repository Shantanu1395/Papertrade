"""
Test configuration and fixtures for integration tests.
"""
import pytest
import os
import json
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.services.trading_client import PaperTradingClient


@pytest.fixture
def test_config():
    """Test configuration for the trading client."""
    return {
        'api_key': 'test_api_key',
        'api_secret': 'test_api_secret',
        'testnet': True,
        'brokerage_fee': 0.001,
        'recv_window': 10000,
        'symbols': ['BTC/USDT', 'ETH/USDT']
    }


@pytest.fixture
def temp_trade_history():
    """Create a temporary trade history file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def clean_test_environment():
    """Ensure clean test environment before and after tests."""
    # Clean up any existing test files
    test_files = ['trade_history.json', 'excluded_currencies.json']
    backup_files = {}

    # Backup existing files
    for file in test_files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                backup_files[file] = f.read()
            os.remove(file)

    yield

    # Restore backed up files
    for file, content in backup_files.items():
        with open(file, 'w') as f:
            f.write(content)

    # Clean up test files
    for file in test_files:
        if os.path.exists(file) and file not in backup_files:
            os.remove(file)

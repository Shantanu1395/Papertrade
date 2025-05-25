"""
Utility functions for the trading application.
"""
import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from app.core.config import settings


class FileManager:
    """Thread-safe file operations manager."""
    
    def __init__(self):
        self.file_lock = threading.Lock()
    
    def read_json(self, filename: str, default: Any = None) -> Any:
        """Read JSON file with thread safety."""
        filepath = os.path.join(settings.generated_dir, filename)
        
        with self.file_lock:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logging.error(f"Failed to read {filename}: {e}")
                    return default
            return default
    
    def write_json(self, filename: str, data: Any) -> bool:
        """Write JSON file with thread safety."""
        filepath = os.path.join(settings.generated_dir, filename)
        
        with self.file_lock:
            try:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                logging.info(f"Successfully wrote {filename}")
                return True
            except Exception as e:
                logging.error(f"Failed to write {filename}: {e}")
                return False
    
    def append_json_list(self, filename: str, new_item: Dict) -> bool:
        """Append item to JSON list file."""
        current_data = self.read_json(filename, [])
        if not isinstance(current_data, list):
            current_data = []
        
        current_data.append(new_item)
        return self.write_json(filename, current_data)


def to_timestamp(time_input) -> int:
    """Convert various time formats to millisecond timestamp."""
    if isinstance(time_input, str):
        try:
            dt = datetime.strptime(time_input, "%Y-%m-%d %H:%M:%S")
            return int(dt.timestamp() * 1000)
        except ValueError:
            raise ValueError(f"Invalid time format: {time_input}. Expected format: YYYY-MM-DD HH:MM:SS")
    elif isinstance(time_input, datetime):
        return int(time_input.timestamp() * 1000)
    elif isinstance(time_input, (int, float)):
        return int(time_input)
    else:
        raise ValueError(f"Unsupported time format: {type(time_input)}")


def format_timestamp(timestamp_ms: int) -> str:
    """Format millisecond timestamp to readable string."""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def validate_symbol(symbol: str) -> str:
    """Validate and normalize trading symbol."""
    if not symbol:
        raise ValueError("Symbol cannot be empty")
    
    # Remove slash if present (ETH/USDT -> ETHUSDT)
    normalized = symbol.replace("/", "").upper()
    
    if not normalized.endswith("USDT"):
        raise ValueError(f"Only USDT pairs are supported. Got: {symbol}")
    
    return normalized


def validate_side(side: str) -> str:
    """Validate trading side."""
    side_upper = side.upper()
    if side_upper not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
    return side_upper


def validate_positive_number(value: float, name: str) -> float:
    """Validate that a number is positive."""
    if value <= 0:
        raise ValueError(f"Invalid {name}: {value}. Must be greater than 0")
    return value


def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage safely."""
    if total == 0:
        return 0.0
    return (part / total) * 100


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# Global file manager instance
file_manager = FileManager()

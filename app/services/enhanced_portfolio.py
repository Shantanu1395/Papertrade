"""
Enhanced Portfolio and Trade History Management System
Provides comprehensive portfolio analytics independent of Binance API limitations.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict

from app.core import file_manager, to_timestamp, format_timestamp


@dataclass
class Trade:
    """Enhanced trade data structure."""
    id: str
    symbol: str
    side: str  # BUY or SELL
    quantity: float
    price: float
    quote_qty: float
    commission: float
    commission_asset: str
    timestamp: int
    order_type: str
    binance_order_id: Optional[int] = None
    
    @property
    def base_asset(self) -> str:
        """Extract base asset from symbol (e.g., BTC from BTCUSDT)."""
        if self.symbol.endswith("USDT"):
            return self.symbol[:-4]  # Remove USDT
        elif self.symbol.endswith("BTC") and self.symbol != "BTC":
            return self.symbol[:-3]  # Remove BTC
        elif self.symbol.endswith("ETH") and self.symbol != "ETH":
            return self.symbol[:-3]  # Remove ETH
        else:
            return self.symbol  # Return as is if no known quote asset
    
    @property
    def quote_asset(self) -> str:
        """Extract quote asset from symbol."""
        if "USDT" in self.symbol:
            return "USDT"
        elif "BTC" in self.symbol and self.symbol != "BTCUSDT":
            return "BTC"
        elif "ETH" in self.symbol and self.symbol != "ETHUSDT":
            return "ETH"
        return "USDT"  # Default


@dataclass
class PortfolioAsset:
    """Enhanced portfolio asset structure."""
    asset: str
    free: float
    locked: float
    avg_buy_price: float
    total_invested: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    last_updated: int
    
    @property
    def total_quantity(self) -> float:
        return self.free + self.locked
    
    @property
    def current_value(self) -> float:
        return self.total_quantity * self.current_price


class EnhancedPortfolioManager:
    """Enhanced portfolio management with comprehensive analytics."""
    
    def __init__(self, trading_client):
        self.trading_client = trading_client
        self.trades_file = "enhanced_trades.json"
        self.portfolio_file = "enhanced_portfolio.json"
        self.analytics_file = "portfolio_analytics.json"
        
    def save_trade(self, trade_data: Dict) -> str:
        """Save trade with enhanced data structure."""
        # Generate unique trade ID
        trade_id = f"{trade_data['symbol']}_{trade_data['side']}_{int(time.time() * 1000)}"
        
        enhanced_trade = Trade(
            id=trade_id,
            symbol=trade_data['symbol'],
            side=trade_data['side'],
            quantity=float(trade_data['quantity']),
            price=float(trade_data['price']),
            quote_qty=float(trade_data.get('quoteQty', trade_data['quantity'] * trade_data['price'])),
            commission=float(trade_data.get('commission', 0)),
            commission_asset=trade_data.get('commissionAsset', 'USDT'),
            timestamp=trade_data['time'],
            order_type=trade_data.get('orderType', 'MARKET'),
            binance_order_id=trade_data.get('tradeId')
        )
        
        # Save to enhanced trades file
        trades = file_manager.read_json(self.trades_file, [])
        trades.append(asdict(enhanced_trade))
        file_manager.write_json(self.trades_file, trades)
        
        # Update portfolio after each trade
        self._update_portfolio_from_trade(enhanced_trade)
        
        logging.info(f"Enhanced trade saved: {trade_id}")
        return trade_id
    
    def _update_portfolio_from_trade(self, trade: Trade):
        """Update portfolio based on trade execution."""
        portfolio = self.get_enhanced_portfolio()
        
        if trade.side == "BUY":
            self._process_buy_trade(portfolio, trade)
        else:  # SELL
            self._process_sell_trade(portfolio, trade)
        
        # Save updated portfolio
        self._save_portfolio(portfolio)
    
    def _process_buy_trade(self, portfolio: Dict[str, PortfolioAsset], trade: Trade):
        """Process buy trade and update portfolio."""
        asset = trade.base_asset
        
        if asset in portfolio:
            # Update existing position
            current_asset = portfolio[asset]
            total_quantity = current_asset.total_quantity + trade.quantity
            total_cost = (current_asset.total_quantity * current_asset.avg_buy_price) + trade.quote_qty
            new_avg_price = total_cost / total_quantity if total_quantity > 0 else 0
            
            current_asset.free += trade.quantity
            current_asset.avg_buy_price = new_avg_price
            current_asset.total_invested = total_cost
        else:
            # Create new position
            portfolio[asset] = PortfolioAsset(
                asset=asset,
                free=trade.quantity,
                locked=0.0,
                avg_buy_price=trade.price,
                total_invested=trade.quote_qty,
                current_price=trade.price,
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                last_updated=trade.timestamp
            )
    
    def _process_sell_trade(self, portfolio: Dict[str, PortfolioAsset], trade: Trade):
        """Process sell trade and update portfolio."""
        asset = trade.base_asset

        if asset in portfolio:
            current_asset = portfolio[asset]

            # Calculate realized PnL for this sale
            realized_pnl = (trade.price - current_asset.avg_buy_price) * trade.quantity

            # Update position
            current_asset.free -= trade.quantity
            current_asset.total_invested -= (current_asset.avg_buy_price * trade.quantity)

            # Remove asset if quantity becomes zero or negative
            if current_asset.total_quantity <= 0.000001:
                del portfolio[asset]

            # Log realized PnL
            self._log_realized_pnl(asset, trade, realized_pnl)
        else:
            # If asset not in portfolio, assume avg buy price equals sell price (no PnL)
            self._log_realized_pnl(asset, trade, 0.0)
    
    def get_enhanced_portfolio(self) -> Dict[str, PortfolioAsset]:
        """Get enhanced portfolio with current prices and PnL."""
        portfolio_data = file_manager.read_json(self.portfolio_file, {})
        portfolio = {}

        for asset_name, data in portfolio_data.items():
            asset = PortfolioAsset(**data)
            # Filter out dust holdings (less than $1 value)
            if asset.current_value >= 1.0:
                portfolio[asset_name] = asset

        # Update current prices and PnL
        self._update_current_prices(portfolio)

        return portfolio
    
    def _update_current_prices(self, portfolio: Dict[str, PortfolioAsset]):
        """Update current prices and calculate unrealized PnL."""
        for asset_name, asset in portfolio.items():
            try:
                # Get current price from trading client
                symbol = f"{asset_name}USDT"
                current_price = self.trading_client.view_current_price(symbol)
                
                if current_price:
                    asset.current_price = current_price
                    asset.unrealized_pnl = (current_price - asset.avg_buy_price) * asset.total_quantity
                    asset.unrealized_pnl_percent = ((current_price - asset.avg_buy_price) / asset.avg_buy_price) * 100 if asset.avg_buy_price > 0 else 0
                    asset.last_updated = int(time.time() * 1000)
                    
            except Exception as e:
                logging.warning(f"Failed to update price for {asset_name}: {e}")
    
    def _save_portfolio(self, portfolio: Dict[str, PortfolioAsset]):
        """Save portfolio to file."""
        portfolio_data = {name: asdict(asset) for name, asset in portfolio.items()}
        file_manager.write_json(self.portfolio_file, portfolio_data)
    
    def _log_realized_pnl(self, asset: str, trade: Trade, realized_pnl: float):
        """Log realized PnL for analytics."""
        pnl_data = {
            "asset": asset,
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "quantity": trade.quantity,
            "sell_price": trade.price,
            "realized_pnl": realized_pnl,
            "timestamp": trade.timestamp
        }
        
        # Append to realized PnL log
        file_manager.append_json_list("realized_pnl.json", pnl_data)
    
    def get_trade_history(self, limit: Optional[int] = None, 
                         start_time: Optional[int] = None, 
                         end_time: Optional[int] = None) -> List[Dict]:
        """Get enhanced trade history with filtering."""
        trades = file_manager.read_json(self.trades_file, [])
        
        # Filter by time range if provided
        if start_time or end_time:
            filtered_trades = []
            for trade in trades:
                trade_time = trade['timestamp']
                if start_time and trade_time < start_time:
                    continue
                if end_time and trade_time > end_time:
                    continue
                filtered_trades.append(trade)
            trades = filtered_trades
        
        # Sort by timestamp (newest first)
        trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply limit if provided
        if limit:
            trades = trades[:limit]
        
        # Add formatted timestamps
        for trade in trades:
            trade['formatted_time'] = format_timestamp(trade['timestamp'])
        
        return trades

    def get_enhanced_trades(self) -> List[Dict]:
        """Get all enhanced trades in the new format."""
        trades = file_manager.read_json(self.trades_file, [])

        # Convert to the expected format for the frontend
        formatted_trades = []
        for trade in trades:
            # Handle both old and new field names
            quote_qty = trade.get('quoteQty', trade.get('quote_qty', 0))
            commission_asset = trade.get('commissionAsset', trade.get('commission_asset', 'USDT'))
            order_type = trade.get('orderType', trade.get('order_type', 'MARKET'))
            trade_time = trade.get('time', trade.get('timestamp', 0))

            formatted_trade = {
                'symbol': trade['symbol'],
                'side': trade['side'],
                'quantity': trade['quantity'],
                'price': trade['price'],
                'quoteQty': quote_qty,
                'commission': trade['commission'],
                'commissionAsset': commission_asset,
                'time': trade_time,
                'orderType': order_type,
                'tradeId': trade.get('tradeId', trade.get('id')),
                'formatted_time': format_timestamp(trade_time),
                'total_value': trade['quantity'] * trade['price']
            }
            formatted_trades.append(formatted_trade)

        return formatted_trades

    def get_trades_in_range(self, start_time: int, end_time: int) -> List[Dict]:
        """Get trades within a specific time range."""
        trades = self.get_enhanced_trades()
        return [
            trade for trade in trades
            if start_time <= trade['time'] <= end_time
        ]

    def calculate_portfolio_analytics(self) -> Dict[str, Any]:
        """Calculate comprehensive portfolio analytics."""
        portfolio = self.get_enhanced_portfolio()
        trades = file_manager.read_json(self.trades_file, [])

        analytics = {
            "total_portfolio_value": 0.0,
            "total_invested": 0.0,
            "total_unrealized_pnl": 0.0,
            "total_unrealized_pnl_percent": 0.0,
            "total_realized_pnl": 0.0,
            "asset_allocation": {},
            "top_performers": [],
            "worst_performers": [],
            "trading_stats": self._calculate_trading_stats(trades),
            "last_updated": int(time.time() * 1000)
        }

        # Calculate portfolio totals
        for asset_name, asset in portfolio.items():
            analytics["total_portfolio_value"] += asset.current_value
            analytics["total_invested"] += asset.total_invested
            analytics["total_unrealized_pnl"] += asset.unrealized_pnl

        # Calculate overall PnL percentage
        if analytics["total_invested"] > 0:
            analytics["total_unrealized_pnl_percent"] = (analytics["total_unrealized_pnl"] / analytics["total_invested"]) * 100

        # Calculate asset allocation
        if analytics["total_portfolio_value"] > 0:
            for asset_name, asset in portfolio.items():
                allocation_percent = (asset.current_value / analytics["total_portfolio_value"]) * 100
                analytics["asset_allocation"][asset_name] = {
                    "value": asset.current_value,
                    "percentage": allocation_percent,
                    "quantity": asset.total_quantity
                }

        # Get realized PnL
        realized_pnl_data = file_manager.read_json("realized_pnl.json", [])
        analytics["total_realized_pnl"] = sum(pnl["realized_pnl"] for pnl in realized_pnl_data)

        # Find top and worst performers
        performers = [(name, asset.unrealized_pnl_percent) for name, asset in portfolio.items()]
        performers.sort(key=lambda x: x[1], reverse=True)

        analytics["top_performers"] = performers[:5]
        analytics["worst_performers"] = performers[-5:] if len(performers) > 5 else []

        # Save analytics
        file_manager.write_json(self.analytics_file, analytics)

        return analytics

    def _calculate_trading_stats(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate trading statistics."""
        if not trades:
            return {
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "total_volume": 0.0,
                "avg_trade_size": 0.0,
                "most_traded_asset": None,
                "trading_frequency": 0.0
            }

        buy_trades = [t for t in trades if t['side'] == 'BUY']
        sell_trades = [t for t in trades if t['side'] == 'SELL']

        total_volume = sum(t['quote_qty'] for t in trades)
        avg_trade_size = total_volume / len(trades) if trades else 0

        # Find most traded asset
        asset_counts = defaultdict(int)
        for trade in trades:
            base_asset = trade['symbol'].replace('USDT', '').replace('BTC', '').replace('ETH', '')
            asset_counts[base_asset] += 1

        most_traded_asset = max(asset_counts.items(), key=lambda x: x[1])[0] if asset_counts else None

        # Calculate trading frequency (trades per day)
        if len(trades) > 1:
            time_span_days = (trades[0]['timestamp'] - trades[-1]['timestamp']) / (1000 * 60 * 60 * 24)
            trading_frequency = len(trades) / max(time_span_days, 1)
        else:
            trading_frequency = 0

        return {
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_volume": total_volume,
            "avg_trade_size": avg_trade_size,
            "most_traded_asset": most_traded_asset,
            "trading_frequency": round(trading_frequency, 2)
        }

    def get_asset_performance(self, asset: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed performance for a specific asset."""
        trades = file_manager.read_json(self.trades_file, [])
        portfolio = self.get_enhanced_portfolio()

        # Filter trades for this asset
        asset_trades = [
            t for t in trades
            if t['symbol'].startswith(asset) and
            t['timestamp'] >= (int(time.time() * 1000) - (days * 24 * 60 * 60 * 1000))
        ]

        if not asset_trades:
            return {"error": f"No trades found for {asset} in the last {days} days"}

        # Calculate metrics
        buy_trades = [t for t in asset_trades if t['side'] == 'BUY']
        sell_trades = [t for t in asset_trades if t['side'] == 'SELL']

        total_bought = sum(t['quantity'] for t in buy_trades)
        total_sold = sum(t['quantity'] for t in sell_trades)
        avg_buy_price = sum(t['price'] * t['quantity'] for t in buy_trades) / total_bought if total_bought > 0 else 0
        avg_sell_price = sum(t['price'] * t['quantity'] for t in sell_trades) / total_sold if total_sold > 0 else 0

        current_holding = portfolio.get(asset)

        return {
            "asset": asset,
            "period_days": days,
            "total_trades": len(asset_trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_bought": total_bought,
            "total_sold": total_sold,
            "net_position": total_bought - total_sold,
            "avg_buy_price": avg_buy_price,
            "avg_sell_price": avg_sell_price,
            "current_holding": asdict(current_holding) if current_holding else None,
            "trades": asset_trades
        }

    def sync_with_binance_portfolio(self):
        """Sync our enhanced portfolio with actual Binance balances."""
        try:
            # Get actual balances from Binance
            binance_portfolio = self.trading_client.view_portfolio()
            enhanced_portfolio = self.get_enhanced_portfolio()

            # Update quantities from Binance data
            for binance_asset in binance_portfolio:
                asset_name = binance_asset['asset']
                if asset_name in enhanced_portfolio:
                    enhanced_portfolio[asset_name].free = binance_asset['free']
                    enhanced_portfolio[asset_name].locked = binance_asset['locked']
                else:
                    # New asset not in our records - add with current price as avg buy price
                    try:
                        current_price = self.trading_client.view_current_price(f"{asset_name}USDT")
                        enhanced_portfolio[asset_name] = PortfolioAsset(
                            asset=asset_name,
                            free=binance_asset['free'],
                            locked=binance_asset['locked'],
                            avg_buy_price=current_price or 0,
                            total_invested=(binance_asset['free'] + binance_asset['locked']) * (current_price or 0),
                            current_price=current_price or 0,
                            unrealized_pnl=0.0,
                            unrealized_pnl_percent=0.0,
                            last_updated=int(time.time() * 1000)
                        )
                    except Exception as e:
                        logging.warning(f"Failed to add new asset {asset_name}: {e}")

            # Remove assets that are no longer in Binance portfolio
            binance_assets = {asset['asset'] for asset in binance_portfolio}
            assets_to_remove = [name for name in enhanced_portfolio.keys() if name not in binance_assets]
            for asset_name in assets_to_remove:
                del enhanced_portfolio[asset_name]

            # Save updated portfolio
            self._save_portfolio(enhanced_portfolio)
            logging.info("Portfolio synced with Binance successfully")

        except Exception as e:
            logging.error(f"Failed to sync portfolio with Binance: {e}")

    def export_portfolio_report(self, format_type: str = "json") -> Dict[str, Any]:
        """Export comprehensive portfolio report."""
        analytics = self.calculate_portfolio_analytics()
        portfolio = self.get_enhanced_portfolio()
        recent_trades = self.get_trade_history(limit=50)

        report = {
            "report_generated": format_timestamp(int(time.time() * 1000)),
            "portfolio_summary": analytics,
            "detailed_holdings": {name: asdict(asset) for name, asset in portfolio.items()},
            "recent_trades": recent_trades,
            "realized_pnl_history": file_manager.read_json("realized_pnl.json", [])
        }

        # Save report
        timestamp = int(time.time())
        report_filename = f"portfolio_report_{timestamp}.json"
        file_manager.write_json(report_filename, report)

        return report

    def migrate_existing_trades(self):
        """Migrate existing trade history to enhanced portfolio system."""
        try:
            # Read existing trade history
            existing_trades = file_manager.read_json("trade_history.json", [])

            if not existing_trades:
                logging.info("No existing trades to migrate")
                return

            logging.info(f"Migrating {len(existing_trades)} existing trades to enhanced portfolio system")

            # Clear existing enhanced data to avoid duplicates
            file_manager.write_json(self.trades_file, [])
            file_manager.write_json(self.portfolio_file, {})
            file_manager.write_json(self.analytics_file, {})
            file_manager.write_json("realized_pnl.json", [])

            # Process each trade
            for trade_data in existing_trades:
                try:
                    # Convert old format to new format
                    enhanced_trade_data = {
                        'symbol': trade_data['symbol'],
                        'side': trade_data['side'],
                        'quantity': trade_data['quantity'],
                        'price': trade_data['price'],
                        'quoteQty': trade_data.get('quoteQty', trade_data['quantity'] * trade_data['price']),
                        'commission': trade_data.get('commission', 0),
                        'commissionAsset': trade_data.get('commissionAsset', 'USDT'),
                        'time': trade_data['time'],
                        'orderType': trade_data.get('orderType', 'MARKET'),
                        'tradeId': trade_data.get('tradeId')
                    }

                    # Save to enhanced system
                    self.save_trade(enhanced_trade_data)

                except Exception as e:
                    logging.warning(f"Failed to migrate trade: {e}")
                    continue

            logging.info("Trade migration completed successfully")

        except Exception as e:
            logging.error(f"Failed to migrate existing trades: {e}")

    def initialize_enhanced_system(self):
        """Initialize the enhanced portfolio system with existing data."""
        # Check if enhanced trades file exists and has data
        enhanced_trades = file_manager.read_json(self.trades_file, [])

        if not enhanced_trades:
            # No enhanced trades, try to migrate from existing trade history
            self.migrate_existing_trades()

        # Sync with current Binance portfolio
        self.sync_with_binance_portfolio()

        # Calculate initial analytics
        self.calculate_portfolio_analytics()

        logging.info("Enhanced portfolio system initialized successfully")

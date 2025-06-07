"""
Enhanced Portfolio API endpoints with comprehensive analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.services.enhanced_portfolio import EnhancedPortfolioManager
from app.services.trading_client import PaperTradingClient
from app.dependencies import get_trading_client
from app.core import format_timestamp

router = APIRouter(
    prefix="/enhanced-portfolio",
    tags=["Enhanced Portfolio"],
    responses={404: {"description": "Not found"}},
)


def get_enhanced_portfolio_manager(client: PaperTradingClient = Depends(get_trading_client)) -> EnhancedPortfolioManager:
    """Dependency to get enhanced portfolio manager."""
    return EnhancedPortfolioManager(client)


@router.get("/portfolio")
async def get_enhanced_portfolio(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Get enhanced portfolio with current prices and PnL."""
    try:
        portfolio = manager.get_enhanced_portfolio()
        
        # Convert to serializable format
        portfolio_data = []
        for asset_name, asset in portfolio.items():
            portfolio_data.append({
                "asset": asset.asset,
                "free": asset.free,
                "locked": asset.locked,
                "total_quantity": asset.total_quantity,
                "avg_buy_price": asset.avg_buy_price,
                "current_price": asset.current_price,
                "current_value": asset.current_value,
                "total_invested": asset.total_invested,
                "unrealized_pnl": asset.unrealized_pnl,
                "unrealized_pnl_percent": asset.unrealized_pnl_percent,
                "last_updated": format_timestamp(asset.last_updated)
            })
        
        return portfolio_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics")
async def get_portfolio_analytics(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Get comprehensive portfolio analytics."""
    try:
        analytics = manager.calculate_portfolio_analytics()
        
        # Format timestamps in analytics
        analytics["last_updated"] = format_timestamp(analytics["last_updated"])
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/asset/{asset}/performance")
async def get_asset_performance(
    asset: str,
    days: int = Query(30, description="Number of days to analyze"),
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Get detailed performance analysis for a specific asset."""
    try:
        performance = manager.get_asset_performance(asset.upper(), days)
        return performance
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def sync_portfolio_with_binance(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Sync enhanced portfolio with actual Binance balances."""
    try:
        manager.sync_with_binance_portfolio()
        return {"message": "Portfolio synced successfully with Binance"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/initialize")
async def initialize_enhanced_system(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Initialize enhanced portfolio system with existing trade data."""
    try:
        manager.initialize_enhanced_system()
        return {"message": "Enhanced portfolio system initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/report")
async def export_portfolio_report(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Export comprehensive portfolio report."""
    try:
        report = manager.export_portfolio_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary")
async def get_portfolio_summary(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Get quick portfolio summary for dashboard."""
    try:
        analytics = manager.calculate_portfolio_analytics()
        portfolio = manager.get_enhanced_portfolio()
        
        # Get recent trades
        recent_trades = manager.get_trade_history(limit=5)
        
        summary = {
            "total_value": analytics["total_portfolio_value"],
            "total_invested": analytics["total_invested"],
            "total_pnl": analytics["total_unrealized_pnl"] + analytics["total_realized_pnl"],
            "unrealized_pnl": analytics["total_unrealized_pnl"],
            "realized_pnl": analytics["total_realized_pnl"],
            "pnl_percentage": analytics["total_unrealized_pnl_percent"],
            "asset_count": len(portfolio),
            "top_performer": analytics["top_performers"][0] if analytics["top_performers"] else None,
            "worst_performer": analytics["worst_performers"][-1] if analytics["worst_performers"] else None,
            "recent_trades": recent_trades,
            "trading_stats": analytics["trading_stats"],
            "last_updated": analytics["last_updated"]
        }
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/allocation")
async def get_asset_allocation(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Get asset allocation breakdown for portfolio visualization."""
    try:
        analytics = manager.calculate_portfolio_analytics()
        
        # Format allocation data for charts
        allocation_data = []
        for asset, data in analytics["asset_allocation"].items():
            allocation_data.append({
                "asset": asset,
                "value": data["value"],
                "percentage": round(data["percentage"], 2),
                "quantity": data["quantity"]
            })
        
        # Sort by value (largest first)
        allocation_data.sort(key=lambda x: x["value"], reverse=True)
        
        return {
            "allocation": allocation_data,
            "total_value": analytics["total_portfolio_value"],
            "diversification_score": len(allocation_data),  # Simple diversification metric
            "largest_position_percent": allocation_data[0]["percentage"] if allocation_data else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trades")
async def get_enhanced_trades(
    limit: int = Query(100, description="Number of trades to return"),
    offset: int = Query(0, description="Number of trades to skip"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    side: Optional[str] = Query(None, description="Filter by side (BUY/SELL)"),
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Get enhanced trade history with filtering and pagination."""
    try:
        trades = manager.get_enhanced_trades()

        # Apply filters
        if symbol:
            trades = [t for t in trades if t["symbol"] == symbol.upper()]
        if side:
            trades = [t for t in trades if t["side"] == side.upper()]

        # Sort by time (newest first)
        trades.sort(key=lambda x: x["time"], reverse=True)

        # Apply pagination
        total_trades = len(trades)
        paginated_trades = trades[offset:offset + limit]

        # Add formatted timestamps and additional info
        for trade in paginated_trades:
            trade["formatted_time"] = format_timestamp(trade["time"])
            trade["total_value"] = trade["quantity"] * trade["price"]

        return {
            "trades": paginated_trades,
            "pagination": {
                "total": total_trades,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_trades
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/performance/timeline")
async def get_performance_timeline(
    days: int = Query(30, description="Number of days for timeline"),
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Get portfolio performance timeline for charts."""
    try:
        # Get trades for the specified period
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)
        
        trades = manager.get_trade_history(start_time=start_time, end_time=end_time)
        
        # Group trades by day and calculate daily portfolio value
        daily_data = {}
        current_date = datetime.fromtimestamp(start_time / 1000).date()
        end_date = datetime.fromtimestamp(end_time / 1000).date()
        
        while current_date <= end_date:
            daily_data[current_date.isoformat()] = {
                "date": current_date.isoformat(),
                "trades": 0,
                "volume": 0.0,
                "pnl": 0.0
            }
            current_date += timedelta(days=1)
        
        # Populate with actual trade data
        for trade in trades:
            trade_date = datetime.fromtimestamp(trade["timestamp"] / 1000).date().isoformat()
            if trade_date in daily_data:
                daily_data[trade_date]["trades"] += 1
                daily_data[trade_date]["volume"] += trade["quote_qty"]
        
        timeline = list(daily_data.values())
        timeline.sort(key=lambda x: x["date"])
        
        return {
            "timeline": timeline,
            "period_days": days,
            "total_trades": len(trades),
            "total_volume": sum(t["quote_qty"] for t in trades)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pnl/calculate")
async def calculate_pnl(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Calculate PnL for a specific date range."""
    try:
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Convert to timestamps
        start_timestamp = int(start_dt.timestamp() * 1000)
        end_timestamp = int((end_dt.timestamp() + 24 * 60 * 60) * 1000)  # End of day

        # Get trades in range
        trades = manager.get_trades_in_range(start_timestamp, end_timestamp)

        # Calculate PnL
        total_realized_pnl = 0
        total_buy_volume = 0
        total_sell_volume = 0
        trade_count = 0

        symbol_pnl = defaultdict(float)
        symbol_trades = defaultdict(int)

        for trade in trades:
            trade_count += 1
            symbol = trade["symbol"]
            symbol_trades[symbol] += 1

            if trade["side"] == "BUY":
                total_buy_volume += trade["quoteQty"]
            else:  # SELL
                total_sell_volume += trade["quoteQty"]
                # Add realized PnL if available
                realized_pnl = trade.get("realized_pnl", 0)
                total_realized_pnl += realized_pnl
                symbol_pnl[symbol] += realized_pnl

        # Get current portfolio value for unrealized PnL calculation
        portfolio = manager.get_enhanced_portfolio()
        current_portfolio_value = sum(
            holding.current_value for holding in portfolio.values()
            if holding.asset != "USDT"
        )

        # Calculate net trading result
        net_trading_result = total_sell_volume - total_buy_volume

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": (end_dt - start_dt).days + 1
            },
            "trading_summary": {
                "total_trades": trade_count,
                "buy_volume": round(total_buy_volume, 2),
                "sell_volume": round(total_sell_volume, 2),
                "net_trading_result": round(net_trading_result, 2)
            },
            "pnl_breakdown": {
                "realized_pnl": round(total_realized_pnl, 2),
                "current_portfolio_value": round(current_portfolio_value, 2),
                "net_result": round(net_trading_result, 2)
            },
            "symbol_breakdown": [
                {
                    "symbol": symbol,
                    "trades": count,
                    "realized_pnl": round(pnl, 2)
                }
                for symbol, (count, pnl) in
                zip(symbol_trades.keys(), zip(symbol_trades.values(), symbol_pnl.values()))
                if count > 0
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/migrate")
async def migrate_trades(
    manager: EnhancedPortfolioManager = Depends(get_enhanced_portfolio_manager)
):
    """Migrate existing trades to enhanced portfolio system."""
    try:
        manager.migrate_existing_trades()
        return {"message": "Trade migration completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

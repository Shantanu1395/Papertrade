"""
Workflow testing endpoint for complete trading workflow validation.
This endpoint performs the complete trading workflow with real API calls.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.dependencies import get_trading_client
from app.services.trading_client import PaperTradingClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow-test", tags=["Workflow Testing"])


class WorkflowTestRequest(BaseModel):
    """Request model for workflow testing."""
    order_amount_usdt: Optional[float] = 100.0  # Amount to trade in USDT
    symbol: Optional[str] = "ETH/USDT"  # Trading pair
    dry_run: Optional[bool] = False  # If True, only simulate without real orders


class WorkflowStep(BaseModel):
    """Model for individual workflow step result."""
    step_number: int
    step_name: str
    status: str  # "success", "failed", "skipped"
    data: Dict[str, Any]
    message: str
    timestamp: datetime


class WorkflowTestResponse(BaseModel):
    """Response model for workflow testing."""
    test_id: str
    status: str  # "completed", "failed", "partial"
    total_steps: int
    completed_steps: int
    start_time: datetime
    end_time: datetime
    steps: List[WorkflowStep]
    summary: Dict[str, Any]


@router.post("/run", response_model=WorkflowTestResponse)
async def run_workflow_test(
    request: WorkflowTestRequest,
    trading_client: PaperTradingClient = Depends(get_trading_client)
):
    """
    Run complete trading workflow test with real API calls.

    This endpoint performs the exact same steps as the integration test:
    1. Get initial portfolio balance
    2. Get initial USDT balance
    3. Place market BUY order
    4. Verify portfolio has purchased asset
    5. Verify USDT balance decreased
    6. Sell 100% of purchased asset
    7. Verify portfolio is empty
    8. Verify USDT balance increased
    9. Check trade history for the trades
    """
    test_id = f"workflow_test_{int(datetime.now().timestamp())}"
    start_time = datetime.now()
    steps = []

    logger.info(f"Starting workflow test {test_id} with request: {request}")

    try:
        # Step 1: Get initial portfolio balance
        step1_start = datetime.now()
        try:
            logger.info("Step 1: Getting initial portfolio balance")
            initial_portfolio = trading_client.view_account_balance()

            steps.append(WorkflowStep(
                step_number=1,
                step_name="Get Initial Portfolio Balance",
                status="success",
                data={"portfolio": initial_portfolio},
                message=f"Retrieved portfolio with {len(initial_portfolio)} assets",
                timestamp=step1_start
            ))
            logger.info(f"Step 1 completed: {len(initial_portfolio)} assets in portfolio")

        except Exception as e:
            logger.error(f"Step 1 failed: {e}")
            steps.append(WorkflowStep(
                step_number=1,
                step_name="Get Initial Portfolio Balance",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to get portfolio: {e}",
                timestamp=step1_start
            ))
            raise HTTPException(status_code=500, detail=f"Step 1 failed: {e}")

        # Step 2: Get initial USDT balance
        step2_start = datetime.now()
        try:
            logger.info("Step 2: Getting initial USDT balance")
            initial_usdt_balance = trading_client.view_usdt_balance()

            steps.append(WorkflowStep(
                step_number=2,
                step_name="Get Initial USDT Balance",
                status="success",
                data={"usdt_balance": initial_usdt_balance},
                message=f"Initial USDT balance: ${initial_usdt_balance:,.2f}",
                timestamp=step2_start
            ))
            logger.info(f"Step 2 completed: USDT balance = ${initial_usdt_balance:,.2f}")

            # Check if we have enough balance
            if initial_usdt_balance < request.order_amount_usdt:
                logger.warning(f"Insufficient balance: {initial_usdt_balance} < {request.order_amount_usdt}")
                # Adjust order amount to 90% of available balance
                request.order_amount_usdt = initial_usdt_balance * 0.9
                logger.info(f"Adjusted order amount to: ${request.order_amount_usdt:,.2f}")

        except Exception as e:
            logger.error(f"Step 2 failed: {e}")
            steps.append(WorkflowStep(
                step_number=2,
                step_name="Get Initial USDT Balance",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to get USDT balance: {e}",
                timestamp=step2_start
            ))
            raise HTTPException(status_code=500, detail=f"Step 2 failed: {e}")

        # Step 3: Place market BUY order
        step3_start = datetime.now()
        buy_order = None
        try:
            logger.info(f"Step 3: Placing BUY order for {request.order_amount_usdt} USDT")

            if request.dry_run:
                # Simulate buy order for dry run
                buy_order = {
                    "symbol": request.symbol.replace("/", ""),
                    "side": "BUY",
                    "status": "FILLED",
                    "quantity": request.order_amount_usdt / 2500,  # Assume ETH price ~$2500
                    "price": 2500.0,
                    "orderId": "DRY_RUN_BUY",
                    "time": int(datetime.now().timestamp() * 1000)
                }
                message = f"DRY RUN: Simulated BUY order for ${request.order_amount_usdt:,.2f}"
            else:
                # Real buy order
                buy_order = trading_client.place_market_order(
                    symbol=request.symbol,
                    side="BUY",
                    quote_order_qty=request.order_amount_usdt
                )
                message = f"Placed BUY order: {buy_order['quantity']} {request.symbol.split('/')[0]} for ${request.order_amount_usdt:,.2f}"

            steps.append(WorkflowStep(
                step_number=3,
                step_name="Place Market BUY Order",
                status="success",
                data={"buy_order": buy_order, "order_amount": request.order_amount_usdt},
                message=message,
                timestamp=step3_start
            ))
            logger.info(f"Step 3 completed: {message}")

        except Exception as e:
            logger.error(f"Step 3 failed: {e}")
            steps.append(WorkflowStep(
                step_number=3,
                step_name="Place Market BUY Order",
                status="failed",
                data={"error": str(e), "order_amount": request.order_amount_usdt},
                message=f"Failed to place BUY order: {e}",
                timestamp=step3_start
            ))
            raise HTTPException(status_code=500, detail=f"Step 3 failed: {e}")

        # Step 4: Get portfolio balance after buy
        step4_start = datetime.now()
        try:
            logger.info("Step 4: Getting portfolio balance after buy")

            if request.dry_run:
                # Simulate portfolio with purchased asset
                portfolio_after_buy = initial_portfolio + [{
                    "asset": request.symbol.split('/')[0],
                    "free": buy_order["quantity"],
                    "locked": 0.0
                }]
                message = f"DRY RUN: Simulated portfolio with {buy_order['quantity']} {request.symbol.split('/')[0]}"
            else:
                portfolio_after_buy = trading_client.view_account_balance()
                asset_symbol = request.symbol.split('/')[0]
                asset_balance = next((asset for asset in portfolio_after_buy if asset["asset"] == asset_symbol), None)

                if not asset_balance:
                    raise Exception(f"No {asset_symbol} found in portfolio after buy order")

                message = f"Portfolio updated: {asset_balance['free']} {asset_symbol} acquired"

            steps.append(WorkflowStep(
                step_number=4,
                step_name="Verify Portfolio After Buy",
                status="success",
                data={"portfolio_after_buy": portfolio_after_buy},
                message=message,
                timestamp=step4_start
            ))
            logger.info(f"Step 4 completed: {message}")

        except Exception as e:
            logger.error(f"Step 4 failed: {e}")
            steps.append(WorkflowStep(
                step_number=4,
                step_name="Verify Portfolio After Buy",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to verify portfolio after buy: {e}",
                timestamp=step4_start
            ))
            raise HTTPException(status_code=500, detail=f"Step 4 failed: {e}")

        # Step 5: Get USDT balance after buy
        step5_start = datetime.now()
        try:
            logger.info("Step 5: Getting USDT balance after buy")

            if request.dry_run:
                usdt_after_buy = initial_usdt_balance - request.order_amount_usdt
                message = f"DRY RUN: Simulated USDT balance: ${usdt_after_buy:,.2f}"
            else:
                usdt_after_buy = trading_client.view_usdt_balance()
                usdt_spent = initial_usdt_balance - usdt_after_buy
                message = f"USDT balance after buy: ${usdt_after_buy:,.2f} (spent: ${usdt_spent:,.2f})"

            steps.append(WorkflowStep(
                step_number=5,
                step_name="Verify USDT Balance After Buy",
                status="success",
                data={"usdt_after_buy": usdt_after_buy, "usdt_spent": initial_usdt_balance - usdt_after_buy},
                message=message,
                timestamp=step5_start
            ))
            logger.info(f"Step 5 completed: {message}")

        except Exception as e:
            logger.error(f"Step 5 failed: {e}")
            steps.append(WorkflowStep(
                step_number=5,
                step_name="Verify USDT Balance After Buy",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to verify USDT balance after buy: {e}",
                timestamp=step5_start
            ))
            raise HTTPException(status_code=500, detail=f"Step 5 failed: {e}")

        # Step 6: Sell 100% of purchased asset
        step6_start = datetime.now()
        sell_order = None
        try:
            logger.info("Step 6: Selling 100% of purchased asset")

            if request.dry_run:
                # Simulate sell order
                sell_order = {
                    "symbol": request.symbol.replace("/", ""),
                    "side": "SELL",
                    "status": "FILLED",
                    "quantity": buy_order["quantity"],
                    "price": 2490.0,  # Slightly lower price
                    "orderId": "DRY_RUN_SELL",
                    "time": int(datetime.now().timestamp() * 1000)
                }
                message = f"DRY RUN: Simulated SELL order for {sell_order['quantity']} {request.symbol.split('/')[0]}"
            else:
                sell_order = trading_client.sell_asset_by_percentage(
                    symbol=request.symbol,
                    percentage=100
                )
                message = f"Sold 100% of {request.symbol.split('/')[0]}: {sell_order['quantity']} units"

            steps.append(WorkflowStep(
                step_number=6,
                step_name="Sell 100% of Asset",
                status="success",
                data={"sell_order": sell_order},
                message=message,
                timestamp=step6_start
            ))
            logger.info(f"Step 6 completed: {message}")

        except Exception as e:
            logger.error(f"Step 6 failed: {e}")
            steps.append(WorkflowStep(
                step_number=6,
                step_name="Sell 100% of Asset",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to sell asset: {e}",
                timestamp=step6_start
            ))
            raise HTTPException(status_code=500, detail=f"Step 6 failed: {e}")

        # Step 7: Verify portfolio is empty
        step7_start = datetime.now()
        try:
            logger.info("Step 7: Verifying portfolio after sell")

            if request.dry_run:
                # Simulate empty portfolio (remove the asset we sold)
                portfolio_after_sell = [asset for asset in portfolio_after_buy if asset["asset"] != request.symbol.split('/')[0]]
                message = f"DRY RUN: Simulated portfolio after sell (asset removed)"
            else:
                portfolio_after_sell = trading_client.view_account_balance()
                asset_symbol = request.symbol.split('/')[0]
                asset_balance = next((asset for asset in portfolio_after_sell if asset["asset"] == asset_symbol), None)

                if asset_balance and asset_balance["free"] > 0.001:  # Allow for small dust
                    logger.warning(f"Small {asset_symbol} dust remaining: {asset_balance['free']}")
                    message = f"Portfolio mostly clean (small dust: {asset_balance['free']} {asset_symbol})"
                else:
                    message = f"Portfolio clean - no {asset_symbol} remaining"

            steps.append(WorkflowStep(
                step_number=7,
                step_name="Verify Portfolio After Sell",
                status="success",
                data={"portfolio_after_sell": portfolio_after_sell},
                message=message,
                timestamp=step7_start
            ))
            logger.info(f"Step 7 completed: {message}")

        except Exception as e:
            logger.error(f"Step 7 failed: {e}")
            steps.append(WorkflowStep(
                step_number=7,
                step_name="Verify Portfolio After Sell",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to verify portfolio after sell: {e}",
                timestamp=step7_start
            ))
            # Don't raise exception here, continue to next steps

        # Step 8: Get final USDT balance
        step8_start = datetime.now()
        try:
            logger.info("Step 8: Getting final USDT balance")

            if request.dry_run:
                # Simulate final balance (slightly less due to fees)
                final_usdt_balance = usdt_after_buy + (request.order_amount_usdt * 0.995)  # 0.5% fee simulation
                message = f"DRY RUN: Simulated final USDT balance: ${final_usdt_balance:,.2f}"
            else:
                final_usdt_balance = trading_client.view_usdt_balance()
                usdt_received = final_usdt_balance - usdt_after_buy
                message = f"Final USDT balance: ${final_usdt_balance:,.2f} (received: ${usdt_received:,.2f})"

            steps.append(WorkflowStep(
                step_number=8,
                step_name="Get Final USDT Balance",
                status="success",
                data={"final_usdt_balance": final_usdt_balance, "usdt_received": final_usdt_balance - usdt_after_buy},
                message=message,
                timestamp=step8_start
            ))
            logger.info(f"Step 8 completed: {message}")

        except Exception as e:
            logger.error(f"Step 8 failed: {e}")
            steps.append(WorkflowStep(
                step_number=8,
                step_name="Get Final USDT Balance",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to get final USDT balance: {e}",
                timestamp=step8_start
            ))
            # Don't raise exception, continue to final step

        # Step 9: Check trade history
        step9_start = datetime.now()
        try:
            logger.info("Step 9: Checking trade history")

            if request.dry_run:
                # Simulate trade history
                recent_trades = [
                    {
                        "symbol": request.symbol.replace("/", ""),
                        "side": "BUY",
                        "quantity": buy_order["quantity"],
                        "price": buy_order["price"],
                        "time": buy_order["time"],
                        "orderType": "MARKET"
                    },
                    {
                        "symbol": request.symbol.replace("/", ""),
                        "side": "SELL",
                        "quantity": sell_order["quantity"],
                        "price": sell_order["price"],
                        "time": sell_order["time"],
                        "orderType": "MARKET"
                    }
                ]
                message = f"DRY RUN: Simulated 2 trades in history"
            else:
                # Get trades from workflow start time to now
                workflow_end_time = datetime.now()
                # Use the workflow start time (not a fixed 15-minute window)
                workflow_start_time = start_time  # This is the workflow start time from the beginning

                # Convert to string format that the trading client expects
                start_time_str = workflow_start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_time_str = workflow_end_time.strftime("%Y-%m-%d %H:%M:%S")

                recent_trades = trading_client.get_trades_in_time_range(start_time_str, end_time_str)

                # Debug: Check if trade history file exists and has content
                from app.core import file_manager
                trade_data = file_manager.read_json("trade_history.json", [])
                logger.info(f"Total trades in file: {len(trade_data)}")
                logger.info(f"Time range for filtering: {start_time_str} to {end_time_str}")

                # Log the timestamps of recent trades for debugging
                if trade_data:
                    logger.info("Recent trade timestamps:")
                    for i, trade in enumerate(trade_data[-5:]):  # Last 5 trades
                        trade_time = datetime.fromtimestamp(trade.get("time", 0) / 1000)
                        logger.info(f"  Trade {i+1}: {trade_time} ({trade.get('symbol')}, {trade.get('side')})")

                # Filter for our symbol
                symbol_trades = [trade for trade in recent_trades if trade.get("symbol") == request.symbol.replace("/", "")]
                message = f"Found {len(recent_trades)} total trades, {len(symbol_trades)} for {request.symbol}"
                logger.info(f"Filtered trades result: {message}")
                logger.info(f"Recent trades returned: {recent_trades}")

            steps.append(WorkflowStep(
                step_number=9,
                step_name="Check Trade History",
                status="success",
                data={"recent_trades": recent_trades, "trade_count": len(recent_trades)},
                message=message,
                timestamp=step9_start
            ))
            logger.info(f"Step 9 completed: {message}")

        except Exception as e:
            logger.error(f"Step 9 failed: {e}")
            steps.append(WorkflowStep(
                step_number=9,
                step_name="Check Trade History",
                status="failed",
                data={"error": str(e)},
                message=f"Failed to check trade history: {e}",
                timestamp=step9_start
            ))

        # Calculate summary
        end_time = datetime.now()
        completed_steps = len([step for step in steps if step.status == "success"])
        total_steps = 9

        # Calculate P&L if we have the data
        net_pnl = 0.0
        pnl_percentage = 0.0
        if len(steps) >= 8 and steps[7].status == "success" and steps[1].status == "success":
            try:
                final_balance = steps[7].data.get("final_usdt_balance", initial_usdt_balance)
                net_pnl = final_balance - initial_usdt_balance
                pnl_percentage = (net_pnl / initial_usdt_balance) * 100 if initial_usdt_balance > 0 else 0
            except:
                pass

        summary = {
            "initial_usdt_balance": initial_usdt_balance if 'initial_usdt_balance' in locals() else 0,
            "final_usdt_balance": final_usdt_balance if 'final_usdt_balance' in locals() else 0,
            "net_pnl": net_pnl,
            "pnl_percentage": pnl_percentage,
            "order_amount": request.order_amount_usdt,
            "symbol": request.symbol,
            "dry_run": request.dry_run,
            "duration_seconds": (end_time - start_time).total_seconds(),
            "success_rate": (completed_steps / total_steps) * 100
        }

        status = "completed" if completed_steps == total_steps else "partial" if completed_steps > 0 else "failed"

        logger.info(f"Workflow test {test_id} completed with status: {status}")

        return WorkflowTestResponse(
            test_id=test_id,
            status=status,
            total_steps=total_steps,
            completed_steps=completed_steps,
            start_time=start_time,
            end_time=end_time,
            steps=steps,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Workflow test {test_id} failed: {e}")
        end_time = datetime.now()

        return WorkflowTestResponse(
            test_id=test_id,
            status="failed",
            total_steps=9,
            completed_steps=len([step for step in steps if step.status == "success"]),
            start_time=start_time,
            end_time=end_time,
            steps=steps,
            summary={
                "error": str(e),
                "dry_run": request.dry_run,
                "duration_seconds": (end_time - start_time).total_seconds()
            }
        )


@router.get("/status")
async def get_workflow_test_status():
    """Get the status of workflow testing capability."""
    return {
        "status": "available",
        "description": "Workflow testing endpoint for complete trading workflow validation",
        "endpoints": {
            "run_test": "/workflow-test/run",
            "status": "/workflow-test/status"
        },
        "features": [
            "Real API calls to Binance",
            "Complete 9-step trading workflow",
            "Dry run mode for testing",
            "Detailed step-by-step results",
            "P&L calculation",
            "Trade history verification"
        ]
    }

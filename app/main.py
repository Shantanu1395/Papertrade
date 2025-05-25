from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routers import account, market, orders, trades, workflow_test

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create FastAPI app
app = FastAPI(
    title="Paper Trading API",
    description="API for paper trading on cryptocurrency exchanges",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(account.router)
app.include_router(market.router)
app.include_router(orders.router)
app.include_router(trades.router)
app.include_router(workflow_test.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Paper Trading API"}
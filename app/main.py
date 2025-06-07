"""
Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core import settings
from app.routers import account, market, orders, trades, workflow_test, enhanced_portfolio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Include routers
app.include_router(account.router)
app.include_router(market.router)
app.include_router(orders.router)
app.include_router(trades.router)
app.include_router(workflow_test.router)
app.include_router(enhanced_portfolio.router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Paper Trading API"}
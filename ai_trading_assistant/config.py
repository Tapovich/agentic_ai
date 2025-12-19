"""
Configuration File
Contains all configuration settings for the application,
including database connection parameters.
"""

# ============================================
# DATABASE CONFIGURATION
# ============================================

# MySQL Database Host (usually 'localhost' for local development)
DB_HOST = 'localhost'

# MySQL Database Username
DB_USER = 'root'

# MySQL Database Password (set your MySQL password here)
DB_PASSWORD = 'your_password_here'

# Database Name (the name of your MySQL database)
DB_NAME = 'ai_trading_db'

# Database Port (default MySQL port is 3306)
DB_PORT = 3306


# ============================================
# APPLICATION CONFIGURATION
# ============================================

# Secret key for Flask sessions (change this to a random string in production)
SECRET_KEY = 'your-secret-key-change-this-in-production'

# Initial virtual balance for new users (in USD)
INITIAL_BALANCE = 10000.0

# Debug mode (set to False in production)
DEBUG = True

# ============================================
# LIVE TRADING CONFIGURATION
# ============================================

# Live Trading Mode (VERY IMPORTANT!)
# When False: Orders are SIMULATED (safe, no real money)
# When True: Orders are sent to REAL exchanges (financial risk!)
#
# For University Project:
# - Keep this FALSE for demonstration and safety
# - Show that it works in simulation mode
# - Explain what would happen if True
#
# In Production:
# - Only enable after extensive testing
# - Use testnet first
# - Implement additional safety checks
# - Add confirmation prompts
# - Log all live trades
LIVE_TRADING_ENABLED = False

# Require confirmation for live trades (additional safety)
REQUIRE_TRADE_CONFIRMATION = True


# ============================================
# MARKET DATA API CONFIGURATION (TASK 36)
# ============================================

# CoinMarketCap API Configuration
# --------------------------------
# CoinMarketCap provides cryptocurrency market data (prices, market caps, volume, etc.)
# 
# How to get API key:
# 1. Go to https://coinmarketcap.com/api/
# 2. Sign up for free account
# 3. Get your API key
# 4. Free tier: 10,000 API calls per month (plenty for demo/university project)
#
# Security Best Practice:
# - In production, read from environment variable: os.environ.get('CMC_API_KEY')
# - Never commit real API keys to Git
# - Add .env file to .gitignore
#
# For University Projects:
# - You can use demo/sandbox mode
# - Or leave as placeholder - service will return demo data
# - Explain to professor: "In production, this would use real API key"

import os

# CoinMarketCap API Key
# Set via environment variable: export CMC_API_KEY="your-key-here"
# Or replace 'YOUR_API_KEY_HERE' with your actual key (not recommended for production)
CMC_API_KEY = os.environ.get('CMC_API_KEY', '1d903b5d08d540aa8e7c8d8e36e68106')

# CoinMarketCap API Base URL
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


# Fear & Greed Index API Configuration
# ------------------------------------
# Alternative.me provides a FREE Crypto Fear & Greed Index
# No API key needed - completely free to use
# 
# What is Fear & Greed Index?
# - Measures market sentiment on a 0-100 scale
# - 0-24: Extreme Fear (potential buying opportunity)
# - 25-49: Fear (market cautious)  
# - 50-74: Greed (market bullish)
# - 75-100: Extreme Greed (potential selling opportunity)
#
# Used by traders as a contrarian indicator:
# - When everyone is fearful, it might be a good time to buy
# - When everyone is greedy, it might be a good time to sell
#
# Updates: Daily
# Rate Limit: ~100 requests per minute (very generous)

# Fear & Greed API URL (FREE - no key needed)
FEAR_GREED_API_URL = "https://api.alternative.me/fng/"


# API Request Timeout (seconds)
# How long to wait for API response before giving up
API_TIMEOUT = 10


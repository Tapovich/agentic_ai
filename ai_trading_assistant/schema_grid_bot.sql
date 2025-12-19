-- ============================================
-- GRID BOT TABLES
-- ============================================
-- Grid trading is an automated trading strategy that:
-- 1. Divides a price range into multiple "grid levels"
-- 2. Places buy orders at lower levels
-- 3. Places sell orders at upper levels
-- 4. Profits from price fluctuations within the range

-- ============================================
-- TABLE: grid_bots
-- ============================================
-- Purpose: Stores grid bot configurations
-- Each bot represents one automated trading strategy
CREATE TABLE grid_bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,                    -- Cryptocurrency symbol (e.g., "BTCUSDT")
    lower_price REAL NOT NULL,               -- Bottom of price range
    upper_price REAL NOT NULL,               -- Top of price range
    grid_count INTEGER NOT NULL,             -- Number of grid levels
    investment_amount REAL NOT NULL,         -- Total virtual capital assigned to this bot
    is_active INTEGER DEFAULT 1,             -- 1 = active, 0 = stopped
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index for faster queries
CREATE INDEX idx_grid_bots_user ON grid_bots(user_id);
CREATE INDEX idx_grid_bots_active ON grid_bots(is_active);

-- ============================================
-- TABLE: grid_levels
-- ============================================
-- Purpose: Stores individual grid levels for each bot
-- Each level represents a price point where the bot will buy or sell
CREATE TABLE grid_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id INTEGER NOT NULL,
    level_price REAL NOT NULL,               -- Price at this grid level
    order_type TEXT NOT NULL CHECK(order_type IN ('BUY', 'SELL')),  -- BUY or SELL
    is_filled INTEGER DEFAULT 0,             -- 0 = pending, 1 = executed
    filled_at TIMESTAMP,                     -- When the order was filled
    FOREIGN KEY (bot_id) REFERENCES grid_bots(id) ON DELETE CASCADE
);

-- Create index for faster queries
CREATE INDEX idx_grid_levels_bot ON grid_levels(bot_id);
CREATE INDEX idx_grid_levels_filled ON grid_levels(is_filled);

-- ============================================
-- EXPLANATION OF GRID TRADING
-- ============================================
/*
What is Grid Trading?
---------------------
Grid trading is an automated strategy that profits from market volatility:

Example:
- Symbol: BTCUSDT (Bitcoin)
- Price Range: $40,000 (lower) to $50,000 (upper)
- Grid Count: 5 levels
- Investment: $1,000

The bot creates 5 evenly-spaced levels:
Level 1: $40,000 - BUY order
Level 2: $42,500 - BUY order
Level 3: $45,000 - SELL order
Level 4: $47,500 - SELL order
Level 5: $50,000 - SELL order

How It Works:
1. When price drops to $40,000 → bot buys
2. When price rises to $45,000 → bot sells (profit!)
3. When price drops to $42,500 → bot buys again
4. Repeat as price fluctuates

Benefits:
- Automated trading (no manual intervention)
- Profits from volatility (price ups and downs)
- Dollar-cost averaging effect
- Works in sideways markets

Risks (in real trading):
- Price may break out of range
- Capital gets stuck
- Requires sufficient balance

In this implementation:
- Paper trading only (virtual money)
- Educational purpose
- Demonstrates algorithmic trading concepts
*/


-- ============================================
-- EXCHANGE ACCOUNTS & TRADE LOGS SCHEMA
-- ============================================
-- These tables enable users to link their real cryptocurrency exchange accounts
-- and track all trades executed through those exchanges.

-- Use Case:
-- 1. User adds their Binance API key
-- 2. AI Trading Assistant can execute real trades on their behalf
-- 3. All trades are logged for transparency and auditing
-- 4. User can link multiple exchanges (Binance, Bybit, OKX, etc.)

-- ============================================
-- TABLE: exchange_accounts
-- ============================================
-- Purpose: Store linked exchange accounts for each user
-- 
-- What this table does:
-- - Allows users to connect their real exchange accounts
-- - Stores API credentials (key and secret)
-- - Supports multiple exchanges per user
-- - Enables automated trading on real exchanges
-- - Distinguishes between testnet (safe) and live accounts
--
-- Security Note:
-- ⚠️ In this educational project, api_secret is stored as plain text
-- ⚠️ In REAL PRODUCTION, you must:
--    - Encrypt the api_secret before storing
--    - Use strong encryption (AES-256 or better)
--    - Store encryption keys separately (HSM, KMS, etc.)
--    - Never log or display API secrets
--    - Use environment variables, not database
--
-- Example Row:
-- user_id=1, exchange_name="binance", account_label="My Main Account",
-- api_key="ABC123...", api_secret_encrypted="XYZ789...", is_testnet=0

CREATE TABLE exchange_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    -- Exchange identifier (must match ccxt exchange names)
    -- Supported: "binance", "bybit", "okx", "mexc", "bingx"
    exchange_name TEXT NOT NULL CHECK(exchange_name IN ('binance', 'bybit', 'okx', 'mexc', 'bingx')),
    
    -- User-friendly label for this account
    -- Example: "My Binance Main", "Bybit Futures Account", etc.
    account_label TEXT DEFAULT 'My Account',
    
    -- API Key from the exchange
    -- This is public (safe to expose in some contexts)
    api_key TEXT NOT NULL,
    
    -- API Secret - MUST BE ENCRYPTED in production!
    -- ⚠️ SECURITY WARNING:
    -- In this university project, storing plain text for simplicity
    -- In real production:
    --   - NEVER store plain text secrets
    --   - Use encryption (AES-256, Fernet, etc.)
    --   - Store in secure vault (AWS KMS, HashiCorp Vault)
    --   - Encrypt before INSERT, decrypt on SELECT
    api_secret_encrypted TEXT NOT NULL,
    
    -- Is this a testnet/sandbox account?
    -- 1 = testnet (fake money, safe for testing)
    -- 0 = live production (real money, real risk)
    is_testnet INTEGER DEFAULT 0 CHECK(is_testnet IN (0, 1)),
    
    -- Is this account currently active?
    -- User can deactivate without deleting
    -- 1 = active (can trade), 0 = inactive (disabled)
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    
    -- When this account was linked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Last time account was used
    last_used_at TIMESTAMP,
    
    -- Foreign key: links to users table
    -- CASCADE: if user is deleted, their exchange accounts are also deleted
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX idx_exchange_accounts_user ON exchange_accounts(user_id);
CREATE INDEX idx_exchange_accounts_active ON exchange_accounts(is_active);
CREATE INDEX idx_exchange_accounts_exchange ON exchange_accounts(exchange_name);

-- ============================================
-- TABLE: exchange_trade_logs
-- ============================================
-- Purpose: Log every trade attempted/executed through real exchanges
--
-- What this table does:
-- - Records all trades sent to real exchanges
-- - Tracks success/failure of each trade
-- - Stores exchange response for debugging
-- - Enables trade history and auditing
-- - Links trades to specific exchange accounts
-- - Can be triggered by: AI predictions, grid bots, manual trades, etc.
--
-- Trade Lifecycle:
-- 1. User/Bot initiates trade
-- 2. System sends order to exchange via API
-- 3. Exchange responds with order details
-- 4. Response logged in this table
-- 5. Status tracked: NEW → FILLED or REJECTED
--
-- Example Row:
-- user_id=1, exchange_account_id=1, symbol="BTCUSDT", side="BUY",
-- amount=0.1, price=45000, status="FILLED"

CREATE TABLE exchange_trade_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    
    -- Which exchange account was used for this trade
    exchange_account_id INTEGER NOT NULL,
    
    -- Trading pair symbol (e.g., "BTCUSDT", "ETHUSDT")
    symbol TEXT NOT NULL,
    
    -- Trade direction
    -- BUY = long/buying the asset
    -- SELL = short/selling the asset
    side TEXT NOT NULL CHECK(side IN ('BUY', 'SELL')),
    
    -- Amount of cryptocurrency traded
    -- Example: 0.1 BTC, 1.5 ETH
    amount REAL NOT NULL CHECK(amount > 0),
    
    -- Price per unit when trade was executed
    -- For market orders, this is the filled price
    -- For limit orders, this is the order price
    price REAL NOT NULL CHECK(price > 0),
    
    -- Total cost/value of the trade
    -- = amount × price
    total_value REAL,
    
    -- Order status from exchange
    -- Common statuses:
    --   "NEW" = order created, not yet filled
    --   "FILLED" = order completely executed
    --   "PARTIALLY_FILLED" = partially executed
    --   "CANCELED" = order canceled
    --   "REJECTED" = exchange rejected the order
    --   "EXPIRED" = order expired
    --   "ERROR" = API error occurred
    status TEXT DEFAULT 'NEW',
    
    -- Order ID from the exchange
    -- Used to track the order on the exchange
    exchange_order_id TEXT,
    
    -- Commission/fee paid for this trade
    -- Example: 0.001 BTC (0.1% fee)
    fee REAL DEFAULT 0,
    
    -- Fee currency (e.g., "BNB", "USDT")
    fee_currency TEXT,
    
    -- Raw JSON response from exchange API
    -- Stores complete response for debugging and auditing
    -- Example: {"orderId": "123", "status": "FILLED", ...}
    -- Useful for:
    --   - Debugging failed trades
    --   - Audit trail
    --   - Regulatory compliance
    --   - Dispute resolution
    raw_response TEXT,
    
    -- Error message if trade failed
    -- Example: "Insufficient balance", "Invalid symbol", etc.
    error_message TEXT,
    
    -- Trade source (who/what initiated this trade)
    -- Examples: "manual", "ai_prediction", "grid_bot", "dca_bot"
    trade_source TEXT DEFAULT 'manual',
    
    -- When this trade was created/attempted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- When order was filled (if applicable)
    filled_at TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exchange_account_id) REFERENCES exchange_accounts(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX idx_exchange_trade_logs_user ON exchange_trade_logs(user_id);
CREATE INDEX idx_exchange_trade_logs_account ON exchange_trade_logs(exchange_account_id);
CREATE INDEX idx_exchange_trade_logs_symbol ON exchange_trade_logs(symbol);
CREATE INDEX idx_exchange_trade_logs_status ON exchange_trade_logs(status);
CREATE INDEX idx_exchange_trade_logs_created ON exchange_trade_logs(created_at);

-- ============================================
-- EXPLANATION FOR STUDENTS
-- ============================================

/*
WHY THESE TABLES?
-----------------

Table 1: exchange_accounts
--------------------------
Imagine you have accounts on multiple exchanges (Binance, Bybit, OKX).
This table stores the API keys so our platform can:
- Check your balances
- Place trades on your behalf
- Fetch your positions
- Execute automated strategies (grid bots, AI trading)

Each user can link multiple accounts, and each account needs:
- Exchange name (which platform)
- API credentials (key + secret)
- Testnet flag (safe mode vs real money)
- Active status (can be disabled without deleting)

Table 2: exchange_trade_logs
-----------------------------
Every time a trade is executed on a real exchange, we log it here.
This provides:
- Complete trade history
- Audit trail (what was traded, when, why)
- Success/failure tracking
- Debugging information (raw response from exchange)
- Regulatory compliance (prove all trades)
- Performance analysis

Example Scenario:
----------------
1. User links their Binance account (row in exchange_accounts)
2. AI predicts "BUY" signal for Bitcoin
3. System sends buy order to Binance via API
4. Binance executes trade and responds
5. Trade logged in exchange_trade_logs with full details
6. User can see trade history and performance

Security Considerations:
-----------------------
API Secret Storage:
- ⚠️ Plain text in this project (educational)
- ✅ In production: Must encrypt with AES-256 or similar
- ✅ Use key management service (AWS KMS, HashiCorp Vault)
- ✅ Never log or display secrets
- ✅ Set API key permissions (read-only if only fetching data)

Data Protection:
- ✅ Foreign key CASCADE: deleting user removes their accounts
- ✅ Indexes for performance
- ✅ Status tracking for order lifecycle
- ✅ Raw response storage for debugging

Trade Source Tracking:
----------------------
The 'trade_source' field identifies what triggered each trade:
- "manual" = user clicked buy/sell manually
- "ai_prediction" = AI model recommended the trade
- "grid_bot" = grid trading bot executed
- "dca_bot" = dollar-cost averaging bot
- "stop_loss" = automatic stop loss triggered
- "take_profit" = take profit order

This helps analyze which strategy performs best!

Benefits:
---------
1. Multi-Exchange Support: Trade on multiple platforms from one dashboard
2. Automation: Bots can execute real trades
3. Transparency: Complete trade history
4. Security: Can disable accounts without deleting
5. Flexibility: Testnet for testing, live for real trading
6. Auditing: Full trail of all trades
7. Analysis: Track performance by source

Risks (In Real Trading):
------------------------
1. API keys can be stolen if not encrypted
2. Losing API secret means losing account access
3. Wrong configuration can lead to losses
4. Exchange hacks/downtime
5. Regulatory compliance requirements

For University Project:
----------------------
- Focus on the architecture and design
- Demonstrate understanding of real-world systems
- Show security awareness (even if simplified)
- Explain what would be different in production
*/

-- ============================================
-- SAMPLE QUERIES (For Reference)
-- ============================================

/*
-- Add an exchange account:
INSERT INTO exchange_accounts (user_id, exchange_name, account_label, api_key, api_secret_encrypted, is_testnet)
VALUES (1, 'binance', 'My Binance Testnet', 'test_api_key', 'encrypted_secret_here', 1);

-- Get all active accounts for a user:
SELECT * FROM exchange_accounts 
WHERE user_id = 1 AND is_active = 1;

-- Log a trade:
INSERT INTO exchange_trade_logs (user_id, exchange_account_id, symbol, side, amount, price, status, trade_source)
VALUES (1, 1, 'BTCUSDT', 'BUY', 0.1, 45000.00, 'FILLED', 'grid_bot');

-- Get user's trade history:
SELECT * FROM exchange_trade_logs 
WHERE user_id = 1 
ORDER BY created_at DESC 
LIMIT 50;

-- Get all successful trades:
SELECT * FROM exchange_trade_logs 
WHERE status = 'FILLED' 
ORDER BY created_at DESC;

-- Calculate total traded volume:
SELECT 
    symbol,
    side,
    COUNT(*) as trade_count,
    SUM(amount) as total_amount,
    AVG(price) as avg_price
FROM exchange_trade_logs
WHERE user_id = 1 AND status = 'FILLED'
GROUP BY symbol, side;
*/


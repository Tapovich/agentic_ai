-- ============================================
-- DCA BOT TABLE
-- ============================================
-- DCA (Dollar-Cost Averaging) is an investment strategy where you:
-- - Buy a fixed amount of an asset at regular intervals
-- - Regardless of the price
-- - Averages out the purchase price over time
-- - Reduces impact of volatility

-- Example:
-- Instead of buying $1000 of Bitcoin all at once,
-- You buy $100 every week for 10 weeks.
-- This way, you buy more when price is low, less when price is high.
-- Your average purchase price is smoothed out.

-- Benefits:
-- - Removes emotion from investing (no timing the market)
-- - Reduces risk of buying at a peak
-- - Works well for long-term investing
-- - Simple and disciplined approach

-- ============================================
-- TABLE: dca_bots
-- ============================================
-- Purpose: Store DCA bot configurations
-- Each bot represents a recurring buy strategy

CREATE TABLE dca_bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- User who owns this DCA bot
    user_id INTEGER NOT NULL,
    
    -- Which exchange account to use for buying
    exchange_account_id INTEGER NOT NULL,
    
    -- Which cryptocurrency to buy
    -- Example: "BTCUSDT", "ETHUSDT"
    symbol TEXT NOT NULL,
    
    -- How much to buy each time (in base currency)
    -- Example: 0.01 BTC, 0.5 ETH
    -- For USDT-quoted pairs, this could also be the USDT amount
    buy_amount REAL NOT NULL CHECK(buy_amount > 0),
    
    -- How often to buy (for display only, not enforced)
    -- Examples: "Daily", "Weekly", "Bi-weekly", "Monthly"
    -- In a real system, this would trigger automatic execution
    -- For this project, manual execution for demonstration
    interval_description TEXT DEFAULT 'Weekly',
    
    -- Is this bot active?
    -- 1 = active (can run)
    -- 0 = stopped (won't run)
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    
    -- When bot was created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Last time bot was executed (run manually or auto)
    last_run_at TIMESTAMP,
    
    -- Total number of times bot has executed
    execution_count INTEGER DEFAULT 0,
    
    -- Foreign keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exchange_account_id) REFERENCES exchange_accounts(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_dca_bots_user ON dca_bots(user_id);
CREATE INDEX idx_dca_bots_active ON dca_bots(is_active);
CREATE INDEX idx_dca_bots_exchange ON dca_bots(exchange_account_id);

-- ============================================
-- EXPLANATION FOR STUDENTS
-- ============================================

/*
WHY DCA (Dollar-Cost Averaging)?
--------------------------------

Problem: Market timing is hard!
- Buy at the peak? Lose money when price drops.
- Wait for a dip? Miss out if price keeps rising.
- Emotional decisions? Often wrong.

Solution: DCA removes guesswork!
- Buy fixed amount regularly
- Don't try to time the market
- Average out the price
- Stay disciplined

Real Example:
------------
Scenario: You want to invest $1,000 in Bitcoin

Option 1: Lump sum (all at once)
- Buy $1,000 of BTC today
- If price = $50,000, you get 0.02 BTC
- If price drops to $40,000 next week, you lost $200
- Risky!

Option 2: DCA (spread over time)
- Week 1: Buy $100 @ $50,000 = 0.002 BTC
- Week 2: Buy $100 @ $48,000 = 0.00208 BTC  
- Week 3: Buy $100 @ $45,000 = 0.00222 BTC
- Week 4: Buy $100 @ $42,000 = 0.00238 BTC
- ...and so on
- Total: More BTC because you bought more when price was low!
- Average price: Better than lump sum
- Less risky!

How This Table Works:
--------------------
1. User creates DCA bot:
   - Symbol: BTCUSDT
   - Buy Amount: 0.01 BTC
   - Interval: "Weekly"
   
2. Bot configuration stored in this table

3. Execution (in production):
   - Automated: Runs every week via cron job
   - Our demo: Manual "Run Once" button
   
4. Each execution:
   - Buys 0.01 BTC at current price
   - Logs trade in exchange_trade_logs
   - Updates last_run_at
   - Increments execution_count

5. Over time:
   - User accumulates Bitcoin
   - Average price smooths out
   - Less volatile than lump sum

In This University Project:
--------------------------
- Manual execution (no cron needed)
- "Run Once" button for demonstration
- Shows the concept clearly
- Easy to explain in presentation

In Production:
-------------
- Automated execution (cron job, scheduler)
- Runs at specified intervals
- Email notifications
- Can pause/resume
- Performance tracking
*/

-- ============================================
-- SAMPLE QUERIES
-- ============================================

/*
-- Create a DCA bot:
INSERT INTO dca_bots (user_id, exchange_account_id, symbol, buy_amount, interval_description)
VALUES (1, 1, 'BTCUSDT', 0.01, 'Weekly');

-- Get user's DCA bots:
SELECT * FROM dca_bots WHERE user_id = 1 AND is_active = 1;

-- Update last run:
UPDATE dca_bots 
SET last_run_at = datetime('now'), execution_count = execution_count + 1 
WHERE id = 1;

-- Stop a DCA bot:
UPDATE dca_bots SET is_active = 0 WHERE id = 1;

-- Get execution history (from trade logs):
SELECT * FROM exchange_trade_logs 
WHERE trade_source LIKE 'dca_bot_%' 
ORDER BY created_at DESC;
*/


-- ============================================
-- MIGRATION 004: Upgrade DCA Bots to Binance-Style Configuration
-- ============================================
-- 
-- This migration adds advanced configuration options to the dca_bots table
-- to support Binance-style Spot DCA (Dollar Cost Averaging) features.
--
-- Binance Spot DCA Features:
-- - Base Order & DCA Order sizing
-- - Price deviation between orders
-- - Take Profit with configurable types
-- - Side selection (BUY/SELL)
-- - Max DCA orders limit
-- - Advanced multipliers for progressive scaling
-- - Trigger price for entry timing
-- - Cooldown between trading rounds
-- - Price range constraints
-- - Stop Loss protection
--
-- Educational Purpose:
-- This demonstrates professional DCA trading configuration options
-- used by major exchanges like Binance, suitable for university projects.
--
-- Date: 2025-11-13
-- Author: AI Trading Assistant Team
-- ============================================

-- Add new columns to dca_bots table
-- These columns enhance the basic DCA bot with Binance-style features

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS side VARCHAR(4) DEFAULT 'BUY'
    COMMENT 'Trading side: BUY (long DCA) or SELL (short DCA)';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS price_deviation_pct FLOAT DEFAULT 1.0
    COMMENT 'Price deviation % between DCA orders. Example: 1.0 = place orders 1% apart';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS take_profit_pct FLOAT DEFAULT NULL
    COMMENT 'Take profit target in %. Bot closes all positions when reached.';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS take_profit_type VARCHAR(10) DEFAULT 'FIX'
    COMMENT 'Take profit calculation type: FIX (fixed %), TRAIL (trailing)';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS base_order_size DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Size of the first (base) order in quote currency';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS dca_order_size DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Size of each subsequent DCA order in quote currency';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS max_dca_orders INT DEFAULT 5
    COMMENT 'Maximum number of DCA orders to place (safety limit)';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS trigger_price DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Bot activates only when market reaches this price. NULL = immediate activation.';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS price_deviation_multiplier FLOAT DEFAULT NULL
    COMMENT 'Multiplier for price deviation. Each order: deviation = base_deviation * (multiplier ^ order_num)';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS dca_order_size_multiplier FLOAT DEFAULT NULL
    COMMENT 'Multiplier for order size. Each order: size = base_size * (multiplier ^ order_num)';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS cooldown_seconds INT DEFAULT NULL
    COMMENT 'Minimum seconds between DCA rounds. Prevents over-trading.';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS range_lower DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Lower price bound for DCA range. Bot only trades above this price.';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS range_upper DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Upper price bound for DCA range. Bot only trades below this price.';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS stop_loss_pct FLOAT DEFAULT NULL
    COMMENT 'Stop loss % from average entry. Bot closes all positions if reached.';

ALTER TABLE dca_bots ADD COLUMN IF NOT EXISTS end_on_stop TINYINT DEFAULT 0
    COMMENT '1 = end bot permanently when stop loss triggers, 0 = pause and wait for manual restart';

-- ============================================
-- NOTES FOR DEVELOPERS
-- ============================================
--
-- DCA Trading Explained:
-- ----------------------
-- Dollar Cost Averaging (DCA) is an investment strategy where you:
-- 1. Make regular purchases of an asset
-- 2. Average down your entry price when price drops
-- 3. Take profit when price rises above your average
--
-- Example:
-- - Base order: Buy $100 BTC at $50,000 (0.002 BTC)
-- - Price drops 2% to $49,000
-- - DCA order 1: Buy $100 at $49,000 (0.00204 BTC)
-- - Average price: $49,500
-- - Total: 0.00404 BTC for $200
-- - If price rises to $51,000 → 3% profit, close position
--
-- Side Selection:
-- ---------------
-- BUY (Long DCA):
-- - Buy base order at current price
-- - Buy more (DCA) when price drops
-- - Take profit when price rises
-- - Use case: Bull market, expect long-term growth
--
-- SELL (Short DCA):
-- - Sell base order at current price
-- - Sell more (DCA) when price rises
-- - Take profit when price drops
-- - Use case: Bear market, shorting overvalued assets
--
-- Price Deviation:
-- ----------------
-- Controls spacing between DCA orders
-- - 1% deviation: Orders at -1%, -2%, -3% from base
-- - 2% deviation: Orders at -2%, -4%, -6% from base
-- - Higher deviation = wider safety net, fewer triggers
-- - Lower deviation = tighter spacing, more triggers
--
-- Price Deviation Multiplier:
-- ---------------------------
-- Makes spacing exponential instead of linear
-- - Multiplier = 1.0: Linear (1%, 2%, 3%, 4%)
-- - Multiplier = 1.5: Exponential (1%, 2.5%, 5%, 10%)
-- - Use case: Hedge against extreme volatility
--
-- Base Order vs DCA Order Size:
-- -----------------------------
-- Base Order: First entry into position
-- DCA Orders: Additional entries to average down
--
-- Strategy 1: Equal sizing
-- - Base: $100, DCA: $100
-- - Risk: Limited averaging power
--
-- Strategy 2: Increasing sizing
-- - Base: $50, DCA: $100
-- - Risk: More capital at lower prices
-- - Better averaging at the cost of higher exposure
--
-- DCA Order Size Multiplier:
-- --------------------------
-- Progressive position sizing
-- - Multiplier = 1.0: Fixed size ($100, $100, $100)
-- - Multiplier = 1.5: Growing ($100, $150, $225)
-- - Multiplier = 0.8: Shrinking ($100, $80, $64)
--
-- Growing (>1.0): Aggressive averaging
-- Shrinking (<1.0): Conservative risk management
--
-- Max DCA Orders:
-- ---------------
-- Safety limit to prevent infinite averaging
-- - Too few (3-5): May not catch the bottom
-- - Too many (20+): Excessive capital deployment
-- - Typical: 5-10 orders
--
-- Take Profit:
-- -----------
-- Automatically close position at profit target
-- - Fixed TP: Close at X% above average entry
-- - Example: 5% TP on $50,000 avg = close at $52,500
-- - Trailing TP: Follow price upward (future feature)
--
-- Trigger Price:
-- -------------
-- Wait for optimal entry
-- - Current BTC: $52,000
-- - Trigger: $48,000
-- - Bot waits in standby until price drops to $48k
-- - Then activates and starts DCA strategy
-- - Use case: "Buy the dip" strategies
--
-- Cooldown:
-- --------
-- Prevent rapid trading in volatile markets
-- - Cooldown = 300 seconds (5 minutes)
-- - After each DCA round, wait 5 min before next
-- - Reduces transaction costs, prevents panic trading
--
-- Price Range:
-- -----------
-- Define operating boundaries
-- - Range: $45,000 - $55,000
-- - Bot only trades within this range
-- - Below $45k: Stop (too risky)
-- - Above $55k: Stop (overbought)
-- - Use case: Range-bound trading strategies
--
-- Stop Loss:
-- ---------
-- Risk management protection
-- - Stop Loss: -10% from average entry
-- - If avg entry = $50,000, SL = $45,000
-- - When triggered:
--   - end_on_stop = 1: Close bot permanently
--   - end_on_stop = 0: Pause bot, keep positions
--
-- ============================================
-- EXAMPLE CONFIGURATIONS
-- ============================================
--
-- Conservative DCA (Low Risk):
-- - Side: BUY
-- - Base Order: $50
-- - DCA Order: $50
-- - Max Orders: 5
-- - Price Deviation: 2%
-- - Take Profit: 5%
-- - Stop Loss: -8%
--
-- Aggressive DCA (High Risk):
-- - Side: BUY
-- - Base Order: $100
-- - DCA Order: $200 (size multiplier: 2.0)
-- - Max Orders: 10
-- - Price Deviation: 1% (deviation multiplier: 1.3)
-- - Take Profit: 15%
-- - Stop Loss: -15%
--
-- "Buy the Dip" Strategy:
-- - Side: BUY
-- - Trigger Price: 10% below current
-- - Base Order: $100
-- - DCA Order: $100
-- - Max Orders: 7
-- - Price Deviation: 1.5%
-- - Take Profit: 10%
-- - Range: Support to Resistance levels
--
-- Range Trading:
-- - Side: BUY
-- - Range: $45k - $55k
-- - Base Order: $200
-- - DCA Order: $150
-- - Max Orders: 5
-- - Price Deviation: 2%
-- - Take Profit: 3%
-- - Cooldown: 600s (10 min)
--
-- ============================================
-- MIGRATION ROLLBACK (if needed)
-- ============================================
--
-- To rollback this migration:
-- ALTER TABLE dca_bots DROP COLUMN side;
-- ALTER TABLE dca_bots DROP COLUMN price_deviation_pct;
-- ALTER TABLE dca_bots DROP COLUMN take_profit_pct;
-- ALTER TABLE dca_bots DROP COLUMN take_profit_type;
-- ALTER TABLE dca_bots DROP COLUMN base_order_size;
-- ALTER TABLE dca_bots DROP COLUMN dca_order_size;
-- ALTER TABLE dca_bots DROP COLUMN max_dca_orders;
-- ALTER TABLE dca_bots DROP COLUMN trigger_price;
-- ALTER TABLE dca_bots DROP COLUMN price_deviation_multiplier;
-- ALTER TABLE dca_bots DROP COLUMN dca_order_size_multiplier;
-- ALTER TABLE dca_bots DROP COLUMN cooldown_seconds;
-- ALTER TABLE dca_bots DROP COLUMN range_lower;
-- ALTER TABLE dca_bots DROP COLUMN range_upper;
-- ALTER TABLE dca_bots DROP COLUMN stop_loss_pct;
-- ALTER TABLE dca_bots DROP COLUMN end_on_stop;
--
-- ============================================

-- Verify migration
SELECT 
    'Migration 004 completed successfully. DCA bots table now supports Binance-style configuration.' as status;


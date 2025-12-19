-- ============================================
-- MIGRATION 003: Upgrade Grid Bots to Binance-Style Configuration
-- ============================================
-- 
-- This migration adds advanced configuration options to the grid_bots table
-- to support Binance-style Spot Grid trading features.
--
-- Binance Spot Grid Features:
-- - Price range (lower/upper)
-- - Grid type (Arithmetic/Geometric)
-- - Investment amount and quote currency
-- - Trailing Up (follow price upward)
-- - Grid Trigger Price (activate grid at specific price)
-- - Take Profit % (auto-close at profit target)
-- - Stop Loss Price (auto-close at loss limit)
-- - Sell All on Stop (liquidate entire position on stop)
--
-- Educational Purpose:
-- This demonstrates professional grid trading configuration options
-- used by major exchanges like Binance, suitable for university projects.
--
-- Date: 2025-11-13
-- Author: AI Trading Assistant Team
-- ============================================

-- Add new columns to grid_bots table
-- These columns enhance the basic grid bot with Binance-style features

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS grid_lower_price DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Lower price boundary of the grid range';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS grid_upper_price DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Upper price boundary of the grid range';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS grid_type VARCHAR(20) DEFAULT 'ARITHMETIC'
    COMMENT 'Grid calculation type: ARITHMETIC (equal price intervals) or GEOMETRIC (equal percentage intervals)';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS investment_amount DECIMAL(20, 8) DEFAULT 0
    COMMENT 'Total investment amount allocated to this grid bot';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS quote_currency VARCHAR(10) DEFAULT 'USDT'
    COMMENT 'Quote currency for the trading pair (e.g., USDT, BTC, ETH)';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS trailing_up TINYINT DEFAULT 0
    COMMENT 'Trailing Up: 1 = grid follows price upward, 0 = fixed range. Binance feature for bull markets.';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS grid_trigger_price DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Grid Trigger Price: Grid bot activates only when market reaches this price. NULL = immediate activation.';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS take_profit_pct FLOAT DEFAULT NULL
    COMMENT 'Take Profit %: Auto-close grid when total profit reaches this percentage. NULL = no take profit.';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS stop_loss_price DECIMAL(20, 8) DEFAULT NULL
    COMMENT 'Stop Loss Price: Auto-close grid when market price hits this level. NULL = no stop loss.';

ALTER TABLE grid_bots ADD COLUMN IF NOT EXISTS sell_all_on_stop TINYINT DEFAULT 0
    COMMENT 'Sell All on Stop: 1 = liquidate entire position when stop loss triggered, 0 = keep holdings.';

-- ============================================
-- NOTES FOR DEVELOPERS
-- ============================================
--
-- Grid Type Explanation:
-- -----------------------
-- ARITHMETIC:
-- - Equal price intervals between grids
-- - Example: $100, $110, $120, $130 (intervals of $10)
-- - Best for: Stable price ranges, lower volatility
-- - Formula: interval = (upper - lower) / (grids - 1)
--
-- GEOMETRIC:
-- - Equal percentage intervals between grids  
-- - Example: $100, $110, $121, $133.1 (10% intervals)
-- - Best for: High volatility, exponential growth
-- - Formula: ratio = (upper / lower) ^ (1 / (grids - 1))
--
-- Trailing Up:
-- ------------
-- When enabled, if price moves above upper range:
-- - Grid shifts upward to follow price
-- - Maintains grid width
-- - Captures profits in bull markets
-- - Risk: May not buy if price drops suddenly
--
-- Grid Trigger Price:
-- -------------------
-- Bot waits in standby until market reaches trigger price
-- - Useful for: "Buy the dip" strategies
-- - Example: Current price $100, trigger $90
-- - Bot activates only when price drops to $90
--
-- Take Profit:
-- ------------
-- Automatically close grid when profit target reached
-- - Calculated as: (current_value - initial_investment) / initial_investment * 100
-- - Example: 10% take profit on $1000 = close at $1100 total value
-- - Locks in gains automatically
--
-- Stop Loss:
-- ----------
-- Automatically close grid when price drops below threshold
-- - Protects against major market downturns
-- - Example: Stop loss at $90 on BTC at $100
-- - If sell_all_on_stop = 1: Liquidates all holdings
-- - If sell_all_on_stop = 0: Stops bot but keeps positions
--
-- ============================================
-- EXAMPLE CONFIGURATIONS
-- ============================================
--
-- Conservative Grid (Low Risk):
-- - Range: Current price ±5%
-- - Grids: 10 (Arithmetic)
-- - Investment: Moderate amount
-- - Trailing: Disabled
-- - Take Profit: 5-10%
-- - Stop Loss: -3%
--
-- Aggressive Grid (High Risk):
-- - Range: Current price ±20%
-- - Grids: 20-50 (Geometric)
-- - Investment: Higher amount
-- - Trailing: Enabled
-- - Take Profit: 20-50%
-- - Stop Loss: -10%
--
-- Neutral Range Grid:
-- - Range: Support to Resistance levels
-- - Grids: 15-25 (Arithmetic)
-- - Investment: Based on risk tolerance
-- - Trailing: Disabled
-- - Take Profit: Optional
-- - Stop Loss: Below support
--
-- ============================================
-- MIGRATION ROLLBACK (if needed)
-- ============================================
--
-- To rollback this migration:
-- ALTER TABLE grid_bots DROP COLUMN grid_lower_price;
-- ALTER TABLE grid_bots DROP COLUMN grid_upper_price;
-- ALTER TABLE grid_bots DROP COLUMN grid_type;
-- ALTER TABLE grid_bots DROP COLUMN investment_amount;
-- ALTER TABLE grid_bots DROP COLUMN quote_currency;
-- ALTER TABLE grid_bots DROP COLUMN trailing_up;
-- ALTER TABLE grid_bots DROP COLUMN grid_trigger_price;
-- ALTER TABLE grid_bots DROP COLUMN take_profit_pct;
-- ALTER TABLE grid_bots DROP COLUMN stop_loss_price;
-- ALTER TABLE grid_bots DROP COLUMN sell_all_on_stop;
--
-- ============================================

-- Verify migration
SELECT 
    'Migration 003 completed successfully. Grid bots table now supports Binance-style configuration.' as status;


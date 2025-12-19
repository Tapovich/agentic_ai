-- Migration: Add demo_mode to Grid and DCA bots tables
-- TASK 56: 1-click demo setups
-- Date: 2025-11-13
-- Description: Add demo_mode flag to support paper-trading demo bots for presentations

-- Add demo_mode column to grid_bots table
-- demo_mode = 1 means this bot is a paper-trading demo bot used for presentations
ALTER TABLE grid_bots ADD COLUMN demo_mode TINYINT(1) NOT NULL DEFAULT 0;

-- Add demo_mode column to dca_bots table
-- demo_mode = 1 means this bot is a paper-trading demo bot used for presentations
ALTER TABLE dca_bots ADD COLUMN demo_mode TINYINT(1) NOT NULL DEFAULT 0;

-- Create index for faster filtering of demo bots
CREATE INDEX idx_grid_bots_demo_mode ON grid_bots(demo_mode);
CREATE INDEX idx_dca_bots_demo_mode ON dca_bots(demo_mode);

-- Update existing bots to explicitly be non-demo (default handles this, but being explicit)
UPDATE grid_bots SET demo_mode = 0 WHERE demo_mode IS NULL;
UPDATE dca_bots SET demo_mode = 0 WHERE demo_mode IS NULL;


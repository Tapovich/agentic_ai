-- ============================================
-- ADVANCED PREDICTIONS TABLE
-- ============================================
-- Stores predictions from both AI and Indicator models
-- Allows tracking prediction accuracy over time

CREATE TABLE IF NOT EXISTS advanced_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    mode VARCHAR(20) NOT NULL,  -- 'ai' or 'indicator'
    timeframe VARCHAR(10) NOT NULL,  -- '1h', '4h', '1d'
    
    -- Prediction details
    signal VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL', 'HOLD'
    direction VARCHAR(20),  -- 'up', 'down', 'neutral'
    confidence DECIMAL(5,2),  -- 0-100%
    
    -- Price information
    current_price DECIMAL(15,2) NOT NULL,
    target_price DECIMAL(15,2),
    pct_change DECIMAL(10,2),  -- Expected % change
    
    -- Summary and details
    summary TEXT,
    indicators_snapshot TEXT,  -- JSON of all indicators at time of prediction
    
    -- Tracking and evaluation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_time TIMESTAMP,  -- When prediction should be evaluated
    actual_price DECIMAL(15,2),  -- Filled later for accuracy tracking
    outcome VARCHAR(20),  -- 'correct', 'incorrect', 'pending'
    accuracy_score DECIMAL(5,2),  -- How accurate was the prediction
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_predictions_user ON advanced_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON advanced_predictions(symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON advanced_predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_outcome ON advanced_predictions(outcome);

-- ============================================
-- PREDICTION HISTORY VIEW
-- ============================================
-- Useful view for analyzing prediction accuracy

CREATE VIEW IF NOT EXISTS prediction_performance AS
SELECT 
    mode,
    symbol,
    COUNT(*) as total_predictions,
    SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct_predictions,
    CAST(SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as accuracy_pct,
    AVG(confidence) as avg_confidence,
    AVG(ABS(pct_change)) as avg_predicted_move
FROM advanced_predictions
WHERE outcome IN ('correct', 'incorrect')
GROUP BY mode, symbol;


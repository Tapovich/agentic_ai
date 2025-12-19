-- ============================================
-- AI Trading Assistant - Database Schema
-- ============================================
-- This file contains the complete database schema for the AI Trading Assistant.
-- Execute this file in MySQL to create all necessary tables.

-- Create the database (optional - comment out if database already exists)
CREATE DATABASE IF NOT EXISTS ai_trading_db;
USE ai_trading_db;

-- ============================================
-- TABLE: users
-- ============================================
-- Purpose: Stores user account information for authentication and identification
-- Each user gets a virtual balance to practice paper trading
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    balance DECIMAL(15, 2) DEFAULT 10000.00,  -- Virtual trading balance (starts at $10,000)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- ============================================
-- TABLE: price_history
-- ============================================
-- Purpose: Stores historical cryptocurrency price data (OHLCV format)
-- This data is used to display charts and train the AI prediction model
-- OHLCV = Open, High, Low, Close, Volume
CREATE TABLE price_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,  -- e.g., "BTCUSDT", "ETHUSDT"
    timestamp DATETIME NOT NULL,
    open_price DECIMAL(15, 2) NOT NULL,   -- Opening price for the time period
    high_price DECIMAL(15, 2) NOT NULL,   -- Highest price in the time period
    low_price DECIMAL(15, 2) NOT NULL,    -- Lowest price in the time period
    close_price DECIMAL(15, 2) NOT NULL,  -- Closing price for the time period
    volume DECIMAL(20, 8) DEFAULT 0,      -- Trading volume
    INDEX idx_symbol_timestamp (symbol, timestamp),
    INDEX idx_timestamp (timestamp)
);

-- ============================================
-- TABLE: predictions
-- ============================================
-- Purpose: Stores AI model predictions for price movements
-- The AI predicts whether the price will go UP (1) or DOWN (0)
-- Includes confidence score to show how certain the model is
CREATE TABLE predictions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,          -- Cryptocurrency symbol
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    prediction_class TINYINT NOT NULL,    -- 1 = UP (price will increase), 0 = DOWN (price will decrease)
    confidence FLOAT NOT NULL,            -- Confidence score (0.0 to 1.0 or 0% to 100%)
    INDEX idx_symbol_timestamp (symbol, timestamp),
    CHECK (prediction_class IN (0, 1)),   -- Ensure only 0 or 1 values
    CHECK (confidence >= 0 AND confidence <= 1)  -- Ensure confidence is between 0 and 1
);

-- ============================================
-- TABLE: portfolio
-- ============================================
-- Purpose: Stores each user's current cryptocurrency holdings
-- Tracks how much of each crypto the user owns and at what average price
CREATE TABLE portfolio (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,          -- Cryptocurrency symbol
    quantity DECIMAL(20, 8) NOT NULL,     -- Amount of crypto owned
    average_price DECIMAL(15, 2) NOT NULL, -- Average purchase price
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_symbol (user_id, symbol),  -- One row per user per symbol
    INDEX idx_user_id (user_id),
    CHECK (quantity >= 0)  -- Quantity cannot be negative
);

-- ============================================
-- TABLE: trades
-- ============================================
-- Purpose: Stores complete trading history for all users
-- Every buy or sell transaction is recorded here
-- Used to display trade history and calculate portfolio performance
CREATE TABLE trades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    symbol VARCHAR(20) NOT NULL,          -- Cryptocurrency symbol
    side ENUM('BUY', 'SELL') NOT NULL,    -- Transaction type: BUY or SELL
    quantity DECIMAL(20, 8) NOT NULL,     -- Amount of crypto bought/sold
    price DECIMAL(15, 2) NOT NULL,        -- Price per unit at time of trade
    total_amount DECIMAL(15, 2) NOT NULL, -- Total transaction value (quantity * price)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_user_symbol (user_id, symbol),
    CHECK (quantity > 0),  -- Quantity must be positive
    CHECK (price > 0)      -- Price must be positive
);

-- ============================================
-- SUMMARY OF TABLES
-- ============================================

/*
TABLE EXPLANATIONS:

1. users
   - Stores all registered user accounts
   - Contains login credentials (username, email, password hash)
   - Tracks virtual balance for paper trading
   - Each new user starts with $10,000 virtual money

2. price_history
   - Historical cryptocurrency price data
   - Uses OHLCV format (standard in trading)
   - Used to display price charts on the dashboard
   - Used to train the AI prediction model
   - Example: Bitcoin price at 1pm was $45,000 (open), peaked at $45,500 (high), etc.

3. predictions
   - Stores AI model's predictions
   - Predicts if price will go UP (1) or DOWN (0)
   - Includes confidence score (how sure the AI is)
   - Example: "Bitcoin will go UP with 75% confidence"

4. portfolio
   - Current holdings for each user
   - Shows what crypto each user owns
   - Tracks average purchase price for profit/loss calculation
   - Updates when user buys or sells
   - Example: User owns 0.5 BTC bought at average price of $40,000

5. trades
   - Complete history of all buy/sell transactions
   - Records every trade made by users
   - Used to show trade history on dashboard
   - Used to calculate user performance
   - Example: User bought 0.1 BTC at $45,000 on Nov 13, 2025
*/

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================

-- Insert a test user (password: "password123")
-- Note: The password hash below is created using werkzeug.security.generate_password_hash()
-- You can also create users by running: python create_demo_user.py
INSERT INTO users (username, email, password_hash, balance) VALUES
('testuser', 'test@example.com', 'scrypt:32768:8:1$0aB1cD2eF3gH4$5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 10000.00);

-- Insert sample price data for Bitcoin (BTCUSDT)
INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume) VALUES
('BTCUSDT', '2025-11-13 09:00:00', 45000.00, 45500.00, 44800.00, 45200.00, 1250.50),
('BTCUSDT', '2025-11-13 10:00:00', 45200.00, 45800.00, 45100.00, 45600.00, 1380.75),
('BTCUSDT', '2025-11-13 11:00:00', 45600.00, 46000.00, 45400.00, 45900.00, 1520.25);

-- Insert a sample AI prediction
INSERT INTO predictions (symbol, prediction_class, confidence) VALUES
('BTCUSDT', 1, 0.78);  -- Predicts UP with 78% confidence


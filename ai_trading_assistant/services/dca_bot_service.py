"""
DCA Bot Service
Implements Dollar-Cost Averaging (DCA) trading strategy.

NOTE (TASK 27): All price data in this module comes from services/realtime_price_service.py
for consistency and real-time behaviour. DCA bots use REAL market prices for execution,
not hardcoded values. Prices are fetched by order_execution_service which uses the unified
price service.

What is DCA (Dollar-Cost Averaging)?
====================================
DCA is an investment strategy where you buy a fixed amount of an asset
at regular intervals, regardless of the price.

Example:
- Instead of buying $1,000 of Bitcoin all at once
- You buy $100 every week for 10 weeks
- This averages out your purchase price
- Reduces impact of volatility
- Removes emotion from investing

Benefits:
- No need to time the market
- Reduces risk of buying at peak
- Accumulates assets over time
- Disciplined approach
- Good for long-term investing

How It Works:
- Set amount to buy (e.g., 0.01 BTC)
- Set interval (e.g., weekly)
- Bot buys automatically on schedule
- Builds position over time

In This Project:
- Manual execution (no cron/scheduler)
- "Run Once" button for demonstration
- Shows how automated DCA would work
- Educational purpose
"""

from models import db
from services import order_execution_service


def create_dca_bot(user_id, exchange_account_id, symbol, buy_amount, interval_description='Weekly',
                   side='BUY', price_deviation_pct=1.0, take_profit_pct=None, take_profit_type='FIX',
                   base_order_size=None, dca_order_size=None, max_dca_orders=5,
                   trigger_price=None, price_deviation_multiplier=None, dca_order_size_multiplier=None,
                   cooldown_seconds=None, range_lower=None, range_upper=None,
                   stop_loss_pct=None, end_on_stop=False):
    """
    Create a new DCA (Dollar-Cost Averaging) bot with Binance-style advanced configuration.
    
    What This Does:
    - Stores a recurring buy/sell strategy with advanced risk management
    - Supports progressive DCA with multipliers
    - Includes take profit, stop loss, and trigger price
    - In production, would run on schedule
    - In this project, triggered manually
    
    Args:
        user_id (int): User's ID
        exchange_account_id (int): Which exchange account to use
        symbol (str): Symbol to trade (e.g., "BTCUSDT")
        buy_amount (float): Amount to buy each time (legacy, can use base_order_size instead)
        interval_description (str): "Daily", "Weekly", "Monthly", etc.
        
        # Binance-Style Advanced Parameters (TASK 39):
        side (str): 'BUY' (long DCA) or 'SELL' (short DCA)
        price_deviation_pct (float): % deviation between DCA orders (e.g., 1.0 = 1%)
        take_profit_pct (float): Take profit % from average entry (None = no TP)
        take_profit_type (str): 'FIX' (fixed %) or 'TRAIL' (trailing, future)
        base_order_size (float): Size of first order (None = use buy_amount)
        dca_order_size (float): Size of each DCA order (None = use buy_amount)
        max_dca_orders (int): Maximum number of DCA orders (safety limit)
        trigger_price (float): Activate bot at this price (None = immediate)
        price_deviation_multiplier (float): Exponential spacing multiplier (None = linear)
        dca_order_size_multiplier (float): Progressive sizing multiplier (None = fixed)
        cooldown_seconds (int): Min seconds between DCA rounds (None = no cooldown)
        range_lower (float): Lower price bound (None = no lower limit)
        range_upper (float): Upper price bound (None = no upper limit)
        stop_loss_pct (float): Stop loss % from average (None = no SL)
        end_on_stop (bool): If True, end bot permanently on stop loss
    
    Returns:
        dict: Result with bot_id and success status
    
    Example (Basic):
        result = create_dca_bot(
            user_id=1,
            exchange_account_id=1,
            symbol="BTCUSDT",
            buy_amount=100,
            interval_description="Weekly"
        )
    
    Example (Advanced with Binance-style features):
        result = create_dca_bot(
            user_id=1,
            exchange_account_id=1,
            symbol="BTCUSDT",
            buy_amount=100,
            interval_description="Daily",
            side='BUY',
            price_deviation_pct=1.5,
            take_profit_pct=10.0,
            base_order_size=100,
            dca_order_size=150,
            max_dca_orders=7,
            trigger_price=45000,
            price_deviation_multiplier=1.3,
            dca_order_size_multiplier=1.5,
            stop_loss_pct=8.0,
            end_on_stop=True
        )
    
    Note:
        This is an educational implementation inspired by Binance Spot DCA.
        Advanced features (multipliers, progressive sizing, auto TP/SL) are stored
        in config but require additional execution logic for full automation.
    """
    
    print(f"\n{'='*70}")
    print(f"Creating DCA Bot (Binance-Style)")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Side: {side}")
    print(f"Base Order: ${base_order_size or buy_amount}")
    print(f"DCA Order: ${dca_order_size or buy_amount}")
    print(f"Max Orders: {max_dca_orders}")
    print(f"Price Deviation: {price_deviation_pct}%")
    if take_profit_pct:
        print(f"✓ Take Profit: {take_profit_pct}%")
    if trigger_price:
        print(f"✓ Trigger Price: ${trigger_price}")
    if stop_loss_pct:
        print(f"✓ Stop Loss: {stop_loss_pct}%")
    
    # ========================================
    # STEP 1: Validation
    # ========================================
    
    # Basic validation
    if buy_amount <= 0:
        return {'success': False, 'error': 'Buy amount must be positive'}
    
    if not symbol:
        return {'success': False, 'error': 'Symbol is required'}
    
    if not interval_description:
        interval_description = 'Weekly'
    
    # Validate side
    if side not in ['BUY', 'SELL']:
        return {'success': False, 'error': 'Side must be BUY or SELL'}
    
    # Validate price deviation
    if price_deviation_pct <= 0 or price_deviation_pct > 100:
        return {'success': False, 'error': 'Price deviation must be between 0 and 100%'}
    
    # Validate take profit
    if take_profit_pct is not None and (take_profit_pct <= 0 or take_profit_pct > 1000):
        return {'success': False, 'error': 'Take profit % must be between 0 and 1000'}
    
    # Validate max orders
    if max_dca_orders < 1 or max_dca_orders > 100:
        return {'success': False, 'error': 'Max DCA orders must be between 1 and 100'}
    
    # Validate stop loss
    if stop_loss_pct is not None and (stop_loss_pct <= 0 or stop_loss_pct > 100):
        return {'success': False, 'error': 'Stop loss % must be between 0 and 100'}
    
    # Validate multipliers
    if price_deviation_multiplier is not None and (price_deviation_multiplier < 0.1 or price_deviation_multiplier > 10):
        return {'success': False, 'error': 'Price deviation multiplier must be between 0.1 and 10'}
    
    if dca_order_size_multiplier is not None and (dca_order_size_multiplier < 0.1 or dca_order_size_multiplier > 10):
        return {'success': False, 'error': 'DCA order size multiplier must be between 0.1 and 10'}
    
    # Set defaults for order sizes if not provided
    if base_order_size is None:
        base_order_size = buy_amount
    if dca_order_size is None:
        dca_order_size = buy_amount
    
    print(f"✅ Validation passed")
    
    # ========================================
    # STEP 2: Create DCA Bot Record (with Binance-style advanced config)
    # ========================================
    
    try:
        # Convert boolean to integer for SQLite
        end_on_stop_int = 1 if end_on_stop else 0
        
        query = """
            INSERT INTO dca_bots (
                user_id, exchange_account_id, symbol, buy_amount, interval_description,
                side, price_deviation_pct, take_profit_pct, take_profit_type,
                base_order_size, dca_order_size, max_dca_orders,
                trigger_price, price_deviation_multiplier, dca_order_size_multiplier,
                cooldown_seconds, range_lower, range_upper,
                stop_loss_pct, end_on_stop, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """
        
        bot_id = db.execute_query(query, (
            user_id, exchange_account_id, symbol, buy_amount, interval_description,
            side, price_deviation_pct, take_profit_pct, take_profit_type,
            base_order_size, dca_order_size, max_dca_orders,
            trigger_price, price_deviation_multiplier, dca_order_size_multiplier,
            cooldown_seconds, range_lower, range_upper,
            stop_loss_pct, end_on_stop_int
        ))
        
        if bot_id:
            print(f"✅ DCA bot created with ID: {bot_id}")
            print(f"{'='*70}\n")
            
            return {
                'success': True,
                'bot_id': bot_id,
                'symbol': symbol,
                'side': side,
                'interval_description': interval_description,
                'buy_amount': buy_amount,
                'base_order_size': base_order_size,
                'dca_order_size': dca_order_size,
                'max_dca_orders': max_dca_orders,
                'price_deviation_pct': price_deviation_pct,
                'take_profit_pct': take_profit_pct,
                'take_profit_type': take_profit_type,
                'trigger_price': trigger_price,
                'price_deviation_multiplier': price_deviation_multiplier,
                'dca_order_size_multiplier': dca_order_size_multiplier,
                'cooldown_seconds': cooldown_seconds,
                'range_lower': range_lower,
                'range_upper': range_upper,
                'stop_loss_pct': stop_loss_pct,
                'end_on_stop': end_on_stop,
                'message': f'DCA bot created: {side} {symbol} {interval_description}'
            }
        else:
            return {'success': False, 'error': 'Failed to create DCA bot'}
            
    except Exception as e:
        print(f"❌ Error creating DCA bot: {e}")
        return {'success': False, 'error': str(e)}


def get_dca_bots_for_user(user_id):
    """
    Get all DCA bots for a user.
    
    Args:
        user_id (int): User's ID
    
    Returns:
        list: List of DCA bot records with exchange info
    
    Example:
        bots = get_dca_bots_for_user(1)
        for bot in bots:
            print(f"Bot {bot['id']}: Buy {bot['buy_amount']} {bot['symbol']} {bot['interval_description']}")
    """
    
    query = """
        SELECT 
            d.*,
            e.exchange_name,
            e.account_label,
            e.is_testnet
        FROM dca_bots d
        JOIN exchange_accounts e ON d.exchange_account_id = e.id
        WHERE d.user_id = ?
        ORDER BY d.created_at DESC
    """
    
    bots = db.fetch_all(query, (user_id,))
    return bots if bots else []


def get_dca_bot_details(bot_id, user_id):
    """
    Get detailed information about a DCA bot.
    
    Args:
        bot_id (int): Bot ID
        user_id (int): User ID (for verification)
    
    Returns:
        dict: Bot details or None if not found
    """
    
    query = """
        SELECT 
            d.*,
            e.exchange_name,
            e.account_label,
            e.is_testnet
        FROM dca_bots d
        JOIN exchange_accounts e ON d.exchange_account_id = e.id
        WHERE d.id = ? AND d.user_id = ?
    """
    
    bot = db.fetch_one(query, (bot_id, user_id))
    return bot


def run_dca_cycle(bot_id, user_id):
    """
    Execute one DCA buy cycle.
    
    What This Does:
    ===============
    1. Loads bot configuration
    2. Buys the specified amount
    3. Logs the trade
    4. Updates bot statistics
    
    In Production:
    - Would run automatically on schedule (cron job)
    - Triggered daily, weekly, etc.
    - No manual intervention
    
    In This Demo:
    - Manual trigger via "Run Once" button
    - Shows how automation would work
    - Educational purpose
    
    DCA Philosophy:
    - Buy regularly, don't time the market
    - Price high? Buy less quantity
    - Price low? Buy more quantity
    - Over time, average price is fair
    
    Args:
        bot_id (int): DCA bot ID
        user_id (int): User ID (for verification)
    
    Returns:
        dict: Execution result
    
    Example:
        result = run_dca_cycle(bot_id=1, user_id=1)
        
        if result['success']:
            print(f"DCA executed: {result['message']}")
            print(f"Bought at: ${result['price']}")
    """
    
    print(f"\n{'='*70}")
    print(f"DCA BOT EXECUTION")
    print(f"{'='*70}")
    
    # Get bot details
    bot = get_dca_bot_details(bot_id, user_id)
    
    if not bot:
        return {
            'success': False,
            'error': 'DCA bot not found or access denied'
        }
    
    if bot['is_active'] == 0:
        return {
            'success': False,
            'error': 'DCA bot is not active'
        }
    
    print(f"Bot ID: {bot_id}")
    print(f"Symbol: {bot['symbol']}")
    print(f"Buy Amount: {bot['buy_amount']}")
    print(f"Interval: {bot['interval_description']}")
    print(f"Exchange: {bot['exchange_name']}")
    print(f"Executions so far: {bot['execution_count']}")
    print(f"{'='*70}\n")
    
    # Convert symbol format if needed (BTCUSDT → BTC/USDT)
    symbol = bot['symbol']
    if '/' not in symbol:
        symbol_exchange = symbol.replace('USDT', '/USDT')
    else:
        symbol_exchange = symbol
    
    # Execute buy order
    # DCA always buys (accumulates asset over time)
    result = order_execution_service.execute_market_order_for_account(
        user_id=user_id,
        exchange_account_id=bot['exchange_account_id'],
        symbol=symbol_exchange,
        side='buy',  # DCA always buys
        amount=bot['buy_amount'],
        trade_source=f'dca_bot_{bot_id}'
    )
    
    if result['success']:
        # Update bot statistics
        query = """
            UPDATE dca_bots 
            SET last_run_at = datetime('now'),
                execution_count = execution_count + 1
            WHERE id = ?
        """
        db.execute_query(query, (bot_id,))
        
        print(f"✅ DCA cycle completed successfully!")
        print(f"   Execution #{bot['execution_count'] + 1}")
        
        # Add bot info to result
        result['bot_id'] = bot_id
        result['symbol'] = bot['symbol']
        result['buy_amount'] = bot['buy_amount']
        result['interval'] = bot['interval_description']
        result['execution_count'] = bot['execution_count'] + 1
    
    return result


def stop_dca_bot(bot_id, user_id):
    """
    Stop a DCA bot (set is_active = 0).
    
    Args:
        bot_id (int): Bot ID
        user_id (int): User ID (for verification)
    
    Returns:
        dict: Result with success status
    """
    
    query = """
        UPDATE dca_bots 
        SET is_active = 0 
        WHERE id = ? AND user_id = ?
    """
    
    result = db.execute_query(query, (bot_id, user_id))
    
    if result:
        return {'success': True, 'message': 'DCA bot stopped'}
    else:
        return {'success': False, 'error': 'Bot not found or access denied'}


def delete_dca_bot(bot_id, user_id):
    """
    Delete a DCA bot.
    
    Args:
        bot_id (int): Bot ID
        user_id (int): User ID (for verification)
    
    Returns:
        dict: Result with success status
    """
    
    query = """
        DELETE FROM dca_bots 
        WHERE id = ? AND user_id = ?
    """
    
    result = db.execute_query(query, (bot_id, user_id))
    
    if result:
        return {'success': True, 'message': 'DCA bot deleted'}
    else:
        return {'success': False, 'error': 'Bot not found or access denied'}


def get_dca_statistics(bot_id, user_id):
    """
    Get statistics for a DCA bot.
    
    Args:
        bot_id (int): Bot ID
        user_id (int): User ID
    
    Returns:
        dict: Statistics about bot performance
    """
    
    # Get bot info
    bot = get_dca_bot_details(bot_id, user_id)
    
    if not bot:
        return None
    
    # Get all trade logs for this bot
    query = """
        SELECT 
            COUNT(*) as total_executions,
            SUM(amount) as total_bought,
            AVG(price) as average_price,
            SUM(total_value) as total_spent,
            MIN(price) as lowest_price,
            MAX(price) as highest_price
        FROM exchange_trade_logs
        WHERE trade_source = ? AND status IN ('FILLED', 'SIMULATED')
    """
    
    stats = db.fetch_one(query, (f'dca_bot_{bot_id}',))
    
    return stats


# ============================================
# EDUCATIONAL NOTES
# ============================================

"""
DCA vs Lump Sum vs Timing:
==========================

Strategy 1: Lump Sum
- Buy all at once
- Best if: Price goes straight up
- Worst if: You buy at the peak
- Risk: High (all eggs in one basket)
- Stress: High (what if it drops?)

Strategy 2: Market Timing
- Buy at dips, sell at peaks
- Best if: You can predict perfectly
- Worst if: Wrong predictions
- Risk: High (usually lose)
- Stress: Very high
- Reality: Almost impossible to do consistently

Strategy 3: DCA (This Implementation)
- Buy fixed amount regularly
- Best if: You want peace of mind
- Worst if: Price goes straight up (you'd have been better with lump sum)
- Risk: Low (spread out)
- Stress: Low (automated)
- Reality: Works well for most people

When to Use DCA:
- Long-term investing
- Volatile markets
- Building position over time
- When you have regular income
- Want to remove emotion

When NOT to Use DCA:
- Short-term trading
- Strong uptrend (lump sum better)
- Very small amounts (fees eat returns)
- Need liquidity soon

For University Project:
- Demonstrates automated strategy
- Shows scheduling concept
- Explains investment philosophy
- Professional feature
"""


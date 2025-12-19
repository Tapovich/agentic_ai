"""
Grid Bot Service
Implements grid trading strategy logic for paper trading.

NOTE (TASK 27): All price data in this module comes from services/realtime_price_service.py
for consistency and real-time behaviour. Grid bots do NOT hardcode prices.

What is Grid Trading?
--------------------
Grid trading is an automated trading strategy that:
1. Divides a price range into multiple levels (grid)
2. Places buy orders at lower levels
3. Places sell orders at upper levels
4. Profits from price fluctuations within the range

Example:
- Range: $40,000 to $50,000
- Grids: 5 levels → $40k, $42.5k, $45k, $47.5k, $50k
- Lower levels: BUY orders
- Upper levels: SELL orders
- As price moves up/down, bot executes trades automatically
"""

from models import db


def create_grid_bot(user_id, symbol, lower_price, upper_price, grid_count, investment_amount,
                    grid_type='ARITHMETIC', quote_currency='USDT', trailing_up=False,
                    grid_trigger_price=None, take_profit_pct=None, stop_loss_price=None,
                    sell_all_on_stop=False):
    """
    Create a new grid trading bot with Binance-style advanced configuration.
    
    This function:
    1. Validates inputs
    2. Creates a bot record in grid_bots table with advanced settings
    3. Calculates grid levels (Arithmetic or Geometric)
    4. Assigns BUY/SELL orders to each level
    5. Stores levels in grid_levels table
    
    Args:
        user_id (int): User's ID
        symbol (str): Cryptocurrency symbol (e.g., "BTCUSDT")
        lower_price (float): Lower bound of price range
        upper_price (float): Upper bound of price range
        grid_count (int): Number of grid levels (must be >= 2)
        investment_amount (float): Total capital for this bot
        
        # Binance-Style Advanced Parameters (TASK 38):
        grid_type (str): 'ARITHMETIC' (equal price intervals) or 'GEOMETRIC' (equal % intervals)
        quote_currency (str): Quote currency for the pair (e.g., 'USDT', 'BTC', 'ETH')
        trailing_up (bool): If True, grid follows price upward (bull market feature)
        grid_trigger_price (float): Bot activates only when price reaches this level (None = immediate)
        take_profit_pct (float): Auto-close grid at this profit % (None = no take profit)
        stop_loss_price (float): Auto-close grid at this price level (None = no stop loss)
        sell_all_on_stop (bool): If True, liquidate all holdings on stop loss trigger
    
    Returns:
        dict: Bot details with id, levels, and success status
        
    Example (Basic):
        bot = create_grid_bot(
            user_id=1,
            symbol="BTCUSDT",
            lower_price=40000,
            upper_price=50000,
            grid_count=5,
            investment_amount=1000
        )
    
    Example (Advanced with Binance-style features):
        bot = create_grid_bot(
            user_id=1,
            symbol="BTCUSDT",
            lower_price=40000,
            upper_price=50000,
            grid_count=10,
            investment_amount=1000,
            grid_type='GEOMETRIC',
            quote_currency='USDT',
            trailing_up=True,
            take_profit_pct=15.0,
            stop_loss_price=38000,
            sell_all_on_stop=True
        )
    
    Note:
        This is an educational implementation inspired by Binance Spot Grid Trading.
        Advanced features (trailing, take profit, stop loss) are stored in config but
        require additional execution logic for full automation (not implemented in this version).
    """
    print(f"\n{'='*70}")
    print(f"Creating Grid Bot (Binance-Style)")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Range: ${lower_price:.2f} - ${upper_price:.2f}")
    print(f"Grids: {grid_count} ({grid_type})")
    print(f"Investment: ${investment_amount:.2f} {quote_currency}")
    if trailing_up:
        print(f"✓ Trailing Up enabled")
    if grid_trigger_price:
        print(f"✓ Trigger Price: ${grid_trigger_price:.2f}")
    if take_profit_pct:
        print(f"✓ Take Profit: {take_profit_pct:.2f}%")
    if stop_loss_price:
        print(f"✓ Stop Loss: ${stop_loss_price:.2f}")
    
    # ========================================
    # STEP 1: Validation
    # ========================================
    
    # Validate grid count
    if grid_count < 2:
        return {'success': False, 'error': 'Grid count must be at least 2'}
    
    if grid_count > 100:
        return {'success': False, 'error': 'Grid count too large (max 100)'}
    
    # Validate price range
    if lower_price >= upper_price:
        return {'success': False, 'error': 'Upper price must be greater than lower price'}
    
    if lower_price <= 0 or upper_price <= 0:
        return {'success': False, 'error': 'Prices must be positive'}
    
    # Validate investment
    if investment_amount <= 0:
        return {'success': False, 'error': 'Investment amount must be positive'}
    
    # Validate grid type
    if grid_type not in ['ARITHMETIC', 'GEOMETRIC']:
        return {'success': False, 'error': 'Grid type must be ARITHMETIC or GEOMETRIC'}
    
    # Validate trigger price (if set)
    if grid_trigger_price is not None and grid_trigger_price <= 0:
        return {'success': False, 'error': 'Trigger price must be positive'}
    
    # Validate take profit (if set)
    if take_profit_pct is not None and (take_profit_pct <= 0 or take_profit_pct > 1000):
        return {'success': False, 'error': 'Take profit % must be between 0 and 1000'}
    
    # Validate stop loss (if set)
    if stop_loss_price is not None and stop_loss_price <= 0:
        return {'success': False, 'error': 'Stop loss price must be positive'}
    
    # Check user has sufficient balance
    query = "SELECT balance FROM users WHERE id = ?"
    user = db.fetch_one(query, (user_id,))
    
    if not user:
        return {'success': False, 'error': 'User not found'}
    
    if user['balance'] < investment_amount:
        return {
            'success': False, 
            'error': f'Insufficient balance. Required: ${investment_amount:.2f}, Available: ${user["balance"]:.2f}'
        }
    
    print(f"✅ Validation passed")
    
    # ========================================
    # STEP 2: Create Grid Bot Record (with Binance-style advanced config)
    # ========================================
    
    # Convert boolean values to integers for SQLite
    trailing_up_int = 1 if trailing_up else 0
    sell_all_on_stop_int = 1 if sell_all_on_stop else 0
    
    query = """
        INSERT INTO grid_bots (
            user_id, symbol, lower_price, upper_price, grid_count, investment_amount,
            grid_lower_price, grid_upper_price, grid_type, quote_currency,
            trailing_up, grid_trigger_price, take_profit_pct, stop_loss_price,
            sell_all_on_stop, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """
    
    # Note: We store both old columns (lower_price, upper_price) and new columns 
    # (grid_lower_price, grid_upper_price) for backwards compatibility
    bot_id = db.execute_query(query, (
        user_id, symbol, lower_price, upper_price, grid_count, investment_amount,
        lower_price, upper_price, grid_type, quote_currency,
        trailing_up_int, grid_trigger_price, take_profit_pct, stop_loss_price,
        sell_all_on_stop_int
    ))
    
    if not bot_id:
        return {'success': False, 'error': 'Failed to create bot'}
    
    print(f"✅ Bot created with ID: {bot_id}")
    
    # ========================================
    # STEP 3: Calculate Grid Levels (ARITHMETIC or GEOMETRIC)
    # ========================================
    
    grid_levels = []
    
    if grid_type == 'ARITHMETIC':
        # ARITHMETIC Grid: Equal price intervals
        # Example: $100, $110, $120, $130 (intervals of $10)
        # Formula: price = lower + (i * step)
        # Best for: Stable price ranges, lower volatility
        
        price_step = (upper_price - lower_price) / (grid_count - 1)
        
        print(f"📊 Calculating ARITHMETIC grid levels...")
        print(f"   Price step: ${price_step:.2f}")
        
        for i in range(grid_count):
            level_price = lower_price + (i * price_step)
            
            # Determine order type:
            # Lower half = BUY orders (buy when price is low)
            # Upper half = SELL orders (sell when price is high)
            if i < grid_count // 2:
                order_type = 'BUY'
            else:
                order_type = 'SELL'
            
            grid_levels.append({
                'level_price': level_price,
                'order_type': order_type,
                'level_number': i + 1
            })
    
    else:  # GEOMETRIC
        # GEOMETRIC Grid: Equal percentage intervals
        # Example: $100, $110, $121, $133.1 (10% intervals)
        # Formula: price = lower * (ratio ^ i)
        # Best for: High volatility, exponential growth
        
        import math
        
        # Calculate geometric ratio
        # ratio = (upper / lower) ^ (1 / (grids - 1))
        ratio = math.pow(upper_price / lower_price, 1.0 / (grid_count - 1))
        
        print(f"📊 Calculating GEOMETRIC grid levels...")
        print(f"   Geometric ratio: {ratio:.6f}")
        
        for i in range(grid_count):
            level_price = lower_price * math.pow(ratio, i)
            
            # Determine order type
            if i < grid_count // 2:
                order_type = 'BUY'
            else:
                order_type = 'SELL'
            
            grid_levels.append({
                'level_price': level_price,
                'order_type': order_type,
                'level_number': i + 1
            })
    
    print(f"✅ Calculated {len(grid_levels)} grid levels ({grid_type})")
    print(f"   Range: ${lower_price:.2f} to ${upper_price:.2f}")
    print(f"   First 3 levels: ", end="")
    for level in grid_levels[:3]:
        print(f"${level['level_price']:.2f} ", end="")
    print()
    
    # ========================================
    # STEP 4: Insert Grid Levels into Database
    # ========================================
    
    query = """
        INSERT INTO grid_levels (bot_id, level_price, order_type, is_filled)
        VALUES (?, ?, ?, 0)
    """
    
    for level in grid_levels:
        db.execute_query(query, (bot_id, level['level_price'], level['order_type']))
    
    print(f"✅ Grid levels saved to database")
    
    # ========================================
    # STEP 5: Reserve Investment Amount
    # ========================================
    # Deduct investment from user's available balance
    # This prevents user from using the same money twice
    
    new_balance = user['balance'] - investment_amount
    query = "UPDATE users SET balance = ? WHERE id = ?"
    db.execute_query(query, (new_balance, user_id))
    
    print(f"✅ Reserved ${investment_amount:.2f} from balance")
    print(f"   New available balance: ${new_balance:.2f}")
    
    # ========================================
    # STEP 6: Return Bot Details (with Binance-style config)
    # ========================================
    
    print(f"{'='*70}\n")
    
    return {
        'success': True,
        'bot_id': bot_id,
        'symbol': symbol,
        'lower_price': lower_price,
        'upper_price': upper_price,
        'grid_count': grid_count,
        'grid_type': grid_type,
        'investment_amount': investment_amount,
        'quote_currency': quote_currency,
        'trailing_up': trailing_up,
        'grid_trigger_price': grid_trigger_price,
        'take_profit_pct': take_profit_pct,
        'stop_loss_price': stop_loss_price,
        'sell_all_on_stop': sell_all_on_stop,
        'levels': grid_levels,
        'new_balance': new_balance
    }


def get_bots_for_user(user_id):
    """
    Get all grid bots for a user.
    
    Args:
        user_id (int): User's ID
    
    Returns:
        list: List of grid bot records
        
    Example:
        bots = get_bots_for_user(1)
        for bot in bots:
            print(f"Bot {bot['id']}: {bot['symbol']} - {bot['grid_count']} levels")
    """
    query = """
        SELECT * FROM grid_bots
        WHERE user_id = ?
        ORDER BY created_at DESC
    """
    bots = db.fetch_all(query, (user_id,))
    
    return bots if bots else []


def get_levels_for_bot(bot_id):
    """
    Get all grid levels for a specific bot.
    
    Args:
        bot_id (int): Bot's ID
    
    Returns:
        list: List of grid level records with price, type, and fill status
        
    Example:
        levels = get_levels_for_bot(1)
        for level in levels:
            status = "Filled" if level['is_filled'] else "Pending"
            print(f"{level['order_type']} @ ${level['level_price']}: {status}")
    """
    query = """
        SELECT * FROM grid_levels
        WHERE bot_id = ?
        ORDER BY level_price ASC
    """
    levels = db.fetch_all(query, (bot_id,))
    
    return levels if levels else []


def get_bot_details(bot_id, user_id=None):
    """
    Get complete bot details including levels.
    
    Args:
        bot_id (int): Bot's ID
        user_id (int, optional): User's ID (for verification)
    
    Returns:
        dict: Bot details with levels, or None if not found
    """
    # Get bot info
    if user_id:
        query = "SELECT * FROM grid_bots WHERE id = ? AND user_id = ?"
        bot = db.fetch_one(query, (bot_id, user_id))
    else:
        query = "SELECT * FROM grid_bots WHERE id = ?"
        bot = db.fetch_one(query, (bot_id,))
    
    if not bot:
        return None
    
    # Get levels
    levels = get_levels_for_bot(bot_id)
    
    # Calculate statistics
    buy_levels = [l for l in levels if l['order_type'] == 'BUY']
    sell_levels = [l for l in levels if l['order_type'] == 'SELL']
    filled_count = len([l for l in levels if l['is_filled'] == 1])
    
    return {
        'bot': bot,
        'levels': levels,
        'stats': {
            'total_levels': len(levels),
            'buy_levels': len(buy_levels),
            'sell_levels': len(sell_levels),
            'filled_count': filled_count,
            'pending_count': len(levels) - filled_count
        }
    }


def stop_grid_bot(bot_id, user_id):
    """
    Stop a grid bot (set is_active to 0).
    
    Args:
        bot_id (int): Bot's ID
        user_id (int): User's ID (for verification)
    
    Returns:
        dict: Success status
    """
    # Verify bot belongs to user
    bot = get_bot_details(bot_id, user_id)
    
    if not bot:
        return {'success': False, 'error': 'Bot not found or access denied'}
    
    # Stop the bot
    query = "UPDATE grid_bots SET is_active = 0 WHERE id = ?"
    db.execute_query(query, (bot_id,))
    
    # Return investment to user's balance
    bot_info = bot['bot']
    query = "UPDATE users SET balance = balance + ? WHERE id = ?"
    db.execute_query(query, (bot_info['investment_amount'], user_id))
    
    return {
        'success': True,
        'message': 'Grid bot stopped',
        'returned_investment': bot_info['investment_amount']
    }


def delete_grid_bot(bot_id, user_id):
    """
    Delete a grid bot.
    
    Args:
        bot_id (int): Bot's ID
        user_id (int): User's ID (for verification)
    
    Returns:
        dict: Success status
    """
    # Verify bot belongs to user
    bot = get_bot_details(bot_id, user_id)
    
    if not bot:
        return {'success': False, 'error': 'Bot not found or access denied'}
    
    bot_info = bot['bot']
    
    # If bot is active, return investment first
    if bot_info['is_active'] == 1:
        query = "UPDATE users SET balance = balance + ? WHERE id = ?"
        db.execute_query(query, (bot_info['investment_amount'], user_id))
    
    # Delete bot (levels will be deleted automatically via CASCADE)
    query = "DELETE FROM grid_bots WHERE id = ?"
    db.execute_query(query, (bot_id,))
    
    return {
        'success': True,
        'message': 'Grid bot deleted'
    }


# ============================================
# UTILITY FUNCTIONS
# ============================================

def calculate_grid_levels(lower_price, upper_price, grid_count):
    """
    Calculate evenly-spaced grid levels.
    
    Args:
        lower_price (float): Lower price bound
        upper_price (float): Upper price bound
        grid_count (int): Number of levels
    
    Returns:
        list: List of price levels
    """
    price_step = (upper_price - lower_price) / (grid_count - 1)
    
    levels = []
    for i in range(grid_count):
        level_price = lower_price + (i * price_step)
        levels.append(level_price)
    
    return levels


def get_grid_statistics(bot_id):
    """
    Get statistics for a grid bot.
    
    Args:
        bot_id (int): Bot's ID
    
    Returns:
        dict: Statistics about the bot's performance
    """
    levels = get_levels_for_bot(bot_id)
    
    if not levels:
        return None
    
    total_levels = len(levels)
    filled_levels = [l for l in levels if l['is_filled'] == 1]
    buy_filled = len([l for l in filled_levels if l['order_type'] == 'BUY'])
    sell_filled = len([l for l in filled_levels if l['order_type'] == 'SELL'])
    
    return {
        'total_levels': total_levels,
        'filled_count': len(filled_levels),
        'pending_count': total_levels - len(filled_levels),
        'buy_filled': buy_filled,
        'sell_filled': sell_filled,
        'completion_pct': (len(filled_levels) / total_levels * 100) if total_levels > 0 else 0
    }


"""
Trading Model
Handles all paper trading operations including buy/sell and portfolio management.
"""

from models import db


def execute_trade(user_id, symbol, side, quantity, price):
    """
    Execute a paper trade (buy or sell).
    
    Args:
        user_id (int): User's ID
        symbol (str): Cryptocurrency symbol (e.g., "BTCUSDT")
        side (str): "BUY" or "SELL"
        quantity (float): Amount to trade
        price (float): Price per unit
    
    Returns:
        dict: Trade result with success flag and message
    """
    # Calculate total amount
    total_amount = quantity * price
    
    # Get user's current balance
    query = "SELECT balance FROM users WHERE id = ?"
    user = db.fetch_one(query, (user_id,))
    
    if not user:
        return {'success': False, 'error': 'User not found'}
    
    current_balance = user['balance']
    
    # Validate trade based on side
    if side == 'BUY':
        # Check if user has enough balance
        if current_balance < total_amount:
            return {
                'success': False,
                'error': f'Insufficient balance. Required: ${total_amount:.2f}, Available: ${current_balance:.2f}'
            }
        
        # Deduct balance
        new_balance = current_balance - total_amount
        
    elif side == 'SELL':
        # Check if user has enough of this asset
        query = "SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?"
        position = db.fetch_one(query, (user_id, symbol))
        
        if not position or position['quantity'] < quantity:
            available = position['quantity'] if position else 0
            return {
                'success': False,
                'error': f'Insufficient {symbol}. Required: {quantity}, Available: {available}'
            }
        
        # Add to balance
        new_balance = current_balance + total_amount
        
    else:
        return {'success': False, 'error': 'Invalid side. Must be BUY or SELL'}
    
    # Update user balance
    query = "UPDATE users SET balance = ? WHERE id = ?"
    db.execute_query(query, (new_balance, user_id))
    
    # Record trade in trades table
    query = """
        INSERT INTO trades (user_id, symbol, side, quantity, price, total_amount)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    trade_id = db.execute_query(query, (user_id, symbol, side, quantity, price, total_amount))
    
    if not trade_id:
        return {'success': False, 'error': 'Failed to record trade'}
    
    # Update portfolio
    if side == 'BUY':
        update_portfolio_buy(user_id, symbol, quantity, price)
    elif side == 'SELL':
        update_portfolio_sell(user_id, symbol, quantity)
    
    return {
        'success': True,
        'message': f'{side} order executed successfully',
        'trade_id': trade_id,
        'quantity': quantity,
        'price': price,
        'total_amount': total_amount,
        'new_balance': new_balance
    }


def update_portfolio_buy(user_id, symbol, quantity, price):
    """
    Update portfolio after a BUY trade.
    Increases quantity and recalculates average price.
    
    Args:
        user_id (int): User's ID
        symbol (str): Cryptocurrency symbol
        quantity (float): Quantity bought
        price (float): Purchase price
    """
    # Check if user already has this asset
    query = "SELECT quantity, average_price FROM portfolio WHERE user_id = ? AND symbol = ?"
    position = db.fetch_one(query, (user_id, symbol))
    
    if position:
        # Calculate new average price
        old_quantity = position['quantity']
        old_avg_price = position['average_price']
        
        # Total cost = old cost + new cost
        total_cost = (old_quantity * old_avg_price) + (quantity * price)
        new_quantity = old_quantity + quantity
        new_avg_price = total_cost / new_quantity
        
        # Update existing position
        query = """
            UPDATE portfolio 
            SET quantity = ?, average_price = ?
            WHERE user_id = ? AND symbol = ?
        """
        db.execute_query(query, (new_quantity, new_avg_price, user_id, symbol))
    else:
        # Create new position
        query = """
            INSERT INTO portfolio (user_id, symbol, quantity, average_price)
            VALUES (?, ?, ?, ?)
        """
        db.execute_query(query, (user_id, symbol, quantity, price))


def update_portfolio_sell(user_id, symbol, quantity):
    """
    Update portfolio after a SELL trade.
    Decreases quantity (or removes position if quantity becomes 0).
    
    Args:
        user_id (int): User's ID
        symbol (str): Cryptocurrency symbol
        quantity (float): Quantity sold
    """
    # Get current position
    query = "SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?"
    position = db.fetch_one(query, (user_id, symbol))
    
    if not position:
        return
    
    new_quantity = position['quantity'] - quantity
    
    if new_quantity <= 0:
        # Remove position entirely
        query = "DELETE FROM portfolio WHERE user_id = ? AND symbol = ?"
        db.execute_query(query, (user_id, symbol))
    else:
        # Update quantity
        query = "UPDATE portfolio SET quantity = ? WHERE user_id = ? AND symbol = ?"
        db.execute_query(query, (new_quantity, user_id, symbol))


def get_user_portfolio(user_id):
    """
    Get user's complete portfolio.
    
    Args:
        user_id (int): User's ID
    
    Returns:
        list: List of portfolio positions
    """
    query = """
        SELECT id, symbol, quantity, average_price, updated_at
        FROM portfolio
        WHERE user_id = ?
        ORDER BY symbol
    """
    portfolio = db.fetch_all(query, (user_id,))
    
    return portfolio if portfolio else []


def get_user_trades(user_id, limit=20):
    """
    Get user's recent trades.
    
    Args:
        user_id (int): User's ID
        limit (int): Number of trades to return
    
    Returns:
        list: List of trade records
    """
    query = """
        SELECT id, symbol, side, quantity, price, total_amount, created_at
        FROM trades
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """
    trades = db.fetch_all(query, (user_id, limit))
    
    return trades if trades else []


def get_portfolio_value(user_id, current_prices):
    """
    Calculate total portfolio value.
    
    Args:
        user_id (int): User's ID
        current_prices (dict): Dictionary of symbol -> current_price
    
    Returns:
        dict: Portfolio summary with total value and P/L
    """
    portfolio = get_user_portfolio(user_id)
    
    total_value = 0
    total_cost = 0
    
    positions = []
    
    for position in portfolio:
        symbol = position['symbol']
        quantity = position['quantity']
        avg_price = position['average_price']
        
        # Get current price (use average price if not provided)
        current_price = current_prices.get(symbol, avg_price)
        
        # Calculate values
        cost = quantity * avg_price
        value = quantity * current_price
        profit_loss = value - cost
        profit_loss_pct = (profit_loss / cost * 100) if cost > 0 else 0
        
        positions.append({
            'symbol': symbol,
            'quantity': quantity,
            'average_price': avg_price,
            'current_price': current_price,
            'total_value': value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        })
        
        total_value += value
        total_cost += cost
    
    total_profit_loss = total_value - total_cost
    total_profit_loss_pct = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
    
    return {
        'positions': positions,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_profit_loss': total_profit_loss,
        'total_profit_loss_pct': total_profit_loss_pct
    }


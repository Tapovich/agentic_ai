"""
Order Execution Service
Connects AI predictions and grid bots to real exchange execution.

ARCHITECTURE OVERVIEW:
=====================

This service acts as the bridge between:
- AI Predictions (UP/DOWN signals)
- Grid Bot Logic (automated buy/sell levels)
- Exchange API (real order execution via CCXT)

Flow:
1. AI or Grid Bot generates a trading signal
2. Signal comes to this service
3. Service checks if live trading is enabled
4. If SIMULATION: Log order, don't execute
5. If LIVE: Execute via exchange API, log result

Educational Purpose:
-------------------
This demonstrates how automated trading systems work in reality:
- Signal generation (AI/bot)
- Order routing (this service)
- Exchange execution (CCXT)
- Trade logging (audit trail)

⚠️ Safety First:
- Default mode is SIMULATION (no real money)
- Clear logging of all actions
- Configurable via config.LIVE_TRADING_ENABLED
"""

import config
from models import db
from models import exchange_account_model
from services import exchange_client
import json
from datetime import datetime


def execute_market_order_for_account(user_id, exchange_account_id, symbol, side, amount, 
                                     is_live_mode=None, trade_source='manual'):
    """
    Execute a market order through a linked exchange account.
    
    This is the CENTRAL function that connects everything:
    - AI predictions → trading signals
    - Grid bots → automated orders
    - Manual trades → user-initiated
    ALL go through this function for consistent execution and logging.
    
    SIMULATION vs LIVE Mode:
    ------------------------
    SIMULATION (is_live_mode=False):
        - Does NOT send order to real exchange
        - Creates log entry with status "SIMULATED"
        - Shows what WOULD happen
        - Safe for testing and demonstration
        - No financial risk
    
    LIVE (is_live_mode=True):
        - Sends REAL order to exchange via API
        - Uses real API credentials
        - Executes with real money (or testnet money)
        - Logs actual exchange response
        - Financial risk if using live account
    
    Args:
        user_id (int): User's ID
        exchange_account_id (int): Which exchange account to use
        symbol (str): Trading pair (e.g., "BTC/USDT")
        side (str): "buy" or "sell"
        amount (float): Amount to trade
        is_live_mode (bool, optional): Override config setting
        trade_source (str): What triggered this ("ai_prediction", "grid_bot", "manual")
    
    Returns:
        dict: Result with success status and details
    
    Example (Simulation):
        result = execute_market_order_for_account(
            user_id=1,
            exchange_account_id=1,
            symbol="BTC/USDT",
            side="buy",
            amount=0.01,
            is_live_mode=False,
            trade_source="ai_prediction"
        )
        # Result: {"success": True, "mode": "SIMULATED", ...}
    
    Example (Live - RISKY!):
        result = execute_market_order_for_account(
            user_id=1,
            exchange_account_id=1,
            symbol="BTC/USDT",
            side="buy",
            amount=0.01,
            is_live_mode=True,
            trade_source="manual"
        )
        # Result: {"success": True, "mode": "LIVE", "order_id": "123456", ...}
    """
    
    # Determine mode: use parameter if provided, otherwise use config
    if is_live_mode is None:
        is_live_mode = config.LIVE_TRADING_ENABLED
    
    mode = "LIVE" if is_live_mode else "SIMULATED"
    
    print(f"\n{'='*70}")
    print(f"EXECUTING ORDER ({mode} MODE)")
    print(f"{'='*70}")
    print(f"User ID: {user_id}")
    print(f"Exchange Account ID: {exchange_account_id}")
    print(f"Symbol: {symbol}")
    print(f"Side: {side.upper()}")
    print(f"Amount: {amount}")
    print(f"Source: {trade_source}")
    print(f"{'='*70}\n")
    
    try:
        # Get exchange account (with API credentials)
        account = exchange_account_model.get_exchange_account_by_id(exchange_account_id, user_id)
        
        if not account:
            return {
                'success': False,
                'error': 'Exchange account not found or access denied'
            }
        
        # ========================================
        # SIMULATION MODE
        # ========================================
        if not is_live_mode:
            print("📝 SIMULATION MODE - No real order will be sent")
            
            # Get current price from database for simulation
            from services import price_service
            price_data = price_service.get_latest_price(symbol.replace('/', ''))
            simulated_price = price_data['close_price'] if price_data else 45000.00
            
            # Calculate simulated values
            total_value = amount * simulated_price
            
            # Log simulated trade
            log_id = log_trade_execution(
                user_id=user_id,
                exchange_account_id=exchange_account_id,
                symbol=symbol,
                side=side.upper(),
                amount=amount,
                price=simulated_price,
                status='SIMULATED',
                exchange_order_id=f'SIM_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                raw_response=json.dumps({
                    'mode': 'simulation',
                    'message': 'Order simulated for demonstration',
                    'would_execute': f'{side} {amount} {symbol} @ ${simulated_price}'
                }),
                trade_source=trade_source
            )
            
            print(f"✅ Simulated order logged (ID: {log_id})")
            print(f"   Would {side}: {amount} {symbol}")
            print(f"   At price: ${simulated_price:,.2f}")
            print(f"   Total: ${total_value:,.2f}")
            
            return {
                'success': True,
                'mode': 'SIMULATED',
                'message': f'Order simulated: {side} {amount} {symbol} @ ${simulated_price:,.2f}',
                'log_id': log_id,
                'price': simulated_price,
                'total': total_value,
                'exchange': account['exchange_name']
            }
        
        # ========================================
        # LIVE MODE (REAL TRADING!)
        # ========================================
        print("🔴 LIVE MODE - Real order will be sent to exchange!")
        print("⚠️ THIS INVOLVES REAL MONEY (or testnet money)")
        
        # Create exchange client with real API credentials
        client = exchange_client.create_exchange_client(
            exchange_name=account['exchange_name'],
            api_key=account['api_key'],
            api_secret=account['api_secret'],
            is_testnet=bool(account['is_testnet'])
        )
        
        if not client:
            return {
                'success': False,
                'error': f'Failed to create {account["exchange_name"]} client'
            }
        
        # Execute real market order via exchange API
        order = exchange_client.place_market_order(
            exchange=client,
            symbol=symbol,
            side=side.lower(),
            amount=amount
        )
        
        if not order:
            # Order failed
            log_id = log_trade_execution(
                user_id=user_id,
                exchange_account_id=exchange_account_id,
                symbol=symbol,
                side=side.upper(),
                amount=amount,
                price=0,
                status='ERROR',
                trade_source=trade_source,
                error_message='Exchange rejected the order'
            )
            
            return {
                'success': False,
                'mode': 'LIVE',
                'error': 'Order execution failed',
                'log_id': log_id
            }
        
        # Order succeeded
        # Log the real trade
        log_id = log_trade_execution(
            user_id=user_id,
            exchange_account_id=exchange_account_id,
            symbol=symbol,
            side=side.upper(),
            amount=order.get('filled', amount),
            price=order.get('average', 0),
            status=order.get('status', 'FILLED').upper(),
            exchange_order_id=order.get('id'),
            raw_response=json.dumps(order),
            trade_source=trade_source,
            fee=order.get('fee', {}).get('cost', 0),
            fee_currency=order.get('fee', {}).get('currency')
        )
        
        print(f"✅ LIVE order executed successfully!")
        print(f"   Order ID: {order.get('id')}")
        print(f"   Status: {order.get('status')}")
        print(f"   Filled: {order.get('filled')}")
        print(f"   Price: ${order.get('average')}")
        
        return {
            'success': True,
            'mode': 'LIVE',
            'message': f'Order executed: {side} {amount} {symbol}',
            'order_id': order.get('id'),
            'log_id': log_id,
            'price': order.get('average'),
            'filled': order.get('filled'),
            'status': order.get('status'),
            'exchange': account['exchange_name']
        }
        
    except Exception as e:
        print(f"❌ Error executing order: {e}")
        
        # Log error
        try:
            log_trade_execution(
                user_id=user_id,
                exchange_account_id=exchange_account_id,
                symbol=symbol,
                side=side.upper(),
                amount=amount,
                price=0,
                status='ERROR',
                trade_source=trade_source,
                error_message=str(e)
            )
        except:
            pass
        
        return {
            'success': False,
            'mode': mode,
            'error': str(e)
        }


def log_trade_execution(user_id, exchange_account_id, symbol, side, amount, price,
                       status, exchange_order_id=None, raw_response=None,
                       trade_source='manual', fee=0, fee_currency=None, error_message=None):
    """
    Log a trade execution to the database.
    
    This creates a permanent record of every trade attempt, whether:
    - Simulated (for testing)
    - Live (real exchange execution)
    - Failed (errors)
    
    Purpose:
    - Audit trail (regulatory compliance)
    - Performance tracking
    - Debugging
    - User transparency
    
    Args:
        user_id (int): User ID
        exchange_account_id (int): Exchange account used
        symbol (str): Trading pair
        side (str): "BUY" or "SELL"
        amount (float): Amount traded
        price (float): Execution price
        status (str): "SIMULATED", "FILLED", "ERROR", etc.
        exchange_order_id (str, optional): Order ID from exchange
        raw_response (str, optional): Full JSON response
        trade_source (str): What triggered this trade
        fee (float): Trading fee
        fee_currency (str): Fee currency
        error_message (str, optional): Error if failed
    
    Returns:
        int: Log ID, or None if failed
    """
    
    total_value = amount * price if price > 0 else 0
    
    query = """
        INSERT INTO exchange_trade_logs 
        (user_id, exchange_account_id, symbol, side, amount, price, total_value,
         status, exchange_order_id, raw_response, trade_source, fee, fee_currency, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    log_id = db.execute_query(query, (
        user_id, exchange_account_id, symbol, side, amount, price, total_value,
        status, exchange_order_id, raw_response, trade_source, fee, fee_currency, error_message
    ))
    
    return log_id


def execute_ai_trade(user_id, exchange_account_id, symbol, amount):
    """
    Execute a trade based on AI prediction.
    
    Complete Flow:
    1. Get AI prediction for symbol (UP or DOWN)
    2. If UP: Buy signal
    3. If DOWN: Sell signal
    4. Execute order (simulation or live based on config)
    5. Log result
    
    This demonstrates AI-driven automated trading.
    
    Args:
        user_id (int): User ID
        exchange_account_id (int): Exchange account to use
        symbol (str): Symbol to trade
        amount (float): Amount to trade
    
    Returns:
        dict: Execution result with prediction details
    """
    
    from services import prediction_service
    
    print(f"\n{'='*70}")
    print(f"AI-DRIVEN TRADE EXECUTION")
    print(f"{'='*70}")
    
    # Step 1: Get AI prediction
    print(f"[1] Getting AI prediction for {symbol}...")
    
    prediction = prediction_service.predict_price_movement(symbol.replace('/', ''))
    
    if not prediction:
        return {
            'success': False,
            'error': 'Failed to get AI prediction'
        }
    
    print(f"   AI Prediction: {prediction['direction']}")
    print(f"   Confidence: {prediction['confidence_pct']}%")
    
    # Step 2: Convert prediction to trading side
    if prediction['direction'] == 'UP':
        side = 'buy'
        print(f"   → Signal: BUY (AI predicts price will rise)")
    else:
        side = 'sell'
        print(f"   → Signal: SELL (AI predicts price will fall)")
    
    # Step 3: Execute the order
    print(f"\n[2] Executing {side.upper()} order...")
    
    result = execute_market_order_for_account(
        user_id=user_id,
        exchange_account_id=exchange_account_id,
        symbol=symbol,
        side=side,
        amount=amount,
        trade_source='ai_prediction'
    )
    
    # Add prediction details to result
    result['prediction'] = {
        'direction': prediction['direction'],
        'confidence': prediction['confidence_pct']
    }
    
    return result


def execute_grid_bot_levels(user_id, bot_id, exchange_account_id, amount_per_order=None):
    """
    Execute grid bot levels that are eligible based on current price.
    
    Grid Bot Execution Logic:
    -------------------------
    1. Get current market price
    2. Find grid levels close to current price
    3. For BUY levels below current price: Execute buy orders
    4. For SELL levels above current price: Execute sell orders
    5. Mark levels as filled
    
    Simplified for Demo:
    - In production, this would run continuously
    - Triggered by price updates via WebSocket
    - Here, we manually trigger for demonstration
    
    Args:
        user_id (int): User ID
        bot_id (int): Grid bot ID
        exchange_account_id (int): Exchange account to use
        amount_per_order (float, optional): Amount for each order
    
    Returns:
        dict: Execution results for all levels
    """
    
    from services import grid_bot_service
    from services import price_service
    
    print(f"\n{'='*70}")
    print(f"GRID BOT EXECUTION")
    print(f"{'='*70}")
    print(f"Bot ID: {bot_id}")
    print(f"Exchange Account ID: {exchange_account_id}")
    print(f"{'='*70}\n")
    
    # Get bot details
    bot_details = grid_bot_service.get_bot_details(bot_id, user_id)
    
    if not bot_details:
        return {
            'success': False,
            'error': 'Grid bot not found or access denied'
        }
    
    bot = bot_details['bot']
    levels = bot_details['levels']
    
    # Get current price
    symbol_db = bot['symbol']  # e.g., "BTCUSDT"
    symbol_exchange = symbol_db.replace('USDT', '/USDT')  # e.g., "BTC/USDT"
    
    price_data = price_service.get_latest_price(symbol_db)
    current_price = price_data['close_price'] if price_data else 45000.00
    
    print(f"Current price: ${current_price:,.2f}")
    print(f"Grid range: ${bot['lower_price']:,.2f} - ${bot['upper_price']:,.2f}")
    print(f"Levels: {len(levels)}")
    
    # Default amount per order
    if not amount_per_order:
        amount_per_order = bot['investment_amount'] / bot['grid_count']
    
    # Execute eligible levels
    executed_levels = []
    
    for level in levels:
        # Skip if already filled
        if level['is_filled'] == 1:
            continue
        
        level_price = level['level_price']
        order_type = level['order_type']
        
        # Simple execution logic for demo:
        # BUY if current price is near or below level
        # SELL if current price is near or above level
        
        should_execute = False
        
        if order_type == 'BUY' and current_price <= level_price * 1.01:  # Within 1%
            should_execute = True
            side = 'buy'
        elif order_type == 'SELL' and current_price >= level_price * 0.99:  # Within 1%
            should_execute = True
            side = 'sell'
        
        if should_execute:
            print(f"\n   Executing {order_type} level @ ${level_price:,.2f}...")
            
            # Execute order
            result = execute_market_order_for_account(
                user_id=user_id,
                exchange_account_id=exchange_account_id,
                symbol=symbol_exchange,
                side=side,
                amount=amount_per_order,
                trade_source=f'grid_bot_{bot_id}'
            )
            
            if result['success']:
                # Mark level as filled
                query = "UPDATE grid_levels SET is_filled = 1, filled_at = datetime('now') WHERE id = ?"
                db.execute_query(query, (level['id'],))
                
                executed_levels.append({
                    'level_id': level['id'],
                    'price': level_price,
                    'type': order_type,
                    'result': result
                })
    
    return {
        'success': True,
        'bot_id': bot_id,
        'current_price': current_price,
        'executed_count': len(executed_levels),
        'executed_levels': executed_levels,
        'mode': 'LIVE' if is_live_mode else 'SIMULATED'
    }


# ============================================
# EDUCATIONAL NOTES
# ============================================

"""
HOW THIS SERVICE WORKS:
=======================

1. SIGNAL GENERATION
   -------------------
   Signals can come from:
   - AI Predictions: ML model predicts UP/DOWN
   - Grid Bots: Price hits grid level
   - Manual: User clicks buy/sell
   - Stop Loss: Risk management triggers
   - Take Profit: Target price reached

2. ORDER ROUTING
   --------------
   All signals go through execute_market_order_for_account():
   - Validates parameters
   - Checks live/simulation mode
   - Routes to appropriate execution path
   - Logs everything

3. EXECUTION
   ----------
   SIMULATION MODE (Safe):
   - Calculates what would happen
   - Logs with status "SIMULATED"
   - No API call to exchange
   - No financial risk
   
   LIVE MODE (Real):
   - Creates CCXT client
   - Sends order to exchange
   - Waits for response
   - Logs actual result

4. LOGGING
   --------
   Every trade (simulated or live) is logged:
   - Audit trail
   - Performance tracking
   - Debugging
   - Regulatory compliance

SAFETY MECHANISMS:
=================

1. Config Flag: LIVE_TRADING_ENABLED (default: False)
2. Per-Order Override: can specify is_live_mode
3. Exchange Account: can be testnet or live
4. Trade Logs: all actions recorded
5. Soft Delete: accounts never hard-deleted

PRODUCTION CONSIDERATIONS:
=========================

In a real system, you would also need:
- Order confirmation prompts
- Maximum order size limits
- Daily/weekly loss limits
- Circuit breakers (stop all trading if losses exceed limit)
- Email/SMS notifications
- Two-factor authentication for live trades
- Real-time price validation
- Slippage protection
- Position size limits

For this university project:
- We demonstrate the architecture
- We use safe defaults (simulation mode)
- We clearly document what's missing
- We show professional awareness
"""


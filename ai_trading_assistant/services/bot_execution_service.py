"""
Bot Execution Service

Handles the execution logic for DCA and Grid bots.
"""

import time
from models.trading_bot_model import trading_bot_model
from services.exchange_trading_service import exchange_trading_service
import services.price_sync_service as price_sync_service


class BotExecutionService:
    """Service for executing trading bot strategies"""
    
    def __init__(self):
        self.running_bots = {}  # Store bot execution states
    
    def execute_dca_bot(self, bot_id, user_id):
        """
        Execute DCA bot strategy
        
        Places base order and sets up DCA orders based on price deviation
        """
        try:
            bot = trading_bot_model.get_bot(bot_id)
            if not bot:
                return {'success': False, 'error': 'Bot not found'}
            
            config = bot['config']
            symbol = bot['symbol']
            side = bot['side']
            is_paper = bot['is_paper_trading']
            
            # Get current price
            price_data = price_sync_service.get_latest_price(symbol)
            if not price_data:
                return {'success': False, 'error': 'Could not fetch current price'}
            
            current_price = price_data['close']
            
            # Extract DCA configuration
            base_order = float(config.get('base_order', 100))
            dca_order = float(config.get('dca_order', 50))
            max_orders = int(config.get('max_orders', 5))
            price_deviation = float(config.get('price_deviation', 1.0)) / 100
            take_profit = float(config.get('take_profit', 2.0)) / 100
            
            orders_placed = []
            
            # Calculate base order amount in base currency
            base_amount = base_order / current_price
            
            # Place base order
            if is_paper:
                # Paper trading - just log the order
                order_id = trading_bot_model.add_bot_order(
                    bot_id=bot_id,
                    symbol=symbol,
                    side=side,
                    order_type='market',
                    price=current_price,
                    amount=base_amount,
                    status='filled' if is_paper else 'pending'
                )
                orders_placed.append({
                    'order_id': order_id,
                    'type': 'base',
                    'price': current_price,
                    'amount': base_amount
                })
            else:
                # Real trading
                result = exchange_trading_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol.replace('USDT', '/USDT'),  # Format for CCXT
                    side=side,
                    amount=base_amount,
                    exchange_name=bot['exchange_name']
                )
                
                if result['success']:
                    order_id = trading_bot_model.add_bot_order(
                        bot_id=bot_id,
                        symbol=symbol,
                        side=side,
                        order_type='market',
                        price=result['price'],
                        amount=base_amount,
                        exchange_order_id=result['order_id'],
                        status='filled'
                    )
                    orders_placed.append({
                        'order_id': order_id,
                        'type': 'base',
                        'price': result['price'],
                        'amount': base_amount
                    })
                else:
                    return {'success': False, 'error': f"Base order failed: {result['error']}"}
            
            # Calculate and place DCA orders
            for i in range(1, max_orders + 1):
                # Calculate DCA order price (lower for buy, higher for sell)
                if side == 'buy':
                    dca_price = current_price * (1 - (price_deviation * i))
                else:
                    dca_price = current_price * (1 + (price_deviation * i))
                
                dca_amount = dca_order / dca_price
                
                # Place limit order
                if is_paper:
                    order_id = trading_bot_model.add_bot_order(
                        bot_id=bot_id,
                        symbol=symbol,
                        side=side,
                        order_type='limit',
                        price=dca_price,
                        amount=dca_amount,
                        status='pending'
                    )
                    orders_placed.append({
                        'order_id': order_id,
                        'type': 'dca',
                        'level': i,
                        'price': dca_price,
                        'amount': dca_amount
                    })
                else:
                    result = exchange_trading_service.execute_limit_order(
                        user_id=user_id,
                        symbol=symbol.replace('USDT', '/USDT'),
                        side=side,
                        amount=dca_amount,
                        price=dca_price,
                        exchange_name=bot['exchange_name']
                    )
                    
                    if result['success']:
                        order_id = trading_bot_model.add_bot_order(
                            bot_id=bot_id,
                            symbol=symbol,
                            side=side,
                            order_type='limit',
                            price=dca_price,
                            amount=dca_amount,
                            exchange_order_id=result['order_id'],
                            status='pending'
                        )
                        orders_placed.append({
                            'order_id': order_id,
                            'type': 'dca',
                            'level': i,
                            'price': dca_price,
                            'amount': dca_amount
                        })
            
            # Calculate take profit price
            if side == 'buy':
                tp_price = current_price * (1 + take_profit)
            else:
                tp_price = current_price * (1 - take_profit)
            
            # Update bot stats
            total_investment = base_order + (dca_order * max_orders)
            trading_bot_model.update_bot_stats(
                bot_id=bot_id,
                total_investment=total_investment,
                orders_placed=len(orders_placed)
            )
            
            return {
                'success': True,
                'bot_id': bot_id,
                'orders_placed': orders_placed,
                'total_investment': total_investment,
                'take_profit_price': tp_price,
                'message': f"DCA bot started with {len(orders_placed)} orders"
            }
            
        except Exception as e:
            print(f"Error executing DCA bot: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_grid_bot(self, bot_id, user_id):
        """
        Execute Grid bot strategy
        
        Places multiple buy/sell limit orders in a grid pattern
        """
        try:
            bot = trading_bot_model.get_bot(bot_id)
            if not bot:
                return {'success': False, 'error': 'Bot not found'}
            
            config = bot['config']
            symbol = bot['symbol']
            side = bot['side']
            is_paper = bot['is_paper_trading']
            
            # Extract Grid configuration
            lower_price = float(config.get('lower_price'))
            upper_price = float(config.get('upper_price'))
            grid_count = int(config.get('grid_count', 10))
            investment = float(config.get('investment', 500))
            mode = config.get('mode', 'arithmetic')
            
            orders_placed = []
            
            # Calculate grid levels
            if mode == 'arithmetic':
                # Equal price differences
                price_step = (upper_price - lower_price) / grid_count
                grid_prices = [lower_price + (price_step * i) for i in range(grid_count + 1)]
            else:
                # Geometric - equal percentage differences
                ratio = (upper_price / lower_price) ** (1 / grid_count)
                grid_prices = [lower_price * (ratio ** i) for i in range(grid_count + 1)]
            
            # Calculate amount per grid
            amount_per_grid = investment / grid_count
            
            # Place orders at each grid level
            for i, grid_price in enumerate(grid_prices):
                # Calculate amount in base currency
                base_amount = amount_per_grid / grid_price
                
                # For buy side: place buy orders below current, sell orders above
                # For sell side: opposite
                order_side = side
                
                if is_paper:
                    order_id = trading_bot_model.add_bot_order(
                        bot_id=bot_id,
                        symbol=symbol,
                        side=order_side,
                        order_type='limit',
                        price=grid_price,
                        amount=base_amount,
                        status='pending'
                    )
                    orders_placed.append({
                        'order_id': order_id,
                        'level': i,
                        'price': grid_price,
                        'amount': base_amount
                    })
                else:
                    result = exchange_trading_service.execute_limit_order(
                        user_id=user_id,
                        symbol=symbol.replace('USDT', '/USDT'),
                        side=order_side,
                        amount=base_amount,
                        price=grid_price,
                        exchange_name=bot['exchange_name']
                    )
                    
                    if result['success']:
                        order_id = trading_bot_model.add_bot_order(
                            bot_id=bot_id,
                            symbol=symbol,
                            side=order_side,
                            order_type='limit',
                            price=grid_price,
                            amount=base_amount,
                            exchange_order_id=result['order_id'],
                            status='pending'
                        )
                        orders_placed.append({
                            'order_id': order_id,
                            'level': i,
                            'price': grid_price,
                            'amount': base_amount
                        })
            
            # Update bot stats
            trading_bot_model.update_bot_stats(
                bot_id=bot_id,
                total_investment=investment,
                orders_placed=len(orders_placed)
            )
            
            return {
                'success': True,
                'bot_id': bot_id,
                'orders_placed': orders_placed,
                'total_investment': investment,
                'grid_count': grid_count,
                'price_range': f"${lower_price:.2f} - ${upper_price:.2f}",
                'message': f"Grid bot started with {len(orders_placed)} orders"
            }
            
        except Exception as e:
            print(f"Error executing Grid bot: {e}")
            return {'success': False, 'error': str(e)}
    
    def stop_bot(self, bot_id):
        """Stop a running bot and cancel all pending orders"""
        try:
            bot = trading_bot_model.get_bot(bot_id)
            if not bot:
                return {'success': False, 'error': 'Bot not found'}
            
            # Get pending orders
            pending_orders = trading_bot_model.get_bot_orders(bot_id, status='pending')
            
            cancelled_count = 0
            for order in pending_orders:
                if not bot['is_paper_trading'] and order.get('exchange_order_id'):
                    # Cancel real exchange order
                    result = exchange_trading_service.cancel_order(
                        user_id=bot['user_id'],
                        order_id=order['exchange_order_id'],
                        symbol=bot['symbol'].replace('USDT', '/USDT'),
                        exchange_name=bot['exchange_name']
                    )
                    if result['success']:
                        trading_bot_model.update_order_status(order['id'], 'cancelled')
                        cancelled_count += 1
                else:
                    # Paper trading - just update status
                    trading_bot_model.update_order_status(order['id'], 'cancelled')
                    cancelled_count += 1
            
            # Update bot status
            trading_bot_model.update_bot_status(bot_id, 'stopped')
            
            return {
                'success': True,
                'bot_id': bot_id,
                'cancelled_orders': cancelled_count,
                'message': f"Bot stopped, {cancelled_count} orders cancelled"
            }
            
        except Exception as e:
            print(f"Error stopping bot: {e}")
            return {'success': False, 'error': str(e)}


# Singleton instance
bot_execution_service = BotExecutionService()


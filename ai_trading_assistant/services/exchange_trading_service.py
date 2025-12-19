"""
Exchange Trading Service

Handles real order execution on connected exchanges using CCXT.

⚠️ WARNING: This service executes REAL trades with REAL money.
Always test on testnet first!
"""

import ccxt
from models.exchange_config_model import exchange_config_model
from decimal import Decimal


class ExchangeTradingService:
    """Service for executing real trades on exchanges"""
    
    # Safety limits (can be configured per user)
    MAX_TRADE_AMOUNT_USD = 1000  # Maximum $1000 per trade
    MAX_DAILY_TRADES = 50         # Maximum 50 trades per day
    ENABLE_SAFETY_CHECKS = True   # Always enabled for safety
    
    def __init__(self):
        self.exchange_instances = {}
    
    def _get_exchange_instance(self, user_id, exchange_name='binance'):
        """
        Get or create exchange instance with user's API keys
        
        Args:
            user_id: User ID
            exchange_name: Exchange name (default: binance)
        
        Returns:
            ccxt.Exchange: Configured exchange instance or None
        """
        cache_key = f"{user_id}_{exchange_name}"
        
        # Return cached instance if exists
        if cache_key in self.exchange_instances:
            return self.exchange_instances[cache_key]
        
        # Get user's exchange config
        config = exchange_config_model.get_exchange_config(user_id, exchange_name)
        if not config:
            print(f"No exchange configuration found for user {user_id} on {exchange_name}")
            return None
        
        try:
            # Initialize exchange based on name
            if exchange_name.lower() == 'binance':
                exchange_class = ccxt.binance
            elif exchange_name.lower() == 'coinbase':
                exchange_class = ccxt.coinbasepro
            elif exchange_name.lower() == 'kraken':
                exchange_class = ccxt.kraken
            else:
                print(f"Unsupported exchange: {exchange_name}")
                return None
            
            # Create exchange instance with API keys
            exchange = exchange_class({
                'apiKey': config['api_key'],
                'secret': config['api_secret'],
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # Spot trading
                }
            })
            
            # Use testnet if configured
            if config['is_testnet']:
                if hasattr(exchange, 'set_sandbox_mode'):
                    exchange.set_sandbox_mode(True)
                    print(f"⚠️ TESTNET MODE enabled for {exchange_name}")
            else:
                print(f"🔴 LIVE TRADING enabled for {exchange_name}")
            
            # Cache the instance
            self.exchange_instances[cache_key] = exchange
            return exchange
            
        except Exception as e:
            print(f"Error initializing exchange {exchange_name}: {e}")
            return None
    
    def execute_market_order(self, user_id, symbol, side, amount, exchange_name='binance'):
        """
        Execute a market order (buy/sell immediately at market price)
        
        Args:
            user_id: User ID
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Amount to trade (in base currency)
            exchange_name: Exchange to use
        
        Returns:
            dict: Order result or None
        """
        try:
            # Safety checks
            if self.ENABLE_SAFETY_CHECKS:
                # Get current price to estimate USD value
                exchange = self._get_exchange_instance(user_id, exchange_name)
                if not exchange:
                    return {'success': False, 'error': 'Exchange not configured'}
                
                ticker = exchange.fetch_ticker(symbol)
                est_usd_value = float(amount) * ticker['last']
                
                if est_usd_value > self.MAX_TRADE_AMOUNT_USD:
                    return {
                        'success': False,
                        'error': f'Trade amount ${est_usd_value:.2f} exceeds safety limit of ${self.MAX_TRADE_AMOUNT_USD}'
                    }
            
            # Execute order
            exchange = self._get_exchange_instance(user_id, exchange_name)
            if not exchange:
                return {'success': False, 'error': 'Exchange not configured'}
            
            order = exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount
            )
            
            return {
                'success': True,
                'order': order,
                'order_id': order['id'],
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': order.get('average') or order.get('price'),
                'status': order['status']
            }
            
        except Exception as e:
            print(f"Error executing market order: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_limit_order(self, user_id, symbol, side, amount, price, exchange_name='binance'):
        """
        Execute a limit order (buy/sell at specific price)
        
        Args:
            user_id: User ID
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Amount to trade
            price: Limit price
            exchange_name: Exchange to use
        
        Returns:
            dict: Order result or None
        """
        try:
            # Safety checks
            if self.ENABLE_SAFETY_CHECKS:
                est_usd_value = float(amount) * float(price)
                if est_usd_value > self.MAX_TRADE_AMOUNT_USD:
                    return {
                        'success': False,
                        'error': f'Trade amount ${est_usd_value:.2f} exceeds safety limit of ${self.MAX_TRADE_AMOUNT_USD}'
                    }
            
            # Execute order
            exchange = self._get_exchange_instance(user_id, exchange_name)
            if not exchange:
                return {'success': False, 'error': 'Exchange not configured'}
            
            order = exchange.create_limit_order(
                symbol=symbol,
                side=side,
                amount=amount,
                price=price
            )
            
            return {
                'success': True,
                'order': order,
                'order_id': order['id'],
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'status': order['status']
            }
            
        except Exception as e:
            print(f"Error executing limit order: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, user_id, order_id, symbol, exchange_name='binance'):
        """Cancel an open order"""
        try:
            exchange = self._get_exchange_instance(user_id, exchange_name)
            if not exchange:
                return {'success': False, 'error': 'Exchange not configured'}
            
            result = exchange.cancel_order(order_id, symbol)
            return {'success': True, 'result': result}
            
        except Exception as e:
            print(f"Error canceling order: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_open_orders(self, user_id, symbol=None, exchange_name='binance'):
        """Get all open orders"""
        try:
            exchange = self._get_exchange_instance(user_id, exchange_name)
            if not exchange:
                return {'success': False, 'error': 'Exchange not configured'}
            
            orders = exchange.fetch_open_orders(symbol)
            return {'success': True, 'orders': orders}
            
        except Exception as e:
            print(f"Error fetching open orders: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_account_balance(self, user_id, exchange_name='binance'):
        """Get account balance from exchange"""
        try:
            exchange = self._get_exchange_instance(user_id, exchange_name)
            if not exchange:
                return {'success': False, 'error': 'Exchange not configured'}
            
            balance = exchange.fetch_balance()
            return {'success': True, 'balance': balance}
            
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_connection(self, user_id, exchange_name='binance'):
        """Test exchange connection and API keys"""
        try:
            exchange = self._get_exchange_instance(user_id, exchange_name)
            if not exchange:
                return {'success': False, 'error': 'Exchange not configured'}
            
            # Try to fetch balance as connection test
            balance = exchange.fetch_balance()
            
            return {
                'success': True,
                'message': 'Connection successful',
                'exchange': exchange_name,
                'testnet': exchange.has['sandbox'] if hasattr(exchange, 'has') else False
            }
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_grid_bot_orders(self, user_id, symbol, lower_price, upper_price, grid_count, investment, exchange_name='binance'):
        """
        Execute grid bot strategy by placing multiple limit orders
        
        Args:
            user_id: User ID
            symbol: Trading pair
            lower_price: Lower price bound
            upper_price: Upper price bound
            grid_count: Number of grid levels
            investment: Total investment amount (USDT)
            exchange_name: Exchange to use
        
        Returns:
            dict: Result with placed orders
        """
        try:
            exchange = self._get_exchange_instance(user_id, exchange_name)
            if not exchange:
                return {'success': False, 'error': 'Exchange not configured'}
            
            # Calculate grid levels
            price_step = (upper_price - lower_price) / grid_count
            amount_per_grid = investment / grid_count
            
            orders = []
            for i in range(grid_count):
                grid_price = lower_price + (price_step * i)
                
                # Calculate amount in base currency (BTC)
                base_amount = amount_per_grid / grid_price
                
                # Place buy limit order
                try:
                    order = self.execute_limit_order(
                        user_id=user_id,
                        symbol=symbol,
                        side='buy',
                        amount=base_amount,
                        price=grid_price,
                        exchange_name=exchange_name
                    )
                    if order['success']:
                        orders.append(order)
                except Exception as e:
                    print(f"Error placing grid order at {grid_price}: {e}")
            
            return {
                'success': True,
                'total_orders': len(orders),
                'orders': orders
            }
            
        except Exception as e:
            print(f"Error executing grid bot orders: {e}")
            return {'success': False, 'error': str(e)}


# Singleton instance
exchange_trading_service = ExchangeTradingService()


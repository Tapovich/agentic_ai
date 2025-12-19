"""
Trading Bot Model

Handles storage and management of DCA and Grid Bot configurations and orders.
"""

import sqlite3
import json
from datetime import datetime

# Database path (same as other models)
DATABASE = 'ai_trading.db'


class TradingBotModel:
    """Model for managing trading bots (DCA and Grid)"""
    
    def __init__(self):
        self.init_tables()
    
    def init_tables(self):
        """Initialize bot-related tables"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Trading bots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bot_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                config TEXT NOT NULL,
                ai_mode INTEGER DEFAULT 0,
                exchange_name TEXT DEFAULT 'binance',
                is_paper_trading INTEGER DEFAULT 1,
                total_investment REAL DEFAULT 0,
                total_profit REAL DEFAULT 0,
                orders_placed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                stopped_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Bot orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER NOT NULL,
                order_id TEXT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                filled_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                exchange_order_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filled_at TIMESTAMP,
                error TEXT,
                FOREIGN KEY (bot_id) REFERENCES trading_bots(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bots_user ON trading_bots(user_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_bot ON bot_orders(bot_id, status)')
        
        conn.commit()
        conn.close()
    
    def create_bot(self, user_id, bot_type, symbol, side, config, ai_mode=False, 
                   exchange_name='binance', is_paper_trading=True):
        """
        Create a new trading bot
        
        Args:
            user_id: User ID
            bot_type: 'dca' or 'grid'
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'buy' or 'sell'
            config: Bot configuration dict
            ai_mode: Whether AI mode is enabled
            exchange_name: Exchange to trade on
            is_paper_trading: If True, no real orders executed
        
        Returns:
            int: Bot ID or None
        """
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_bots 
                (user_id, bot_type, symbol, side, config, ai_mode, exchange_name, is_paper_trading)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, bot_type, symbol, side, json.dumps(config), 
                  int(ai_mode), exchange_name, int(is_paper_trading)))
            
            bot_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return bot_id
        except Exception as e:
            print(f"Error creating bot: {e}")
            return None
    
    def get_bot(self, bot_id):
        """Get bot by ID"""
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM trading_bots WHERE id = ?', (bot_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                bot = dict(row)
                bot['config'] = json.loads(bot['config'])
                bot['ai_mode'] = bool(bot['ai_mode'])
                bot['is_paper_trading'] = bool(bot['is_paper_trading'])
                return bot
            return None
        except Exception as e:
            print(f"Error getting bot: {e}")
            return None
    
    def get_user_bots(self, user_id, bot_type=None, status='active'):
        """Get all bots for a user"""
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if bot_type:
                cursor.execute('''
                    SELECT * FROM trading_bots 
                    WHERE user_id = ? AND bot_type = ? AND status = ?
                    ORDER BY created_at DESC
                ''', (user_id, bot_type, status))
            else:
                cursor.execute('''
                    SELECT * FROM trading_bots 
                    WHERE user_id = ? AND status = ?
                    ORDER BY created_at DESC
                ''', (user_id, status))
            
            rows = cursor.fetchall()
            conn.close()
            
            bots = []
            for row in rows:
                bot = dict(row)
                bot['config'] = json.loads(bot['config'])
                bot['ai_mode'] = bool(bot['ai_mode'])
                bot['is_paper_trading'] = bool(bot['is_paper_trading'])
                bots.append(bot)
            return bots
        except Exception as e:
            print(f"Error getting user bots: {e}")
            return []
    
    def update_bot_status(self, bot_id, status):
        """Update bot status (active, paused, stopped)"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            stopped_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'stopped' else None
            
            cursor.execute('''
                UPDATE trading_bots 
                SET status = ?, stopped_at = ?
                WHERE id = ?
            ''', (status, stopped_at, bot_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating bot status: {e}")
            return False
    
    def update_bot_stats(self, bot_id, total_investment=None, total_profit=None, orders_placed=None):
        """Update bot statistics"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if total_investment is not None:
                updates.append('total_investment = ?')
                params.append(total_investment)
            if total_profit is not None:
                updates.append('total_profit = ?')
                params.append(total_profit)
            if orders_placed is not None:
                updates.append('orders_placed = ?')
                params.append(orders_placed)
            
            if not updates:
                return True
            
            params.append(bot_id)
            query = f"UPDATE trading_bots SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating bot stats: {e}")
            return False
    
    def add_bot_order(self, bot_id, symbol, side, order_type, price, amount, 
                      exchange_order_id=None, status='pending'):
        """Add an order to bot's order history"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bot_orders 
                (bot_id, symbol, side, order_type, price, amount, exchange_order_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bot_id, symbol, side, order_type, price, amount, exchange_order_id, status))
            
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return order_id
        except Exception as e:
            print(f"Error adding bot order: {e}")
            return None
    
    def get_bot_orders(self, bot_id, status=None):
        """Get all orders for a bot"""
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM bot_orders 
                    WHERE bot_id = ? AND status = ?
                    ORDER BY created_at DESC
                ''', (bot_id, status))
            else:
                cursor.execute('''
                    SELECT * FROM bot_orders 
                    WHERE bot_id = ?
                    ORDER BY created_at DESC
                ''', (bot_id,))
            
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting bot orders: {e}")
            return []
    
    def update_order_status(self, order_id, status, filled_amount=None, error=None):
        """Update order status"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            filled_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'filled' else None
            
            if filled_amount is not None:
                cursor.execute('''
                    UPDATE bot_orders 
                    SET status = ?, filled_amount = ?, filled_at = ?, error = ?
                    WHERE id = ?
                ''', (status, filled_amount, filled_at, error, order_id))
            else:
                cursor.execute('''
                    UPDATE bot_orders 
                    SET status = ?, error = ?
                    WHERE id = ?
                ''', (status, error, order_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False
    
    def get_bot_statistics(self, bot_id):
        """Get detailed statistics for a bot"""
        try:
            bot = self.get_bot(bot_id)
            if not bot:
                return None
            
            orders = self.get_bot_orders(bot_id)
            
            filled_orders = [o for o in orders if o['status'] == 'filled']
            pending_orders = [o for o in orders if o['status'] == 'pending']
            
            total_invested = sum(o['price'] * o['filled_amount'] for o in filled_orders if o['side'] == 'buy')
            total_sold = sum(o['price'] * o['filled_amount'] for o in filled_orders if o['side'] == 'sell')
            
            return {
                'bot': bot,
                'total_orders': len(orders),
                'filled_orders': len(filled_orders),
                'pending_orders': len(pending_orders),
                'total_invested': total_invested,
                'total_sold': total_sold,
                'net_profit': total_sold - total_invested,
                'orders': orders
            }
        except Exception as e:
            print(f"Error getting bot statistics: {e}")
            return None
    
    def delete_bot(self, bot_id):
        """Delete a bot and its orders"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            # Delete orders first
            cursor.execute('DELETE FROM bot_orders WHERE bot_id = ?', (bot_id,))
            # Delete bot
            cursor.execute('DELETE FROM trading_bots WHERE id = ?', (bot_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting bot: {e}")
            return False


# Singleton instance
trading_bot_model = TradingBotModel()


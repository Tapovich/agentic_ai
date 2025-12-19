"""
Exchange Configuration Model

Handles storage and retrieval of exchange API credentials (encrypted).
"""

import sqlite3
from cryptography.fernet import Fernet
import os

# Database path (same as other models)
DATABASE = 'ai_trading.db'

# Generate encryption key (in production, store this securely)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)


class ExchangeConfigModel:
    """Model for managing exchange API configurations"""
    
    def __init__(self):
        self.init_table()
    
    def init_table(self):
        """Initialize exchange_configs table"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exchange_name TEXT NOT NULL,
                api_key TEXT NOT NULL,
                api_secret TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_testnet INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, exchange_name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_exchange_config(self, user_id, exchange_name, api_key, api_secret, is_testnet=True):
        """
        Add or update exchange configuration
        
        Args:
            user_id: User ID
            exchange_name: Name of exchange (e.g., 'binance', 'coinbase')
            api_key: API key (will be encrypted)
            api_secret: API secret (will be encrypted)
            is_testnet: Whether to use testnet (default True for safety)
        
        Returns:
            bool: Success status
        """
        try:
            # Encrypt sensitive data
            encrypted_key = cipher.encrypt(api_key.encode()).decode()
            encrypted_secret = cipher.encrypt(api_secret.encode()).decode()
            
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO exchange_configs 
                (user_id, exchange_name, api_key, api_secret, is_testnet, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, exchange_name, encrypted_key, encrypted_secret, is_testnet))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding exchange config: {e}")
            return False
    
    def get_exchange_config(self, user_id, exchange_name):
        """
        Get decrypted exchange configuration
        
        Args:
            user_id: User ID
            exchange_name: Exchange name
        
        Returns:
            dict: Exchange configuration or None
        """
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM exchange_configs 
                WHERE user_id = ? AND exchange_name = ? AND is_active = 1
            ''', (user_id, exchange_name))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Decrypt sensitive data
                api_key = cipher.decrypt(row['api_key'].encode()).decode()
                api_secret = cipher.decrypt(row['api_secret'].encode()).decode()
                
                return {
                    'id': row['id'],
                    'exchange_name': row['exchange_name'],
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'is_testnet': bool(row['is_testnet']),
                    'created_at': row['created_at']
                }
            return None
        except Exception as e:
            print(f"Error getting exchange config: {e}")
            return None
    
    def get_all_user_exchanges(self, user_id):
        """Get all exchange configurations for a user"""
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, exchange_name, is_active, is_testnet, created_at 
                FROM exchange_configs 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error getting user exchanges: {e}")
            return []
    
    def delete_exchange_config(self, user_id, exchange_name):
        """Delete exchange configuration"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM exchange_configs 
                WHERE user_id = ? AND exchange_name = ?
            ''', (user_id, exchange_name))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting exchange config: {e}")
            return False
    
    def toggle_exchange_status(self, user_id, exchange_name, is_active):
        """Enable/disable exchange"""
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE exchange_configs 
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND exchange_name = ?
            ''', (is_active, user_id, exchange_name))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error toggling exchange status: {e}")
            return False


# Singleton instance
exchange_config_model = ExchangeConfigModel()


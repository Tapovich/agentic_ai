"""
Exchange Account Model
Database operations for managing linked exchange accounts.

⚠️ SECURITY WARNING (For University Project):
============================================
This code uses SIMPLE BASE64 ENCODING for educational purposes.
This is NOT real encryption and is NOT secure!

In a real production system, you MUST:
- Use proper encryption (AES-256, Fernet, etc.)
- Store encryption keys in secure vault (AWS KMS, HashiCorp Vault)
- Never commit secrets to git
- Use environment variables
- Implement key rotation
- Add access logging

For this university project, we use base64 to demonstrate the concept,
but we clearly mark it as insecure for educational purposes only.
"""

from models import db
from datetime import datetime
import base64


# ============================================
# SIMPLE ENCODING (NOT ENCRYPTION!)
# ============================================
# ⚠️ For educational purposes only!
# ⚠️ This is NOT secure encryption!
# ⚠️ In production, use proper encryption libraries!

def simple_encode_secret(secret):
    """
    Simple base64 encoding (NOT encryption!).
    
    ⚠️ EDUCATIONAL PURPOSE ONLY - NOT SECURE!
    
    In production, use proper encryption:
    - from cryptography.fernet import Fernet
    - cipher = Fernet(encryption_key)
    - encrypted = cipher.encrypt(secret.encode())
    
    Args:
        secret (str): API secret to encode
    
    Returns:
        str: Base64-encoded secret
    """
    # Convert to bytes, encode to base64, convert back to string
    encoded_bytes = base64.b64encode(secret.encode('utf-8'))
    return encoded_bytes.decode('utf-8')


def simple_decode_secret(encoded_secret):
    """
    Simple base64 decoding (NOT decryption!).
    
    ⚠️ EDUCATIONAL PURPOSE ONLY - NOT SECURE!
    
    Args:
        encoded_secret (str): Base64-encoded secret
    
    Returns:
        str: Decoded secret
    """
    # Convert to bytes, decode from base64, convert back to string
    decoded_bytes = base64.b64decode(encoded_secret.encode('utf-8'))
    return decoded_bytes.decode('utf-8')


def create_exchange_account(user_id, exchange_name, account_label, api_key, api_secret, is_testnet=False):
    """
    Link an exchange account to a user.
    
    ⚠️ Security Note (For University Project):
    ==========================================
    This function uses SIMPLE BASE64 ENCODING (not encryption!) for educational purposes.
    
    What happens:
    1. API secret is base64 encoded (reversible, NOT secure)
    2. Stored in database
    3. Decoded when needed for API calls
    
    Why this is NOT secure:
    - Base64 is encoding, not encryption
    - Anyone with database access can decode it
    - No encryption key needed
    - Trivial to reverse
    
    In a REAL production system, you MUST:
    - Use proper encryption (AES-256, Fernet, etc.)
    - Store encryption keys in secure vault
    - Use environment variables
    - Implement key rotation
    - Add access logging
    
    For this university project:
    - We demonstrate the concept
    - We clearly document the limitation
    - We show what should be done in production
    
    Args:
        user_id (int): User's ID
        exchange_name (str): Exchange name ("binance", "bybit", "okx", "mexc", "bingx")
        account_label (str): Human-readable name
        api_key (str): API key from exchange
        api_secret (str): API secret from exchange
        is_testnet (bool): True for testnet/sandbox mode
    
    Returns:
        dict: Result with account_id and success status
              {"success": True, "account_id": 1}
              {"success": False, "error": "error message"}
    
    Example:
        result = create_exchange_account(
            user_id=1,
            exchange_name="binance",
            account_label="My Binance Testnet",
            api_key="my_api_key",
            api_secret="my_api_secret",
            is_testnet=True
        )
    """
    
    # Validate exchange name
    valid_exchanges = ['binance', 'bybit', 'okx', 'mexc', 'bingx']
    if exchange_name.lower() not in valid_exchanges:
        return {
            'success': False,
            'error': f'Invalid exchange. Must be one of: {", ".join(valid_exchanges)}'
        }
    
    # Validate inputs
    if not api_key or not api_secret:
        return {'success': False, 'error': 'API key and secret are required'}
    
    if not account_label:
        account_label = f"{exchange_name.capitalize()} Account"
    
    # Convert boolean to int (0 or 1) for SQLite
    is_testnet_int = 1 if is_testnet else 0
    
    # ⚠️ EDUCATIONAL ONLY: Simple encoding (NOT encryption!)
    # In production: api_secret_encrypted = proper_encrypt(api_secret, encryption_key)
    api_secret_encoded = simple_encode_secret(api_secret)
    
    try:
        query = """
            INSERT INTO exchange_accounts 
            (user_id, exchange_name, account_label, api_key, api_secret_encrypted, is_testnet, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """
        
        account_id = db.execute_query(query, (
            user_id, exchange_name, account_label, api_key, api_secret_encoded, is_testnet_int
        ))
        
        if account_id:
            print(f"✅ Exchange account created: {account_label} ({exchange_name})")
            return {'success': True, 'account_id': account_id}
        else:
            return {'success': False, 'error': 'Failed to create account'}
            
    except Exception as e:
        print(f"❌ Error creating exchange account: {e}")
        return {'success': False, 'error': str(e)}


def get_exchange_accounts_for_user(user_id, active_only=True):
    """
    Get all exchange accounts for a user.
    
    Security: API secrets are NOT included in this response.
    They're only fetched when needed for actual API calls.
    
    Args:
        user_id (int): User's ID
        active_only (bool): If True, only return active accounts
    
    Returns:
        list: List of exchange account records (WITHOUT api_secret)
    
    Example:
        accounts = get_exchange_accounts_for_user(1)
        for account in accounts:
            print(f"{account['account_label']}: {account['exchange_name']}")
            print(f"   Testnet: {account['is_testnet']}")
            print(f"   API Key: {account['api_key'][:10]}...")  # Show first 10 chars only
    """
    
    if active_only:
        query = """
            SELECT id, user_id, exchange_name, account_label, api_key, is_testnet, is_active, created_at
            FROM exchange_accounts
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """
    else:
        query = """
            SELECT id, user_id, exchange_name, account_label, api_key, is_testnet, is_active, created_at
            FROM exchange_accounts
            WHERE user_id = ?
            ORDER BY created_at DESC
        """
    
    # Note: We don't return api_secret in the list for security
    # Only fetch it when actually needed for API calls
    
    accounts = db.fetch_all(query, (user_id,))
    
    # Mask API keys for security (show only first 10 characters)
    if accounts:
        for account in accounts:
            if account.get('api_key'):
                full_key = account['api_key']
                account['api_key_masked'] = full_key[:10] + '...' if len(full_key) > 10 else full_key
    
    return accounts if accounts else []


def get_exchange_account_by_id(account_id, user_id):
    """
    Get exchange account WITH api_secret (for API calls).
    
    ⚠️ Security: This function returns the API secret!
    - Only call when you need to make API requests
    - Never expose secret to frontend or logs
    - Never return to client-side JavaScript
    
    Args:
        account_id (int): Account ID
        user_id (int): User ID (for security verification)
    
    Returns:
        dict: Complete account details including DECODED api_secret
              None if not found or access denied
    
    Security Check:
        - Verifies account belongs to user (prevents unauthorized access)
        - Only returns if user_id matches
    """
    
    query = """
        SELECT * FROM exchange_accounts
        WHERE id = ? AND user_id = ? AND is_active = 1
    """
    
    account = db.fetch_one(query, (account_id, user_id))
    
    if account:
        # ⚠️ Decode the api_secret (base64, not real encryption!)
        # In production: account['api_secret'] = proper_decrypt(account['api_secret_encrypted'], key)
        try:
            account['api_secret'] = simple_decode_secret(account['api_secret_encrypted'])
        except Exception as e:
            print(f"❌ Error decoding api_secret: {e}")
            account['api_secret'] = None
    
    return account


def deactivate_exchange_account(account_id, user_id):
    """
    Deactivate an exchange account (set is_active = 0).
    
    Args:
        account_id (int): Account ID
        user_id (int): User ID (for verification)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    query = """
        UPDATE exchange_accounts
        SET is_active = 0
        WHERE id = ? AND user_id = ?
    """
    
    result = db.execute_query(query, (account_id, user_id))
    return result is not None


def delete_exchange_account(account_id, user_id):
    """
    Delete an exchange account.
    
    Implementation: SOFT DELETE (safer approach)
    - Sets is_active = 0 instead of deleting the row
    - Preserves data for audit trail
    - Can be reactivated if needed
    - Associated trade logs remain intact
    
    Alternative: Hard delete (permanently removes row)
    - Use: DELETE FROM exchange_accounts WHERE id = ?
    - More thorough but loses history
    - Cascade deletes trade logs
    
    For this project, we use soft delete for safety.
    
    Args:
        account_id (int): Account ID to delete
        user_id (int): User ID (for security verification)
    
    Returns:
        dict: Result with success status
    """
    
    # Soft delete: Set is_active = 0
    # This preserves the record for audit purposes
    query = """
        UPDATE exchange_accounts
        SET is_active = 0
        WHERE id = ? AND user_id = ?
    """
    
    result = db.execute_query(query, (account_id, user_id))
    
    if result:
        print(f"✅ Exchange account {account_id} deactivated (soft delete)")
        return {'success': True, 'message': 'Account removed successfully'}
    else:
        return {'success': False, 'error': 'Account not found or access denied'}


# ============================================
# TRADE LOGGING FUNCTIONS
# ============================================

def log_exchange_trade(user_id, exchange_account_id, symbol, side, amount, price, 
                       status='NEW', exchange_order_id=None, raw_response=None, 
                       trade_source='manual', fee=0, fee_currency=None, error_message=None):
    """
    Log a trade executed (or attempted) on an exchange.
    
    Args:
        user_id (int): User's ID
        exchange_account_id (int): Which exchange account was used
        symbol (str): Trading pair (e.g., "BTCUSDT")
        side (str): "BUY" or "SELL"
        amount (float): Amount traded
        price (float): Execution price
        status (str): Order status ("NEW", "FILLED", "REJECTED", etc.)
        exchange_order_id (str, optional): Order ID from exchange
        raw_response (str, optional): Full JSON response from exchange
        trade_source (str): What triggered this trade
        fee (float): Trading fee amount
        fee_currency (str): Fee currency
        error_message (str, optional): Error if trade failed
    
    Returns:
        int: Log ID if successful, None if failed
    """
    
    # Calculate total value
    total_value = amount * price
    
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


def update_trade_log_status(log_id, status, filled_at=None, error_message=None):
    """
    Update the status of a trade log.
    
    Args:
        log_id (int): Trade log ID
        status (str): New status
        filled_at (str, optional): Timestamp when filled
        error_message (str, optional): Error message if failed
    
    Returns:
        bool: True if successful
    """
    
    if filled_at:
        query = """
            UPDATE exchange_trade_logs
            SET status = ?, filled_at = ?, error_message = ?
            WHERE id = ?
        """
        result = db.execute_query(query, (status, filled_at, error_message, log_id))
    else:
        query = """
            UPDATE exchange_trade_logs
            SET status = ?, error_message = ?
            WHERE id = ?
        """
        result = db.execute_query(query, (status, error_message, log_id))
    
    return result is not None


def get_user_trade_logs(user_id, limit=50):
    """
    Get trade logs for a user.
    
    Args:
        user_id (int): User's ID
        limit (int): Maximum number of records to return
    
    Returns:
        list: List of trade log records
    """
    
    query = """
        SELECT tl.*, ea.exchange_name, ea.account_label
        FROM exchange_trade_logs tl
        JOIN exchange_accounts ea ON tl.exchange_account_id = ea.id
        WHERE tl.user_id = ?
        ORDER BY tl.created_at DESC
        LIMIT ?
    """
    
    logs = db.fetch_all(query, (user_id, limit))
    return logs if logs else []


def get_trade_statistics(user_id, symbol=None):
    """
    Get trading statistics for a user.
    
    Args:
        user_id (int): User's ID
        symbol (str, optional): Filter by symbol
    
    Returns:
        dict: Statistics about trades
    """
    
    if symbol:
        query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'FILLED' THEN 1 ELSE 0 END) as filled_trades,
                SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buy_trades,
                SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sell_trades,
                SUM(total_value) as total_volume,
                SUM(fee) as total_fees
            FROM exchange_trade_logs
            WHERE user_id = ? AND symbol = ?
        """
        stats = db.fetch_one(query, (user_id, symbol))
    else:
        query = """
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'FILLED' THEN 1 ELSE 0 END) as filled_trades,
                SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buy_trades,
                SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sell_trades,
                SUM(total_value) as total_volume,
                SUM(fee) as total_fees
            FROM exchange_trade_logs
            WHERE user_id = ?
        """
        stats = db.fetch_one(query, (user_id,))
    
    return stats


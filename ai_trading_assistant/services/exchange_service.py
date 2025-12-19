"""
Centralized Exchange Service (TASK 48)

Single source of truth for all exchange connections.
Provides hardened, consistent interface for CCXT exchange clients.

Purpose:
- Centralize exchange configuration
- Consistent error handling across all exchange operations
- Connection testing and validation
- Safe defaults and rate limiting

Usage:
    from services.exchange_service import get_ccxt_client, test_exchange_connection
    
    # Get configured client
    client = get_ccxt_client("binance", api_key, api_secret)
    
    # Test connection
    result = test_exchange_connection("binance", api_key, api_secret)
"""

import ccxt
from typing import Optional, Dict, Any, Tuple


# ============================================
# SUPPORTED EXCHANGES
# ============================================

SUPPORTED_EXCHANGES = {
    'binance': {
        'class': ccxt.binance,
        'name': 'Binance',
        'has_testnet': True,
        'description': 'World\'s largest crypto exchange'
    },
    'bybit': {
        'class': ccxt.bybit,
        'name': 'Bybit',
        'has_testnet': True,
        'description': 'Popular derivatives exchange'
    },
    'okx': {
        'class': ccxt.okx,
        'name': 'OKX',
        'has_testnet': True,
        'description': 'Major exchange with spot and futures'
    },
    'mexc': {
        'class': ccxt.mexc,
        'name': 'MEXC',
        'has_testnet': False,
        'description': 'Wide selection of altcoins'
    },
    'bingx': {
        'class': ccxt.bingx,
        'name': 'BingX',
        'has_testnet': False,
        'description': 'Copy trading and derivatives'
    }
}


def get_ccxt_client(exchange_name: str, api_key: Optional[str] = None, 
                    api_secret: Optional[str] = None, is_testnet: bool = False) -> Optional[ccxt.Exchange]:
    """
    Get configured CCXT exchange client - SINGLE SOURCE OF TRUTH (TASK 48).
    
    All exchange connections in the system MUST use this function.
    
    Args:
        exchange_name (str): Exchange name ("binance", "bybit", "okx", "mexc", "bingx")
        api_key (str, optional): API key for authentication
        api_secret (str, optional): API secret for authentication
        is_testnet (bool): Use testnet/sandbox mode (default False)
    
    Returns:
        ccxt.Exchange: Configured exchange client
        None: If exchange not supported or configuration failed
    
    Features:
        - Rate limiting enabled automatically
        - Testnet mode support
        - Consistent configuration across all exchanges
        - Clear error messages
    
    Example:
        >>> client = get_ccxt_client("binance", api_key="...", api_secret="...")
        >>> if client:
        >>>     balances = client.fetch_balance()
    
    Security Note:
        API keys should be encrypted in database and decrypted only when needed.
    """
    
    # Normalize exchange name
    exchange_name = exchange_name.lower().strip()
    
    print(f"\n{'='*70}")
    print(f"EXCHANGE SERVICE - Creating Client")
    print(f"Exchange: {exchange_name}")
    print(f"Testnet: {is_testnet}")
    print(f"{'='*70}")
    
    # Check if exchange is supported
    if exchange_name not in SUPPORTED_EXCHANGES:
        error_msg = f"Exchange '{exchange_name}' is not supported"
        print(f"❌ {error_msg}")
        print(f"   Supported exchanges: {', '.join(SUPPORTED_EXCHANGES.keys())}")
        raise ValueError(error_msg)
    
    try:
        exchange_info = SUPPORTED_EXCHANGES[exchange_name]
        ExchangeClass = exchange_info['class']
        
        # Build configuration with safe defaults
        config = {
            'enableRateLimit': True,  # Critical: prevents rate limit bans
            'timeout': 30000,  # 30 seconds timeout
            'rateLimit': 1000,  # Minimum 1 second between requests
        }
        
        # Add API credentials if provided
        if api_key and api_secret:
            config['apiKey'] = api_key
            config['secret'] = api_secret
            print(f"✅ API credentials provided")
        else:
            print(f"ℹ️  No credentials - public data only")
        
        # Initialize exchange
        exchange = ExchangeClass(config)
        
        # Configure testnet mode if requested
        if is_testnet:
            if exchange_info['has_testnet']:
                exchange.set_sandbox_mode(True)
                print(f"✅ Testnet mode enabled for {exchange_info['name']}")
            else:
                print(f"⚠️  {exchange_info['name']} does not support testnet")
                print(f"   Using production mode")
        
        print(f"✅ {exchange_info['name']} client created successfully")
        print(f"{'='*70}\n")
        
        return exchange
        
    except ValueError as e:
        # Re-raise ValueError (unsupported exchange)
        raise
        
    except Exception as e:
        print(f"❌ Error creating {exchange_name} client: {e}")
        print(f"{'='*70}\n")
        import traceback
        traceback.print_exc()
        return None


def test_exchange_connection(exchange_name: str, api_key: str, api_secret: str, 
                            is_testnet: bool = False) -> Dict[str, Any]:
    """
    Test exchange connection by fetching balance (TASK 48).
    
    This is the definitive connection test - if balance fetch works,
    the connection is properly configured.
    
    Args:
        exchange_name (str): Exchange name
        api_key (str): API key
        api_secret (str): API secret
        is_testnet (bool): Use testnet mode
    
    Returns:
        dict: Test result
              {
                  "ok": True/False,
                  "exchange": "binance",
                  "message": "Success message or error",
                  "balances_sample": {"USDT": 1000.0, ...} (if success),
                  "error_type": "auth_error" | "network_error" | "unknown" (if failure)
              }
    
    Example:
        >>> result = test_exchange_connection("binance", "key", "secret")
        >>> if result['ok']:
        >>>     print(f"✅ Connected: {result['message']}")
        >>> else:
        >>>     print(f"❌ Failed: {result['error']}")
    
    Error Types:
        - auth_error: Invalid API key/secret
        - network_error: Cannot reach exchange
        - permission_error: API key lacks permissions
        - unknown: Other errors
    """
    
    print(f"\n{'='*70}")
    print(f"TESTING EXCHANGE CONNECTION")
    print(f"Exchange: {exchange_name}")
    print(f"Testnet: {is_testnet}")
    print(f"{'='*70}")
    
    try:
        # Get client
        client = get_ccxt_client(exchange_name, api_key, api_secret, is_testnet)
        
        if not client:
            return {
                'ok': False,
                'exchange': exchange_name,
                'message': 'Failed to create exchange client',
                'error_type': 'unknown'
            }
        
        # Test connection by fetching balance
        print(f"📊 Fetching balance from {exchange_name}...")
        balance_response = client.fetch_balance()
        
        # Extract non-zero balances
        balances_sample = {}
        balance_info = balance_response.get('total', {})
        
        if isinstance(balance_info, dict):
            for currency, amount in balance_info.items():
                if amount and amount > 0:
                    balances_sample[currency] = float(amount)
        
        # Success!
        print(f"✅ Balance fetched successfully")
        print(f"   Found {len(balances_sample)} non-zero balances")
        print(f"{'='*70}\n")
        
        return {
            'ok': True,
            'exchange': exchange_name,
            'message': f'Successfully connected to {SUPPORTED_EXCHANGES[exchange_name]["name"]}',
            'balances_sample': balances_sample,
            'total_assets': len(balances_sample)
        }
        
    except ccxt.AuthenticationError as e:
        # Invalid API key or secret
        error_msg = str(e)
        print(f"❌ Authentication Error: {error_msg}")
        print(f"{'='*70}\n")
        
        return {
            'ok': False,
            'exchange': exchange_name,
            'message': 'Authentication failed - check API key and secret',
            'error': error_msg,
            'error_type': 'auth_error',
            'suggestion': 'Verify API key and secret are correct'
        }
        
    except ccxt.PermissionDenied as e:
        # API key lacks required permissions
        error_msg = str(e)
        print(f"❌ Permission Denied: {error_msg}")
        print(f"{'='*70}\n")
        
        return {
            'ok': False,
            'exchange': exchange_name,
            'message': 'API key lacks required permissions',
            'error': error_msg,
            'error_type': 'permission_error',
            'suggestion': 'Enable "Read" permissions on exchange API key settings'
        }
        
    except ccxt.NetworkError as e:
        # Cannot reach exchange
        error_msg = str(e)
        print(f"❌ Network Error: {error_msg}")
        print(f"{'='*70}\n")
        
        return {
            'ok': False,
            'exchange': exchange_name,
            'message': 'Cannot connect to exchange',
            'error': error_msg,
            'error_type': 'network_error',
            'suggestion': 'Check internet connection and exchange status'
        }
        
    except ValueError as e:
        # Unsupported exchange
        error_msg = str(e)
        print(f"❌ Configuration Error: {error_msg}")
        print(f"{'='*70}\n")
        
        return {
            'ok': False,
            'exchange': exchange_name,
            'message': error_msg,
            'error_type': 'unsupported',
            'suggestion': f'Use one of: {", ".join(SUPPORTED_EXCHANGES.keys())}'
        }
        
    except Exception as e:
        # Unknown error
        error_msg = str(e)
        print(f"❌ Unexpected Error: {error_msg}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")
        
        return {
            'ok': False,
            'exchange': exchange_name,
            'message': 'Unexpected error occurred',
            'error': error_msg,
            'error_type': 'unknown',
            'suggestion': 'Check server logs for details'
        }


def get_exchange_client_from_account(account: Dict[str, Any]) -> Optional[ccxt.Exchange]:
    """
    Get CCXT client from exchange account dictionary.
    
    Convenience function for loading client from database records.
    
    Args:
        account (dict): Exchange account dictionary with keys:
                       - exchange_name: str
                       - api_key: str
                       - api_secret_encrypted: str (or api_secret)
                       - is_testnet: int (0 or 1)
    
    Returns:
        ccxt.Exchange: Configured client or None
    
    Example:
        >>> account = db.fetch_one("SELECT * FROM exchange_accounts WHERE id = ?", (account_id,))
        >>> client = get_exchange_client_from_account(account)
    """
    
    if not account:
        return None
    
    try:
        exchange_name = account.get('exchange_name', '').lower()
        api_key = account.get('api_key', '')
        
        # Handle both encrypted and plain secret (for backward compatibility)
        api_secret = account.get('api_secret_encrypted') or account.get('api_secret', '')
        
        is_testnet = bool(account.get('is_testnet', 0))
        
        return get_ccxt_client(exchange_name, api_key, api_secret, is_testnet)
        
    except Exception as e:
        print(f"❌ Error creating client from account: {e}")
        return None


def list_supported_exchanges() -> Dict[str, Dict[str, Any]]:
    """
    Get list of supported exchanges with their details.
    
    Returns:
        dict: Exchange information dictionary
    
    Example:
        >>> exchanges = list_supported_exchanges()
        >>> for name, info in exchanges.items():
        >>>     print(f"{info['name']}: {info['description']}")
    """
    
    return {
        name: {
            'name': info['name'],
            'description': info['description'],
            'has_testnet': info['has_testnet']
        }
        for name, info in SUPPORTED_EXCHANGES.items()
    }


if __name__ == '__main__':
    # Test the exchange service
    print("\n" + "="*70)
    print("TESTING EXCHANGE SERVICE")
    print("="*70 + "\n")
    
    # Test 1: List supported exchanges
    print("Test 1: List Supported Exchanges")
    exchanges = list_supported_exchanges()
    for name, info in exchanges.items():
        testnet_str = "✅" if info['has_testnet'] else "❌"
        print(f"  {name:10} - {info['name']:15} - {info['description']:40} [Testnet: {testnet_str}]")
    print()
    
    # Test 2: Create client without credentials (public data only)
    print("Test 2: Create Public Client (Binance)")
    try:
        client = get_ccxt_client("binance")
        if client:
            ticker = client.fetch_ticker('BTC/USDT')
            print(f"  BTC/USDT Price: ${ticker['last']:,.2f}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 3: Try unsupported exchange
    print("Test 3: Unsupported Exchange (Should Fail)")
    try:
        client = get_ccxt_client("fake_exchange")
    except ValueError as e:
        print(f"  Expected error: {e}")
    print()
    
    print("="*70)
    print("✅ EXCHANGE SERVICE TEST COMPLETE")
    print("="*70 + "\n")


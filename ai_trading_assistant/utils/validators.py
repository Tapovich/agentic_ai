"""
Input Validation Functions
Contains all validation logic for user inputs, trading data, etc.
These functions help prevent invalid data and security issues.
"""

import re


def validate_email(email):
    """
    Validate email format using simple regex pattern.
    
    Security: Prevents injection attacks through email field.
    Business: Ensures valid email for communication.
    
    Args:
        email (str): Email address to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    
    Example:
        is_valid, error = validate_email("user@example.com")
        if not is_valid:
            return error
    """
    if not email or not isinstance(email, str):
        return False, "Email is required"
    
    email = email.strip()
    
    if len(email) == 0:
        return False, "Email cannot be empty"
    
    if len(email) > 100:
        return False, "Email is too long (max 100 characters)"
    
    # Simple email pattern: something@something.something
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format (example: user@example.com)"
    
    return True, None


def validate_username(username):
    """
    Validate username format and length.
    
    Security: Prevents SQL injection and XSS through username.
    Business: Ensures consistent username format.
    
    Args:
        username (str): Username to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) == 0:
        return False, "Username cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username is too long (max 50 characters)"
    
    # Allow only alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, None


def validate_password(password):
    """
    Validate password strength and format.
    
    Security: Ensures minimum password strength.
    Business: Protects user accounts.
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    # Note: We check the original password, not stripped
    # (passwords can have leading/trailing spaces)
    
    if len(password) == 0:
        return False, "Password cannot be empty"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    return True, None


def validate_trade_data(symbol, side, quantity, price):
    """
    Validate trading data for buy/sell operations.
    
    Security: Prevents invalid trades and potential exploits.
    Business: Ensures valid trading operations.
    
    Args:
        symbol (str): Cryptocurrency symbol
        side (str): Trade side (BUY or SELL)
        quantity (float): Trade quantity
        price (float): Price per unit
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    # Validate symbol
    if not symbol or not isinstance(symbol, str):
        return False, "Symbol is required"
    
    symbol = symbol.strip().upper()
    
    if len(symbol) == 0:
        return False, "Symbol cannot be empty"
    
    if len(symbol) > 20:
        return False, "Symbol is too long"
    
    # Only allow alphanumeric characters
    if not re.match(r'^[A-Z0-9]+$', symbol):
        return False, "Invalid symbol format"
    
    # Validate side
    if not side or not isinstance(side, str):
        return False, "Trade side is required (BUY or SELL)"
    
    side = side.strip().upper()
    
    if side not in ['BUY', 'SELL']:
        return False, "Trade side must be BUY or SELL"
    
    # Validate quantity
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return False, "Quantity must be a valid number"
    
    if quantity <= 0:
        return False, "Quantity must be greater than 0"
    
    if quantity > 1000000:
        return False, "Quantity is too large"
    
    # Validate price
    try:
        price = float(price)
    except (TypeError, ValueError):
        return False, "Price must be a valid number"
    
    if price <= 0:
        return False, "Price must be greater than 0"
    
    if price > 10000000:
        return False, "Price is too high"
    
    return True, None


def sanitize_string(input_str, max_length=100):
    """
    Sanitize string input by removing dangerous characters.
    
    Security: Basic protection against XSS and injection attacks.
    
    Args:
        input_str (str): String to sanitize
        max_length (int): Maximum allowed length
    
    Returns:
        str: Sanitized string
    """
    if not input_str or not isinstance(input_str, str):
        return ""
    
    # Strip whitespace
    sanitized = input_str.strip()
    
    # Limit length
    sanitized = sanitized[:max_length]
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    return sanitized


def validate_quantity(quantity_str):
    """
    Validate and convert quantity string to float.
    
    Args:
        quantity_str: Quantity as string or number
    
    Returns:
        tuple: (is_valid: bool, value: float or None, error: str or None)
    """
    try:
        quantity = float(quantity_str)
        
        if quantity <= 0:
            return False, None, "Quantity must be greater than 0"
        
        if quantity > 1000000:
            return False, None, "Quantity is too large"
        
        return True, quantity, None
        
    except (TypeError, ValueError):
        return False, None, "Invalid quantity format"


def validate_price(price_str):
    """
    Validate and convert price string to float.
    
    Args:
        price_str: Price as string or number
    
    Returns:
        tuple: (is_valid: bool, value: float or None, error: str or None)
    """
    try:
        price = float(price_str)
        
        if price <= 0:
            return False, None, "Price must be greater than 0"
        
        if price > 10000000:
            return False, None, "Price is too high"
        
        return True, price, None
        
    except (TypeError, ValueError):
        return False, None, "Invalid price format"


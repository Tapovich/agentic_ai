"""
Models Package
This package contains all database-related code including:
- Database connection utilities
- User model
- Trading model
- Portfolio model
- Trade history model
- Price data model
"""

# Import simple database helper functions (recommended for students)
from .db import (
    get_connection,
    execute_query,
    fetch_all,
    fetch_one,
    test_connection
)

# Import user model functions
from . import user_model

# Import trading model functions
from . import trading_model

# This file makes the 'models' directory a Python package


"""
Services Package
This package contains business logic and services including:
- AI prediction service (machine learning model)
- Trading service (buy/sell operations)
- Price data service
"""

# Import AI services for easy access
from .train_model import train_model, load_model
from .prediction_service import (
    predict_price_movement,
    save_prediction_to_db,
    get_latest_prediction,
    generate_and_save_prediction
)

# This file makes the 'services' directory a Python package


# Getting Started

This guide will help you install, configure, and run the AI Trading Assistant platform on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Python 3.9 or 3.10 recommended)
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Code editor** (VS Code, PyCharm, or similar)

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

Should output: `Python 3.8.x` or higher

## Installation Steps

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>

# Navigate to the project directory
cd ai_trading_assistant
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Key Dependencies:**
- `Flask`: Web framework
- `ccxt`: Exchange connectivity
- `pandas`: Data manipulation
- `scikit-learn`: Machine learning
- `joblib`: Model serialization
- `werkzeug`: Security utilities

### 4. Set Up Environment Variables

Create a `.env` file in the project root (or set environment variables manually):

```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
DEBUG=True

# Database
DATABASE_PATH=ai_trading.db

# External APIs (Optional)
CMC_API_KEY=your-coinmarketcap-api-key
FEAR_GREED_API_URL=https://api.alternative.me/fng/

# Exchange API Keys (for testing - use testnet!)
# DO NOT commit real API keys to version control
```

**Important**: 
- Change `SECRET_KEY` to a random string
- For production, set `DEBUG=False`
- Never commit `.env` to Git (add to `.gitignore`)

### 5. Initialize the Database

The database will be created automatically on first run, but you can also initialize it manually:

```bash
# Run database initialization script (if available)
python init_db.py

# Or just start the app - it will create tables automatically
```

### 6. (Optional) Train AI Models

If you want to use AI-based predictions:

```bash
# Train the prediction models
python services/train_advanced_ai_model.py
```

This will:
- Fetch historical OHLCV data
- Calculate technical indicators
- Train RandomForest models
- Save models to `models/` directory

**Note**: Training requires historical price data. The script will sync data from Binance automatically.

## Running the Application

### Start the Flask Development Server

```bash
# Make sure virtual environment is activated
python app.py
```

You should see output like:

```
 * Running on http://127.0.0.1:5001
 * Debug mode: on
```

### Access the Application

Open your browser and navigate to:

```
http://localhost:5001
```

Or:

```
http://127.0.0.1:5001
```

### Create an Account

1. Click **"Register"** on the login page
2. Enter username, email, and password
3. Click **"Create Account"**
4. Log in with your credentials

## Quick Setup Guide

### 1. Sync Price History

Before using predictions or bots, sync historical price data:

1. Navigate to **Dashboard**
2. Click **"Sync Latest Prices"** button
3. Wait for data to be fetched (may take 30-60 seconds)

### 2. View Indicators

1. Select a symbol (e.g., BTCUSDT) from the dropdown
2. Click **"Refresh"** in the Indicators section
3. View EMAs, RSI, MACD, and EMA Signals

### 3. Try Advanced Prediction

1. Navigate to **Advanced Prediction** (from navigation menu)
2. Select symbol and timeframe
3. Choose mode: **AI** or **Indicator**
4. Click **"Get Prediction"**
5. View the prediction chart and recommendation

### 4. (Optional) Connect Exchange Account

**⚠️ Use Testnet Only for Learning!**

1. Navigate to **Exchange Accounts**
2. Select exchange (e.g., Binance)
3. Enter **testnet** API credentials:
   - Get testnet API keys from: [testnet.binance.vision](https://testnet.binance.vision)
4. Check **"Use Testnet"** checkbox
5. Click **"Link Exchange Account"**
6. Click **"Test Connection"** to verify


### Issue: "ModuleNotFoundError"

**Solution**: Make sure virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate  # Activate venv
pip install -r requirements.txt
```

### Issue: Database errors on startup

**Solution**: Delete the old database and let it recreate:

```bash
rm ai_trading.db
python app.py
```

### Issue: "Port 5000 already in use"

**Solution**: Either:
1. Stop the other process using port 5000
2. Or change the port in `app.py`:

```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

### Issue: API rate limits when syncing prices

**Solution**: 
- Wait a few minutes between sync requests
- CCXT has rate limiting enabled automatically
- Use cached data when possible

### Issue: "Not enough data" error for indicators

**Solution**:
- Click **"Sync Price History Now"** button
- System needs at least 200 candles for EMA 200
- Wait for sync to complete

## Configuration Options

### Database Configuration

In `app.py` or via environment variables:

```python
DATABASE_PATH = 'ai_trading.db'  # SQLite database file
```

### Flask Configuration

```python
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['DEBUG'] = True  # False for production
```

### External API Configuration

```python
CMC_API_KEY = os.environ.get('CMC_API_KEY', '')
FEAR_GREED_API_URL = 'https://api.alternative.me/fng/'
```
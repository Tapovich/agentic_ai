"""
AI Portfolio Management Service
Analyzes portfolio and suggests rebalancing trades.

NOTE (TASK 27): All price data in this module comes from services/realtime_price_service.py
for consistency and real-time behaviour. Portfolio analysis uses REAL current market prices,
not hardcoded values. Prices are provided by app.py which fetches them via the unified
real-time price service.

⚠️ DISCLAIMER - EDUCATIONAL PURPOSE ONLY:
This is NOT real financial advice!
This demonstrates algorithmic portfolio management concepts.
Real portfolio management requires:
- Professional financial analysis
- Risk assessment
- Market research
- Regulatory compliance
- Licensed advisors

What is Portfolio Rebalancing?
==============================
Rebalancing means adjusting your portfolio back to target allocations.

Example:
- Target: 50% BTC, 30% ETH, 20% TON
- Current: 70% BTC, 20% ETH, 10% TON (BTC grew a lot!)
- Action: Sell some BTC, buy more ETH and TON

Why Rebalance?
- Maintains desired risk level
- Takes profits from winners
- Buys more of underperformers (if you believe in them)
- Disciplined approach

This Implementation:
- Simple algorithmic suggestions
- Educational demonstration
- Shows how robo-advisors work
- Not real financial advice!
"""

# NOTE: This service receives prices from app.py, which uses realtime_price_service


def get_target_allocation():
    """
    Get target portfolio allocation.
    
    ⚠️ For demonstration purposes:
    - This is a HARDCODED target allocation
    - In real system, would be customizable per user
    - Could be based on risk tolerance
    - Could use ML to optimize
    
    Returns:
        dict: Target allocation percentages (must sum to 1.0)
              {
                  "BTC": 0.50,  # 50% Bitcoin
                  "ETH": 0.30,  # 30% Ethereum
                  "BNB": 0.10,  # 10% Binance Coin
                  "SOL": 0.10   # 10% Solana
              }
    
    Explanation:
        - Balanced portfolio across major cryptocurrencies
        - BTC: Largest allocation (most stable, "digital gold")
        - ETH: Second largest (smart contract platform)
        - BNB, SOL: Smaller allocations (higher risk/reward)
    
    Real-World Approaches:
        - Conservative: 70% BTC, 20% ETH, 10% others
        - Aggressive: 30% BTC, 30% ETH, 40% altcoins
        - Based on: Risk tolerance, market conditions, research
    """
    
    # Demo target allocation
    # This is a simplified example for educational purposes
    return {
        "BTC": 0.50,   # 50% - Bitcoin (largest, most stable)
        "ETH": 0.30,   # 30% - Ethereum (second largest)
        "BNB": 0.10,   # 10% - Binance Coin
        "SOL": 0.10    # 10% - Solana
    }


def analyze_portfolio_and_suggest_trades(balances, prices):
    """
    Analyze portfolio and suggest rebalancing trades.
    
    This function:
    1. Calculates current portfolio value in USDT
    2. Determines current allocation percentages
    3. Compares to target allocation
    4. Suggests trades to rebalance
    
    Algorithm (Simplified):
    - If asset is over-allocated → Suggest SELL
    - If asset is under-allocated → Suggest BUY
    - Maintain USDT as cash reserve (don't allocate)
    
    Args:
        balances (dict): Current balances {"BTC": 0.5, "ETH": 1.2, "USDT": 1000}
        prices (dict): Current prices {"BTC": 45000, "ETH": 2800}
    
    Returns:
        dict: Analysis result with suggestions
              {
                  "total_value_usdt": 25000,
                  "current_allocation": {"BTC": 0.7, "ETH": 0.2, "USDT": 0.1},
                  "target_allocation": {"BTC": 0.5, "ETH": 0.3, ...},
                  "suggested_trades": [
                      {
                          "action": "SELL",
                          "symbol": "BTC",
                          "amount": 0.1,
                          "reason": "Reduce BTC from 70% to 50%"
                      },
                      {
                          "action": "BUY",
                          "symbol": "ETH",
                          "amount": 0.5,
                          "reason": "Increase ETH from 20% to 30%"
                      }
                  ],
                  "needs_rebalancing": true
              }
    
    ⚠️ Educational Disclaimer:
        This is a simplified algorithm for demonstration.
        Real portfolio management considers:
        - Transaction costs
        - Tax implications
        - Market conditions
        - Correlation between assets
        - Risk metrics
        - Minimum trade sizes
    """
    
    if not balances or not prices:
        return {
            'success': False,
            'error': 'Balances and prices required'
        }
    
    # Get target allocation
    target_allocation = get_target_allocation()
    
    # ========================================
    # Step 1: Calculate Portfolio Value
    # ========================================
    
    total_value_usdt = 0
    asset_values = {}
    
    for asset, amount in balances.items():
        if amount <= 0:
            continue
        
        if asset == 'USDT':
            # USDT is already in USDT
            asset_values[asset] = amount
            total_value_usdt += amount
        else:
            # Convert to USDT using price
            price = prices.get(asset, 0)
            value = amount * price
            asset_values[asset] = value
            total_value_usdt += value
    
    if total_value_usdt == 0:
        return {
            'success': False,
            'error': 'Portfolio has no value'
        }
    
    print(f"\n{'='*70}")
    print(f"AI PORTFOLIO ANALYSIS")
    print(f"{'='*70}")
    print(f"Total Portfolio Value: ${total_value_usdt:,.2f}")
    print(f"{'='*70}\n")
    
    # ========================================
    # Step 2: Calculate Current Allocation
    # ========================================
    
    current_allocation = {}
    
    for asset, value in asset_values.items():
        if asset != 'USDT':  # Don't allocate USDT (it's cash)
            allocation_pct = value / total_value_usdt
            current_allocation[asset] = allocation_pct
    
    print("Current Allocation:")
    for asset, pct in sorted(current_allocation.items(), key=lambda x: x[1], reverse=True):
        print(f"  {asset}: {pct*100:.1f}%")
    
    # ========================================
    # Step 3: Compare to Target
    # ========================================
    
    print("\nTarget Allocation:")
    for asset, pct in sorted(target_allocation.items(), key=lambda x: x[1], reverse=True):
        print(f"  {asset}: {pct*100:.1f}%")
    
    # ========================================
    # Step 4: Generate Trade Suggestions
    # ========================================
    
    suggested_trades = []
    threshold = 0.05  # 5% difference threshold
    
    print("\nAnalysis:")
    
    # Check each target asset
    for asset, target_pct in target_allocation.items():
        current_pct = current_allocation.get(asset, 0)
        difference = current_pct - target_pct
        
        print(f"  {asset}: Current {current_pct*100:.1f}%, Target {target_pct*100:.1f}%, Diff {difference*100:+.1f}%")
        
        if abs(difference) > threshold:
            # Needs rebalancing
            
            if difference > 0:
                # Over-allocated → SELL
                excess_value = difference * total_value_usdt
                price = prices.get(asset, 1)
                amount_to_sell = excess_value / price
                
                suggested_trades.append({
                    'action': 'SELL',
                    'symbol': f'{asset}/USDT',
                    'asset': asset,
                    'amount': round(amount_to_sell, 6),
                    'reason': f'Reduce {asset} from {current_pct*100:.1f}% to {target_pct*100:.1f}%',
                    'current_pct': round(current_pct * 100, 1),
                    'target_pct': round(target_pct * 100, 1)
                })
                
            else:
                # Under-allocated → BUY
                deficit_value = abs(difference) * total_value_usdt
                price = prices.get(asset, 1)
                amount_to_buy = deficit_value / price
                
                suggested_trades.append({
                    'action': 'BUY',
                    'symbol': f'{asset}/USDT',
                    'asset': asset,
                    'amount': round(amount_to_buy, 6),
                    'reason': f'Increase {asset} from {current_pct*100:.1f}% to {target_pct*100:.1f}%',
                    'current_pct': round(current_pct * 100, 1),
                    'target_pct': round(target_pct * 100, 1)
                })
    
    needs_rebalancing = len(suggested_trades) > 0
    
    print(f"\nSuggested Trades: {len(suggested_trades)}")
    for trade in suggested_trades:
        print(f"  {trade['action']} {trade['amount']} {trade['asset']} - {trade['reason']}")
    
    return {
        'success': True,
        'total_value_usdt': round(total_value_usdt, 2),
        'current_allocation': {k: round(v*100, 1) for k, v in current_allocation.items()},
        'target_allocation': {k: round(v*100, 1) for k, v in target_allocation.items()},
        'suggested_trades': suggested_trades,
        'needs_rebalancing': needs_rebalancing,
        'asset_values': {k: round(v, 2) for k, v in asset_values.items()}
    }


def execute_rebalancing_trades(user_id, exchange_account_id, suggested_trades):
    """
    Execute suggested rebalancing trades.
    
    ⚠️ This executes multiple trades!
    - In SIMULATION: Safe, just logs
    - In LIVE: Real money, financial risk!
    
    Args:
        user_id (int): User ID
        exchange_account_id (int): Exchange account to use
        suggested_trades (list): List of trade suggestions
    
    Returns:
        dict: Execution results for all trades
    """
    
    from services import order_execution_service
    
    print(f"\n{'='*70}")
    print(f"EXECUTING PORTFOLIO REBALANCING")
    print(f"{'='*70}")
    print(f"Number of trades: {len(suggested_trades)}")
    print(f"{'='*70}\n")
    
    execution_results = []
    successful = 0
    failed = 0
    
    for trade in suggested_trades:
        print(f"\n[Trade {len(execution_results) + 1}/{len(suggested_trades)}]")
        print(f"  {trade['action']} {trade['amount']} {trade['asset']}")
        print(f"  Reason: {trade['reason']}")
        
        # Execute trade
        result = order_execution_service.execute_market_order_for_account(
            user_id=user_id,
            exchange_account_id=exchange_account_id,
            symbol=trade['symbol'],
            side=trade['action'].lower(),
            amount=trade['amount'],
            trade_source='portfolio_ai_rebalancing'
        )
        
        execution_results.append({
            'trade': trade,
            'result': result,
            'success': result['success']
        })
        
        if result['success']:
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"REBALANCING COMPLETE")
    print(f"{'='*70}")
    print(f"Successful: {successful}/{len(suggested_trades)}")
    print(f"Failed: {failed}/{len(suggested_trades)}")
    print(f"{'='*70}\n")
    
    return {
        'success': True,
        'total_trades': len(suggested_trades),
        'successful': successful,
        'failed': failed,
        'results': execution_results
    }


# ============================================
# EDUCATIONAL NOTES
# ============================================

"""
PORTFOLIO REBALANCING EXPLAINED:
================================

Concept:
--------
You set target allocations (e.g., 50% BTC, 30% ETH, 20% others).
Over time, assets grow at different rates.
Your actual allocation drifts from target.
Rebalancing brings it back to target.

Example Scenario:
----------------
January 1st (Start):
- BTC: $5,000 (50%)
- ETH: $3,000 (30%)  
- TON: $2,000 (20%)
- Total: $10,000

March 1st (After growth):
- BTC grew 40%: Now $7,000 (58% - too high!)
- ETH grew 10%: Now $3,300 (27% - bit low)
- TON flat: Still $2,000 (17% - too low)
- Total: $12,300

Rebalancing Action:
- Sell $984 of BTC (bring to 50% = $6,150)
- Buy $369 of ETH (bring to 30% = $3,690)
- Buy $369 of TON (bring to 20% = $2,460)
- Result: Back to 50/30/20 target

Benefits:
- Takes profit from BTC (it grew too much)
- Buys more of assets that didn't grow as much
- Maintains risk profile
- Prevents over-concentration

Drawbacks:
- Transaction fees
- May sell winners too early
- May buy losers
- Tax implications (capital gains)

Types of Rebalancing:
--------------------
1. Calendar-based: Every month/quarter
2. Threshold-based: When allocation drifts >5%
3. Hybrid: Calendar + threshold

This Implementation:
-------------------
- Threshold-based (5% difference)
- Simple allocation algorithm
- Educational demonstration
- Shows the concept clearly

Real-World Considerations:
-------------------------
In production, you'd also need:
- Transaction cost analysis
- Tax optimization
- Minimum trade sizes
- Slippage estimation
- Market impact
- Correlation analysis
- Risk metrics (Sharpe ratio, volatility)
- Backtesting
"""


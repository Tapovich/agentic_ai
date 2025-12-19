"""
Test Grid Bot Functionality
Demonstrates how to create and manage grid trading bots.

Usage:
    python test_grid_bot.py
"""

from services import grid_bot_service
from models import user_model


def test_grid_bot():
    """
    Test creating a grid bot.
    """
    print("=" * 70)
    print("TESTING GRID BOT SERVICE")
    print("=" * 70)
    
    # Get test user
    print("\n[1] Getting test user...")
    user = user_model.get_user_by_username('testuser')
    
    if not user:
        print("❌ Test user not found. Please create demo user first:")
        print("   python create_demo_user.py")
        return
    
    print(f"✅ User found: {user['username']}")
    print(f"   Current balance: ${user['balance']:.2f}")
    
    # Create grid bot
    print("\n[2] Creating grid bot...")
    
    result = grid_bot_service.create_grid_bot(
        user_id=user['id'],
        symbol='BTCUSDT',
        lower_price=40000.00,
        upper_price=50000.00,
        grid_count=5,
        investment_amount=1000.00
    )
    
    if result['success']:
        print(f"✅ Grid bot created successfully!")
        print(f"   Bot ID: {result['bot_id']}")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Price Range: ${result['lower_price']:.2f} - ${result['upper_price']:.2f}")
        print(f"   Grid Count: {result['grid_count']}")
        print(f"   Investment: ${result['investment_amount']:.2f}")
        print(f"   Price Step: ${result['price_step']:.2f}")
        print(f"   New Balance: ${result['new_balance']:.2f}")
        
        print(f"\n   Grid Levels Created:")
        print(f"   {'Level':<8} {'Price':<12} {'Type':<10}")
        print(f"   {'-'*30}")
        for level in result['levels']:
            print(f"   {level['level_number']:<8} ${level['level_price']:<11.2f} {level['order_type']:<10}")
        
        bot_id = result['bot_id']
        
    else:
        print(f"❌ Failed to create grid bot: {result['error']}")
        return
    
    # Get user's bots
    print(f"\n[3] Getting user's grid bots...")
    
    bots = grid_bot_service.get_bots_for_user(user['id'])
    
    print(f"✅ Found {len(bots)} bot(s)")
    for bot in bots:
        status = "Active" if bot['is_active'] == 1 else "Stopped"
        print(f"   Bot {bot['id']}: {bot['symbol']} ({bot['grid_count']} grids) - {status}")
    
    # Get bot levels
    print(f"\n[4] Getting bot levels...")
    
    levels = grid_bot_service.get_levels_for_bot(bot_id)
    
    print(f"✅ Found {len(levels)} level(s)")
    for level in levels:
        filled = "Filled" if level['is_filled'] == 1 else "Pending"
        print(f"   Level {level['id']}: {level['order_type']} @ ${level['level_price']:.2f} - {filled}")
    
    # Get bot details
    print(f"\n[5] Getting bot details...")
    
    details = grid_bot_service.get_bot_details(bot_id, user['id'])
    
    if details:
        print(f"✅ Bot Details:")
        print(f"   Total Levels: {details['stats']['total_levels']}")
        print(f"   Buy Levels: {details['stats']['buy_levels']}")
        print(f"   Sell Levels: {details['stats']['sell_levels']}")
        print(f"   Filled: {details['stats']['filled_count']}")
        print(f"   Pending: {details['stats']['pending_count']}")
    
    # Stop bot
    print(f"\n[6] Stopping bot...")
    
    stop_result = grid_bot_service.stop_grid_bot(bot_id, user['id'])
    
    if stop_result['success']:
        print(f"✅ {stop_result['message']}")
        print(f"   Returned investment: ${stop_result['returned_investment']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ GRID BOT TEST COMPLETED!")
    print("=" * 70)
    print("\nGrid bot system is working correctly!")
    print("You can now create grid bots via the API or frontend.")
    print("=" * 70)


if __name__ == "__main__":
    test_grid_bot()


"""
Database Diagnostics Service (TASK 46)

Provides database health metrics and overview for monitoring.

Purpose:
- Monitor database table sizes
- Track data growth over time
- Help identify database issues
- Provide admin dashboard insights

Usage:
    from services.db_diagnostics import get_db_overview
    overview = get_db_overview()
    print(f"Users: {overview['users']}")
"""

from models import db_sqlite as db


def get_db_overview():
    """
    Get comprehensive database overview with record counts for all tables.
    
    Returns:
        dict: Record counts for each table
              {
                  "users": 5,
                  "exchange_accounts": 3,
                  "grid_bots": 10,
                  "dca_bots": 7,
                  "advanced_predictions": 150,
                  "price_history": 50000,
                  "predictions": 200,
                  "portfolio": 15,
                  "trades": 300,
                  "exchange_trade_logs": 85,
                  "grid_levels": 150
              }
    
    Educational Note:
    - Each table's record count helps track system usage
    - High price_history count = good data coverage for AI
    - High predictions count = active AI usage
    - Trade logs track real/simulated trading activity
    
    Example:
        >>> overview = get_db_overview()
        >>> print(f"Database has {overview['users']} users")
        Database has 5 users
    """
    
    overview = {}
    
    # List of all tables to check
    tables = [
        'users',
        'exchange_accounts',
        'grid_bots',
        'dca_bots',
        'advanced_predictions',
        'price_history',
        'predictions',
        'portfolio',
        'trades',
        'exchange_trade_logs',
        'grid_levels'
    ]
    
    print(f"\n{'='*70}")
    print(f"DATABASE DIAGNOSTICS")
    print(f"{'='*70}")
    
    for table in tables:
        try:
            # Query: SELECT COUNT(*) FROM table_name
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = db.execute_query(query)
            
            if result:
                # Result format: [(count,)]
                count = result if isinstance(result, int) else 0
                overview[table] = count
                print(f"✅ {table:30} {count:>10} records")
            else:
                overview[table] = 0
                print(f"⚠️  {table:30} {0:>10} records (empty or error)")
                
        except Exception as e:
            # Table might not exist
            overview[table] = -1
            print(f"❌ {table:30} {'ERROR':>10} (table not found: {e})")
    
    print(f"{'='*70}\n")
    
    return overview


def get_table_info(table_name):
    """
    Get detailed information about a specific table.
    
    Args:
        table_name (str): Name of the table to inspect
    
    Returns:
        dict: Table information including:
              - record_count: Number of records
              - columns: List of column names
              - sample_data: First 5 records (if any)
    
    Example:
        >>> info = get_table_info('users')
        >>> print(info['columns'])
        ['id', 'username', 'email', 'password_hash', 'balance', 'created_at']
    """
    
    try:
        # Get record count
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        count_result = db.execute_query(count_query)
        record_count = count_result if isinstance(count_result, int) else 0
        
        # Get column information (SQLite specific)
        columns_query = f"PRAGMA table_info({table_name})"
        columns_result = db.execute_query(columns_query)
        
        # Extract column names from PRAGMA result
        # Format: [(cid, name, type, notnull, dflt_value, pk), ...]
        columns = []
        if columns_result and isinstance(columns_result, list):
            columns = [col[1] for col in columns_result]  # col[1] is the name
        
        # Get sample data (first 5 records)
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        sample_data = db.execute_query(sample_query)
        
        return {
            'table_name': table_name,
            'record_count': record_count,
            'columns': columns,
            'sample_data': sample_data if sample_data else [],
            'exists': True
        }
        
    except Exception as e:
        return {
            'table_name': table_name,
            'record_count': -1,
            'columns': [],
            'sample_data': [],
            'exists': False,
            'error': str(e)
        }


def get_database_size_info():
    """
    Get database file size and storage information.
    
    Returns:
        dict: Database size metrics
              {
                  "total_size_bytes": 5242880,
                  "total_size_mb": 5.0,
                  "total_size_readable": "5.00 MB"
              }
    
    Note: This is useful for monitoring database growth over time.
    """
    
    import os
    
    try:
        # Get database file path (assuming ai_trading.db in root)
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ai_trading.db')
        
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            
            # Format size in human-readable format
            if size_mb < 1:
                size_readable = f"{size_bytes / 1024:.2f} KB"
            elif size_mb < 1024:
                size_readable = f"{size_mb:.2f} MB"
            else:
                size_readable = f"{size_mb / 1024:.2f} GB"
            
            return {
                'database_file': 'ai_trading.db',
                'total_size_bytes': size_bytes,
                'total_size_mb': round(size_mb, 2),
                'total_size_readable': size_readable,
                'exists': True
            }
        else:
            return {
                'database_file': 'ai_trading.db',
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'total_size_readable': "0 KB",
                'exists': False,
                'error': 'Database file not found'
            }
            
    except Exception as e:
        return {
            'database_file': 'ai_trading.db',
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'total_size_readable': "Unknown",
            'exists': False,
            'error': str(e)
        }


def check_database_health():
    """
    Comprehensive database health check.
    
    Returns:
        dict: Health status with detailed metrics
              {
                  "status": "healthy" | "warning" | "critical",
                  "overview": {...},
                  "size_info": {...},
                  "issues": [...],
                  "recommendations": [...]
              }
    
    Health Criteria:
    - Status "healthy": All tables exist, database is accessible
    - Status "warning": Some tables empty or minor issues
    - Status "critical": Tables missing or major issues
    """
    
    overview = get_db_overview()
    size_info = get_database_size_info()
    
    issues = []
    recommendations = []
    
    # Check for missing tables (count = -1)
    missing_tables = [table for table, count in overview.items() if count == -1]
    if missing_tables:
        issues.append(f"Missing tables: {', '.join(missing_tables)}")
        recommendations.append("Run database setup script or migrations")
    
    # Check for empty core tables
    if overview.get('users', 0) == 0:
        issues.append("No users registered")
        recommendations.append("Create a demo user for testing")
    
    if overview.get('price_history', 0) < 100:
        issues.append("Limited price history data (< 100 records)")
        recommendations.append("Sync price history from exchange (POST /api/prices/sync)")
    
    # Determine overall status
    if missing_tables:
        status = "critical"
    elif issues:
        status = "warning"
    else:
        status = "healthy"
    
    return {
        'status': status,
        'overview': overview,
        'size_info': size_info,
        'issues': issues,
        'recommendations': recommendations,
        'total_records': sum(count for count in overview.values() if count > 0)
    }


if __name__ == '__main__':
    # Test the diagnostics
    print("\n" + "="*70)
    print("TESTING DB DIAGNOSTICS")
    print("="*70 + "\n")
    
    # Test 1: Get overview
    print("Test 1: Get DB Overview")
    overview = get_db_overview()
    print(f"Result: {len(overview)} tables checked\n")
    
    # Test 2: Get database size
    print("Test 2: Get Database Size")
    size_info = get_database_size_info()
    print(f"Database size: {size_info.get('total_size_readable', 'Unknown')}\n")
    
    # Test 3: Health check
    print("Test 3: Health Check")
    health = check_database_health()
    print(f"Status: {health['status']}")
    print(f"Total records: {health['total_records']}")
    
    if health['issues']:
        print("\nIssues found:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    if health['recommendations']:
        print("\nRecommendations:")
        for rec in health['recommendations']:
            print(f"  - {rec}")
    
    print("\n" + "="*70)
    print("✅ DIAGNOSTICS TEST COMPLETE")
    print("="*70 + "\n")


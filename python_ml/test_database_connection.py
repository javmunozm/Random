#!/usr/bin/env python3
"""
Database Connection Test Script

Attempts to connect to the LuckyDb SQL Server database and check for new data.

Requirements:
- pyodbc or pymssql (not available in current environment)
- SQL Server connection (Windows SQL Server Express with Integrated Security)

This script is for documentation purposes and will likely fail in the current
Linux environment without proper SQL Server drivers and Windows authentication.
"""

import sys

# Connection details from DatabaseConnection.cs
SERVER = "DESKTOP-QR14EDK\\SQLEXPRESS01"
DATABASE = "LuckyDb"
CONNECTION_STRING_TEMPLATE = (
    "Server={server};Database={database};Integrated Security=true;"
    "TrustServerCertificate=true;"
)

def check_pyodbc():
    """Check if pyodbc is available"""
    try:
        import pyodbc
        return True, pyodbc
    except ImportError:
        return False, None

def check_pymssql():
    """Check if pymssql is available"""
    try:
        import pymssql
        return True, pymssql
    except ImportError:
        return False, None

def connect_with_pyodbc():
    """Attempt connection using pyodbc"""
    available, pyodbc = check_pyodbc()
    if not available:
        print("❌ pyodbc not available")
        return None

    try:
        # This requires ODBC Driver for SQL Server
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
        print(f"Attempting connection with pyodbc...")
        print(f"Connection string: {conn_str}")

        conn = pyodbc.connect(conn_str, timeout=5)
        print("✅ Connected successfully with pyodbc!")
        return conn
    except Exception as e:
        print(f"❌ pyodbc connection failed: {e}")
        return None

def connect_with_pymssql():
    """Attempt connection using pymssql"""
    available, pymssql = check_pymssql()
    if not available:
        print("❌ pymssql not available")
        return None

    try:
        print(f"Attempting connection with pymssql...")
        # pymssql doesn't support Windows Integrated Security from Linux
        # Would need SQL Server authentication
        print("⚠️  pymssql doesn't support Windows Integrated Security from Linux")
        return None
    except Exception as e:
        print(f"❌ pymssql connection failed: {e}")
        return None

def query_latest_series(conn):
    """Query the latest series from the database"""
    try:
        cursor = conn.cursor()

        # Get latest series ID
        query = "SELECT MAX(Id) as MaxId FROM dbo.event"
        cursor.execute(query)
        row = cursor.fetchone()

        if row:
            latest_series = row[0]
            print(f"📊 Latest series in database: {latest_series}")
            return latest_series
        else:
            print("⚠️  No data found in database")
            return None

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return None
    finally:
        cursor.close()

def get_series_data(conn, series_id):
    """Get all event data for a specific series"""
    try:
        cursor = conn.cursor()

        query = """
            SELECT el.Element1, el.Element2, el.Element3, el.Element4, el.Element5, el.Element6, el.Element7,
                   el.Element8, el.Element9, el.Element10, el.Element11, el.Element12, el.Element13, el.Element14
            FROM dbo.event e
            INNER JOIN dbo.elements el ON e.Id = el.IdEvents
            WHERE e.Id = ?
            ORDER BY el.Id
        """

        cursor.execute(query, series_id)
        rows = cursor.fetchall()

        events = []
        for row in rows:
            event = [row[i] for i in range(14)]
            events.append(event)

        print(f"📊 Series {series_id} has {len(events)} events")
        return events

    except Exception as e:
        print(f"❌ Query failed: {e}")
        return None
    finally:
        cursor.close()

def main():
    print("=" * 80)
    print("DATABASE CONNECTION TEST")
    print("=" * 80)
    print()
    print(f"Target Server: {SERVER}")
    print(f"Target Database: {DATABASE}")
    print()

    # Check available drivers
    print("Checking available SQL Server drivers...")
    print()

    pyodbc_available, _ = check_pyodbc()
    pymssql_available, _ = check_pymssql()

    print(f"pyodbc: {'✅ Available' if pyodbc_available else '❌ Not available'}")
    print(f"pymssql: {'✅ Available' if pymssql_available else '❌ Not available'}")
    print()

    if not pyodbc_available and not pymssql_available:
        print("=" * 80)
        print("NO SQL SERVER DRIVERS AVAILABLE")
        print("=" * 80)
        print()
        print("To connect to SQL Server from Python, you need to install:")
        print("1. For pyodbc:")
        print("   - pip install pyodbc")
        print("   - ODBC Driver 17 for SQL Server")
        print("   - Note: Integrated Security requires Windows environment")
        print()
        print("2. For pymssql:")
        print("   - pip install pymssql")
        print("   - Note: Doesn't support Windows Integrated Security from Linux")
        print()
        print("=" * 80)
        print("ALTERNATIVE: Use existing database export")
        print("=" * 80)
        print()
        print("Latest export: /home/user/Random/Results/database_export_2898_3143_20251105_135513.json")
        print("Contains: Series 2898-3143 (246 series)")
        print()
        print("Manual additions:")
        print("- Series 3144 added manually to Python code")
        print("- Series 3145 prediction generated")
        print()
        return 1

    # Try connection
    print("=" * 80)
    print("ATTEMPTING CONNECTION")
    print("=" * 80)
    print()

    conn = None
    if pyodbc_available:
        conn = connect_with_pyodbc()

    if not conn and pymssql_available:
        conn = connect_with_pymssql()

    if not conn:
        print()
        print("=" * 80)
        print("CONNECTION FAILED")
        print("=" * 80)
        print()
        print("Possible reasons:")
        print("1. Running in Linux environment (SQL Server is on Windows)")
        print("2. Integrated Security requires Windows authentication")
        print("3. SQL Server not accessible from this machine")
        print("4. Network/firewall restrictions")
        print()
        return 1

    # Query database
    print()
    print("=" * 80)
    print("QUERYING DATABASE")
    print("=" * 80)
    print()

    latest = query_latest_series(conn)

    if latest:
        print()
        print(f"Latest series in DB: {latest}")
        print(f"Latest in export: 3143")
        print(f"Latest in code: 3144 (manual)")
        print(f"Prediction generated: 3145")
        print()

        if latest > 3144:
            print(f"⚠️  NEW DATA AVAILABLE: Series {latest}")
            print(f"   Need to update Python code with Series {latest} results")

            # Fetch new data
            for series_id in range(3145, latest + 1):
                events = get_series_data(conn, series_id)
                if events:
                    print()
                    print(f"Series {series_id} data:")
                    for i, event in enumerate(events, 1):
                        print(f"  Event {i}: {event}")

    conn.close()
    print()
    print("✅ Connection closed")
    return 0

if __name__ == "__main__":
    sys.exit(main())

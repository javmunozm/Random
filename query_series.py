import pyodbc

# Connection string
conn_str = r'DRIVER={SQL Server};SERVER=DESKTOP-QR14EDK\SQLEXPRESS01;DATABASE=LuckyDb;Trusted_Connection=yes;'

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("=== Querying Series Data from Database ===")
    print()
    
    # Query series 3124-3130
    for series_id in range(3124, 3131):
        print("--- Series", series_id, "---")
        
        query = """
            SELECT el.Element1, el.Element2, el.Element3, el.Element4, el.Element5, el.Element6, el.Element7,
                   el.Element8, el.Element9, el.Element10, el.Element11, el.Element12, el.Element13, el.Element14
            FROM dbo.elements el
            INNER JOIN dbo.event e ON e.Id = el.IdEvents
            WHERE e.Id = ?
            ORDER BY el.Id
        """
        
        cursor.execute(query, series_id)
        results = cursor.fetchall()
        
        if not results:
            print("Series", series_id, "does not exist or has no data")
            print()
            continue
        
        print("Found", len(results), "events:")
        for i, row in enumerate(results, 1):
            numbers = ["%02d" % n for n in row if n is not None]
            print("   Event", str(i) + ":", ' '.join(numbers))
        print()
    
    # Check latest series
    cursor.execute("SELECT MAX(Id) FROM dbo.event")
    latest = cursor.fetchone()[0]
    print("Latest series in database:", latest)
    
    conn.close()
except Exception as e:
    print("Error:", e)

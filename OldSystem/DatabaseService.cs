using Microsoft.Data.SqlClient;
using System.Data;

public class DatabaseService
{
    private readonly string _connectionString;

    public DatabaseService()
    {
        var server = "DESKTOP-QR14EDK\\SQLEXPRESS01";
        var database = "LuckyDb";
        
        _connectionString = $"Data Source={server};Initial Catalog={database};Integrated Security=True;TrustServerCertificate=True;";
    }

    public List<NumericData> LoadLotteryData()
    {
        var lotteryData = new List<NumericData>();
        var processedEventIds = new HashSet<int>();

        using var connection = new SqlConnection(_connectionString);
        connection.Open();

        // Get all events first, then get the first element combination for each
        var query = @"
            SELECT DISTINCT e.Id
            FROM dbo.event e
            ORDER BY e.Id";

        using var command = new SqlCommand(query, connection);
        using var reader = command.ExecuteReader();
        
        var eventIds = new List<int>();
        while (reader.Read())
        {
            eventIds.Add(Convert.ToInt32(reader["Id"]));
        }
        reader.Close();

        // For each event, get only the first element combination
        foreach (var eventId in eventIds)
        {
            var elementQuery = @"
                SELECT TOP 1
                    el.Element1, el.Element2, el.Element3, el.Element4, el.Element5,
                    el.Element6, el.Element7, el.Element8, el.Element9, el.Element10,
                    el.Element11, el.Element12, el.Element13, el.Element14
                FROM dbo.elements el
                WHERE el.IdEvents = @EventId
                ORDER BY el.Element1"; // Use some consistent ordering

            using var elementCommand = new SqlCommand(elementQuery, connection);
            elementCommand.Parameters.AddWithValue("@EventId", eventId);
            using var elementReader = elementCommand.ExecuteReader();

            if (elementReader.Read())
            {
                var data = new NumericData
                {
                    SeriesId = eventId,
                    Numbers = new List<int>()
                };

                for (int i = 1; i <= 14; i++)
                {
                    var columnName = $"Element{i}";
                    if (!elementReader.IsDBNull(columnName))
                    {
                        var value = Convert.ToInt32(elementReader[columnName]);
                        if (value > 0) // Only add valid numbers
                        {
                            data.Numbers.Add(value);
                        }
                    }
                }

                if (data.Numbers.Count > 0)
                {
                    lotteryData.Add(data);
                }
            }
        }

        Console.WriteLine($"Loaded {lotteryData.Count} unique series from database (avoiding duplicates)");
        if (lotteryData.Count > 0)
        {
            var minSeries = lotteryData.Min(x => x.SeriesId);
            var maxSeries = lotteryData.Max(x => x.SeriesId);
            Console.WriteLine($"Series range: {minSeries} to {maxSeries} (expected: 2898 to 3107)");
            Console.WriteLine($"Expected count: {3107 - 2898 + 1}, Actual count: {lotteryData.Count}");
        }
        return lotteryData;
    }

    public NumericData? GetLatestSeries()
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();

        // First get the latest event ID
        var latestEventQuery = "SELECT MAX(Id) FROM dbo.event";
        using var latestEventCommand = new SqlCommand(latestEventQuery, connection);
        var latestEventId = latestEventCommand.ExecuteScalar();
        
        if (latestEventId == null || latestEventId == DBNull.Value)
            return null;

        var eventId = Convert.ToInt32(latestEventId);

        // Then get the first element combination for that event
        var query = @"
            SELECT TOP 1
                el.Element1, el.Element2, el.Element3, el.Element4, el.Element5,
                el.Element6, el.Element7, el.Element8, el.Element9, el.Element10,
                el.Element11, el.Element12, el.Element13, el.Element14
            FROM dbo.elements el
            WHERE el.IdEvents = @EventId
            ORDER BY el.Element1";

        using var command = new SqlCommand(query, connection);
        command.Parameters.AddWithValue("@EventId", eventId);
        using var reader = command.ExecuteReader();

        if (reader.Read())
        {
            var data = new NumericData
            {
                SeriesId = eventId,
                Numbers = new List<int>()
            };

            for (int i = 1; i <= 14; i++)
            {
                var columnName = $"Element{i}";
                if (!reader.IsDBNull(columnName))
                {
                    var value = Convert.ToInt32(reader[columnName]);
                    if (value > 0)
                    {
                        data.Numbers.Add(value);
                    }
                }
            }

            return data;
        }

        return null;
    }

    public List<NumericData> GetRecentSeries(int count)
    {
        var lotteryData = new List<NumericData>();

        using var connection = new SqlConnection(_connectionString);
        connection.Open();

        var query = $@"
            SELECT TOP {count}
                e.Id,
                el.Element1, el.Element2, el.Element3, el.Element4, el.Element5,
                el.Element6, el.Element7, el.Element8, el.Element9, el.Element10,
                el.Element11, el.Element12, el.Element13, el.Element14
            FROM dbo.event e
            INNER JOIN dbo.elements el ON e.Id = el.IdEvents
            ORDER BY e.Id DESC";

        using var command = new SqlCommand(query, connection);
        using var reader = command.ExecuteReader();

        while (reader.Read())
        {
            var data = new NumericData
            {
                SeriesId = Convert.ToInt32(reader["Id"]),
                Numbers = new List<int>()
            };

            for (int i = 1; i <= 14; i++)
            {
                var columnName = $"Element{i}";
                if (!reader.IsDBNull(columnName))
                {
                    var value = Convert.ToInt32(reader[columnName]);
                    if (value > 0)
                    {
                        data.Numbers.Add(value);
                    }
                }
            }

            lotteryData.Add(data);
        }

        return lotteryData.OrderBy(x => x.SeriesId).ToList();
    }

    public void PrintDatabaseStatistics()
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();

        var query = "SELECT MAX(Id) as MaxId, MIN(Id) as MinId, COUNT(*) as TotalCount FROM dbo.event";
        using var command = new SqlCommand(query, connection);
        using var reader = command.ExecuteReader();

        if (reader.Read())
        {
            var maxId = reader["MaxId"];
            var minId = reader["MinId"];
            var count = reader["TotalCount"];
            
            Console.WriteLine($"=== Database Statistics ===");
            if (maxId == DBNull.Value || count.Equals(0))
            {
                Console.WriteLine("Database is empty - no series found");
            }
            else
            {
                Console.WriteLine($"Latest Series in DB: {maxId}");
                Console.WriteLine($"Earliest Series in DB: {minId}");
                Console.WriteLine($"Total Series Count: {count}");
                Console.WriteLine($"Next Series to Predict: {Convert.ToInt32(maxId) + 1}");
            }
            Console.WriteLine();
        }
    }

    // CRUD Operations
    public bool InsertLotteryData(NumericData data)
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            // Check if event already exists
            var checkEventQuery = "SELECT COUNT(*) FROM dbo.event WHERE Id = @Id";
            using var checkEventCommand = new SqlCommand(checkEventQuery, connection, transaction);
            checkEventCommand.Parameters.AddWithValue("@Id", data.SeriesId);
            var eventExists = (int)checkEventCommand.ExecuteScalar() > 0;

            if (!eventExists)
            {
                // Insert into event table
                var insertEventQuery = "INSERT INTO dbo.event (Id) VALUES (@Id)";
                using var insertEventCommand = new SqlCommand(insertEventQuery, connection, transaction);
                insertEventCommand.Parameters.AddWithValue("@Id", data.SeriesId);
                insertEventCommand.ExecuteNonQuery();
            }

            // Check if elements already exist
            var checkElementsQuery = "SELECT COUNT(*) FROM dbo.elements WHERE IdEvents = @IdEvents";
            using var checkElementsCommand = new SqlCommand(checkElementsQuery, connection, transaction);
            checkElementsCommand.Parameters.AddWithValue("@IdEvents", data.SeriesId);
            var elementsExist = (int)checkElementsCommand.ExecuteScalar() > 0;

            if (elementsExist)
            {
                transaction.Rollback();
                Console.WriteLine($"Series {data.SeriesId} already exists in database.");
                return false;
            }

            // Prepare elements array (pad with nulls if needed)
            var elements = new object[14];
            for (int i = 0; i < 14; i++)
            {
                elements[i] = i < data.Numbers.Count ? (object)data.Numbers[i] : DBNull.Value;
            }

            // Insert into elements table
            var insertElementsQuery = @"
                INSERT INTO dbo.elements (IdEvents, Element1, Element2, Element3, Element4, Element5, Element6, Element7, Element8, Element9, Element10, Element11, Element12, Element13, Element14)
                VALUES (@IdEvents, @E1, @E2, @E3, @E4, @E5, @E6, @E7, @E8, @E9, @E10, @E11, @E12, @E13, @E14)";
            
            using var insertElementsCommand = new SqlCommand(insertElementsQuery, connection, transaction);
            insertElementsCommand.Parameters.AddWithValue("@IdEvents", data.SeriesId);
            for (int i = 0; i < 14; i++)
            {
                insertElementsCommand.Parameters.AddWithValue($"@E{i + 1}", elements[i]);
            }
            insertElementsCommand.ExecuteNonQuery();

            transaction.Commit();
            return true;
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            Console.WriteLine($"Error inserting series {data.SeriesId}: {ex.Message}");
            return false;
        }
    }

    public bool UpdateLotteryData(NumericData data)
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            // Check if event exists
            var checkEventQuery = "SELECT COUNT(*) FROM dbo.event WHERE Id = @Id";
            using var checkEventCommand = new SqlCommand(checkEventQuery, connection, transaction);
            checkEventCommand.Parameters.AddWithValue("@Id", data.SeriesId);
            var eventExists = (int)checkEventCommand.ExecuteScalar() > 0;

            if (!eventExists)
            {
                transaction.Rollback();
                Console.WriteLine($"Series {data.SeriesId} does not exist in database.");
                return false;
            }

            // Prepare elements array (pad with nulls if needed)
            var elements = new object[14];
            for (int i = 0; i < 14; i++)
            {
                elements[i] = i < data.Numbers.Count ? (object)data.Numbers[i] : DBNull.Value;
            }

            // Update elements table
            var updateElementsQuery = @"
                UPDATE dbo.elements 
                SET Element1=@E1, Element2=@E2, Element3=@E3, Element4=@E4, Element5=@E5, Element6=@E6, Element7=@E7, 
                    Element8=@E8, Element9=@E9, Element10=@E10, Element11=@E11, Element12=@E12, Element13=@E13, Element14=@E14
                WHERE IdEvents = @IdEvents";
            
            using var updateElementsCommand = new SqlCommand(updateElementsQuery, connection, transaction);
            updateElementsCommand.Parameters.AddWithValue("@IdEvents", data.SeriesId);
            for (int i = 0; i < 14; i++)
            {
                updateElementsCommand.Parameters.AddWithValue($"@E{i + 1}", elements[i]);
            }
            
            var rowsAffected = updateElementsCommand.ExecuteNonQuery();
            if (rowsAffected == 0)
            {
                transaction.Rollback();
                Console.WriteLine($"No elements found for series {data.SeriesId}.");
                return false;
            }

            transaction.Commit();
            return true;
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            Console.WriteLine($"Error updating series {data.SeriesId}: {ex.Message}");
            return false;
        }
    }

    public bool DeleteLotteryData(int seriesId)
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            // Delete from elements table first (foreign key constraint)
            var deleteElementsQuery = "DELETE FROM dbo.elements WHERE IdEvents = @IdEvents";
            using var deleteElementsCommand = new SqlCommand(deleteElementsQuery, connection, transaction);
            deleteElementsCommand.Parameters.AddWithValue("@IdEvents", seriesId);
            var elementsDeleted = deleteElementsCommand.ExecuteNonQuery();

            // Delete from event table
            var deleteEventQuery = "DELETE FROM dbo.event WHERE Id = @Id";
            using var deleteEventCommand = new SqlCommand(deleteEventQuery, connection, transaction);
            deleteEventCommand.Parameters.AddWithValue("@Id", seriesId);
            var eventDeleted = deleteEventCommand.ExecuteNonQuery();

            if (eventDeleted == 0)
            {
                transaction.Rollback();
                Console.WriteLine($"Series {seriesId} does not exist in database.");
                return false;
            }

            transaction.Commit();
            Console.WriteLine($"Successfully deleted series {seriesId} (removed {elementsDeleted} element records).");
            return true;
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            Console.WriteLine($"Error deleting series {seriesId}: {ex.Message}");
            return false;
        }
    }

    public bool Insert3109Results()
    {
        var results = new List<List<int>>
        {
            new() {1, 3, 4, 5, 7, 9, 10, 12, 13, 14, 15, 22, 23, 24},
            new() {1, 3, 4, 5, 6, 7, 10, 11, 13, 14, 15, 16, 18, 25},
            new() {2, 3, 4, 5, 10, 12, 14, 16, 17, 18, 20, 21, 24, 25},
            new() {5, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 24},
            new() {1, 2, 5, 7, 11, 13, 15, 17, 18, 19, 21, 22, 23, 24},
            new() {1, 2, 3, 4, 8, 10, 11, 13, 14, 16, 17, 19, 20, 21},
            new() {1, 5, 6, 8, 10, 11, 12, 13, 14, 17, 19, 20, 21, 22}
        };

        using var connection = new SqlConnection(_connectionString);
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            // Insert event if doesn't exist
            var checkEventQuery = "SELECT COUNT(*) FROM dbo.event WHERE Id = 3109";
            using var checkEventCommand = new SqlCommand(checkEventQuery, connection, transaction);
            var eventExists = (int)checkEventCommand.ExecuteScalar() > 0;

            if (!eventExists)
            {
                var insertEventQuery = "INSERT INTO dbo.event (Id) VALUES (3109)";
                using var insertEventCommand = new SqlCommand(insertEventQuery, connection, transaction);
                insertEventCommand.ExecuteNonQuery();
            }

            // Clear existing elements for 3109
            var clearElementsQuery = "DELETE FROM dbo.elements WHERE IdEvents = 3109";
            using var clearElementsCommand = new SqlCommand(clearElementsQuery, connection, transaction);
            clearElementsCommand.ExecuteNonQuery();

            // Insert all 7 combinations for 3109
            foreach (var result in results)
            {
                var insertElementsQuery = @"
                    INSERT INTO dbo.elements 
                    (IdEvents, Element1, Element2, Element3, Element4, Element5, Element6, Element7, 
                     Element8, Element9, Element10, Element11, Element12, Element13, Element14)
                    VALUES (@IdEvents, @E1, @E2, @E3, @E4, @E5, @E6, @E7, @E8, @E9, @E10, @E11, @E12, @E13, @E14)";
                
                using var insertElementsCommand = new SqlCommand(insertElementsQuery, connection, transaction);
                insertElementsCommand.Parameters.AddWithValue("@IdEvents", 3109);
                
                for (int i = 0; i < 14; i++)
                {
                    insertElementsCommand.Parameters.AddWithValue($"@E{i + 1}", 
                        i < result.Count ? (object)result[i] : DBNull.Value);
                }
                
                insertElementsCommand.ExecuteNonQuery();
            }

            transaction.Commit();
            Console.WriteLine("Successfully inserted all 7 actual results for series 3109.");
            return true;
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            Console.WriteLine($"Error inserting 3109 results: {ex.Message}");
            return false;
        }
    }

    public bool SeriesExists(int seriesId)
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();

        var query = "SELECT COUNT(*) FROM dbo.event WHERE Id = @Id";
        using var command = new SqlCommand(query, connection);
        command.Parameters.AddWithValue("@Id", seriesId);
        
        return (int)command.ExecuteScalar() > 0;
    }

    public int InsertBatchLotteryData(List<NumericData> dataList)
    {
        int successCount = 0;
        Console.WriteLine($"Starting batch insertion of {dataList.Count} series...");

        foreach (var data in dataList)
        {
            if (InsertLotteryData(data))
            {
                successCount++;
                Console.WriteLine($"✓ Inserted series {data.SeriesId} with {data.Numbers.Count} numbers");
            }
            else
            {
                Console.WriteLine($"✗ Failed to insert series {data.SeriesId}");
            }
        }

        Console.WriteLine($"Batch insertion completed: {successCount}/{dataList.Count} series inserted successfully.");
        return successCount;
    }

    public int InsertMultipleElementsForSameEvent(int eventId, List<List<int>> elementCombinations)
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            // Insert or verify event exists
            var checkEventQuery = "SELECT COUNT(*) FROM dbo.event WHERE Id = @Id";
            using var checkEventCommand = new SqlCommand(checkEventQuery, connection, transaction);
            checkEventCommand.Parameters.AddWithValue("@Id", eventId);
            var eventExists = (int)checkEventCommand.ExecuteScalar() > 0;

            if (!eventExists)
            {
                var insertEventQuery = "INSERT INTO dbo.event (Id) VALUES (@Id)";
                using var insertEventCommand = new SqlCommand(insertEventQuery, connection, transaction);
                insertEventCommand.Parameters.AddWithValue("@Id", eventId);
                insertEventCommand.ExecuteNonQuery();
                Console.WriteLine($"✓ Created event {eventId}");
            }

            // Delete existing elements for this event (if any)
            var deleteElementsQuery = "DELETE FROM dbo.elements WHERE IdEvents = @IdEvents";
            using var deleteElementsCommand = new SqlCommand(deleteElementsQuery, connection, transaction);
            deleteElementsCommand.Parameters.AddWithValue("@IdEvents", eventId);
            var deletedCount = deleteElementsCommand.ExecuteNonQuery();
            if (deletedCount > 0)
            {
                Console.WriteLine($"✓ Removed {deletedCount} existing element records for event {eventId}");
            }

            // Insert all element combinations for this event
            int insertedCount = 0;
            foreach (var combination in elementCombinations)
            {
                // Prepare elements array (pad with nulls if needed)
                var elements = new object[14];
                for (int i = 0; i < 14; i++)
                {
                    elements[i] = i < combination.Count ? (object)combination[i] : DBNull.Value;
                }

                var insertElementsQuery = @"
                    INSERT INTO dbo.elements (IdEvents, Element1, Element2, Element3, Element4, Element5, Element6, Element7, Element8, Element9, Element10, Element11, Element12, Element13, Element14)
                    VALUES (@IdEvents, @E1, @E2, @E3, @E4, @E5, @E6, @E7, @E8, @E9, @E10, @E11, @E12, @E13, @E14)";
                
                using var insertElementsCommand = new SqlCommand(insertElementsQuery, connection, transaction);
                insertElementsCommand.Parameters.AddWithValue("@IdEvents", eventId);
                for (int i = 0; i < 14; i++)
                {
                    insertElementsCommand.Parameters.AddWithValue($"@E{i + 1}", elements[i]);
                }
                insertElementsCommand.ExecuteNonQuery();
                insertedCount++;
                Console.WriteLine($"✓ Inserted combination {insertedCount}: {string.Join(" ", combination.Select(n => n.ToString("D2")))}");
            }

            transaction.Commit();
            Console.WriteLine($"✓ Successfully inserted {insertedCount} element combinations for event {eventId}");
            return insertedCount;
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            Console.WriteLine($"Error inserting multiple elements for event {eventId}: {ex.Message}");
            return 0;
        }
    }

    public bool TruncateTables()
    {
        using var connection = new SqlConnection(_connectionString);
        connection.Open();
        using var transaction = connection.BeginTransaction();

        try
        {
            Console.WriteLine("Truncating database tables...");
            
            // Delete all records from elements table first (foreign key constraint)
            var truncateElementsQuery = "DELETE FROM dbo.elements";
            using var truncateElementsCommand = new SqlCommand(truncateElementsQuery, connection, transaction);
            var elementsDeleted = truncateElementsCommand.ExecuteNonQuery();
            Console.WriteLine($"✓ Deleted {elementsDeleted} records from elements table");

            // Delete all records from event table
            var truncateEventQuery = "DELETE FROM dbo.event";
            using var truncateEventCommand = new SqlCommand(truncateEventQuery, connection, transaction);
            var eventsDeleted = truncateEventCommand.ExecuteNonQuery();
            Console.WriteLine($"✓ Deleted {eventsDeleted} records from event table");

            // Reset identity if exists
            try
            {
                var resetEventIdentityQuery = "DBCC CHECKIDENT ('dbo.event', RESEED, 0)";
                using var resetEventIdentityCommand = new SqlCommand(resetEventIdentityQuery, connection, transaction);
                resetEventIdentityCommand.ExecuteNonQuery();
                Console.WriteLine("✓ Reset event table identity");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Note: Could not reset event identity: {ex.Message}");
            }

            transaction.Commit();
            Console.WriteLine("✅ Successfully truncated both tables");
            return true;
        }
        catch (Exception ex)
        {
            transaction.Rollback();
            Console.WriteLine($"❌ Error truncating tables: {ex.Message}");
            return false;
        }
    }

    public int LoadFromCsv(string csvFilePath)
    {
        if (!File.Exists(csvFilePath))
        {
            Console.WriteLine($"❌ CSV file not found: {csvFilePath}");
            return 0;
        }

        Console.WriteLine($"Loading data from CSV: {csvFilePath}");
        
        // Use FileStream with read sharing to avoid file access issues
        string[] lines;
        try
        {
            using var fileStream = new FileStream(csvFilePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            using var reader = new StreamReader(fileStream);
            var linesList = new List<string>();
            string line;
            while ((line = reader.ReadLine()) != null)
            {
                linesList.Add(line);
            }
            lines = linesList.ToArray();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Error reading CSV file: {ex.Message}");
            return 0;
        }
        
        if (lines.Length <= 1)
        {
            Console.WriteLine("❌ CSV file is empty or has no data rows");
            return 0;
        }

        int successCount = 0;
        int errorCount = 0;

        using var connection = new SqlConnection(_connectionString);
        connection.Open();

        for (int i = 1; i < lines.Length; i++) // Skip header
        {
            try
            {
                var line = lines[i].Trim();
                if (string.IsNullOrEmpty(line)) continue;

                var parts = line.Split(',');
                if (parts.Length < 2)
                {
                    Console.WriteLine($"⚠️ Skipping line {i + 1}: insufficient data");
                    errorCount++;
                    continue;
                }

                // Parse event ID
                if (!int.TryParse(parts[0], out var eventId))
                {
                    Console.WriteLine($"⚠️ Skipping line {i + 1}: invalid event ID '{parts[0]}'");
                    errorCount++;
                    continue;
                }

                // Parse elements (skip first column which is event ID)
                var elements = new List<int>();
                for (int j = 1; j < parts.Length; j++)
                {
                    if (int.TryParse(parts[j], out var element))
                    {
                        elements.Add(element);
                    }
                }

                if (elements.Count == 0)
                {
                    Console.WriteLine($"⚠️ Skipping line {i + 1}: no valid elements");
                    errorCount++;
                    continue;
                }

                // Insert event (ignore if already exists)
                var insertEventQuery = "IF NOT EXISTS (SELECT 1 FROM dbo.event WHERE Id = @Id) INSERT INTO dbo.event (Id) VALUES (@Id)";
                using var insertEventCommand = new SqlCommand(insertEventQuery, connection);
                insertEventCommand.Parameters.AddWithValue("@Id", eventId);
                insertEventCommand.ExecuteNonQuery();

                // Prepare elements array (pad with nulls if needed, truncate if too many)
                var elementArray = new object[14];
                for (int k = 0; k < 14; k++)
                {
                    elementArray[k] = k < elements.Count ? (object)elements[k] : DBNull.Value;
                }

                // Insert elements
                var insertElementsQuery = @"
                    INSERT INTO dbo.elements (IdEvents, Element1, Element2, Element3, Element4, Element5, Element6, Element7, Element8, Element9, Element10, Element11, Element12, Element13, Element14)
                    VALUES (@IdEvents, @E1, @E2, @E3, @E4, @E5, @E6, @E7, @E8, @E9, @E10, @E11, @E12, @E13, @E14)";
                
                using var insertElementsCommand = new SqlCommand(insertElementsQuery, connection);
                insertElementsCommand.Parameters.AddWithValue("@IdEvents", eventId);
                for (int k = 0; k < 14; k++)
                {
                    insertElementsCommand.Parameters.AddWithValue($"@E{k + 1}", elementArray[k]);
                }
                insertElementsCommand.ExecuteNonQuery();

                successCount++;
                if (successCount % 100 == 0 || elements.Count != 14)
                {
                    Console.WriteLine($"✓ Processed event {eventId} with {elements.Count} elements (line {i + 1})");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error processing line {i + 1}: {ex.Message}");
                errorCount++;
            }
        }

        Console.WriteLine($"✅ CSV import completed: {successCount} events inserted, {errorCount} errors");
        return successCount;
    }
}

public class NumericData
{
    public int SeriesId { get; set; }
    public List<int> Numbers { get; set; } = new();
}
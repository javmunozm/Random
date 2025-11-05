using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using Microsoft.Data.SqlClient;
using DataProcessor.Models;

namespace DataProcessor.Connections
{
    public class SpatialDatabaseConnection
    {
        private readonly string connectionString;

        public SpatialDatabaseConnection()
        {
            connectionString = "Server=localhost;Database=SpatialEventDb;Trusted_Connection=true;TrustServerCertificate=true;";
        }

        public List<SpatialEventPattern> LoadHistoricalSpatialDataBefore(int beforeEventId)
        {
            var spatialPatterns = new List<SpatialEventPattern>();

            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                // Load all spatial events before the specified event ID
                string query = @"
                    SELECT e.id, e.event_date, e.event_day, c.x_coordinate, c.y_coordinate 
                    FROM spatial_events e
                    INNER JOIN spatial_coordinates c ON e.id = c.event_id
                    WHERE e.id < @beforeEventId
                    ORDER BY e.id, c.coordinate_order";

                using var command = new SqlCommand(query, connection);
                command.Parameters.AddWithValue("@beforeEventId", beforeEventId);

                using var reader = command.ExecuteReader();
                
                SpatialEventPattern currentPattern = null;
                var currentEventId = -1;

                while (reader.Read())
                {
                    var eventId = reader.GetInt32("id");
                    
                    if (eventId != currentEventId)
                    {
                        // Save previous pattern if exists
                        if (currentPattern != null)
                        {
                            spatialPatterns.Add(currentPattern);
                        }
                        
                        // Start new pattern
                        currentPattern = new SpatialEventPattern
                        {
                            EventId = eventId,
                            EventTime = reader.GetDateTime("event_date"),
                            EventDay = Enum.Parse<DayOfWeek>(reader.GetString("event_day"))
                        };
                        currentEventId = eventId;
                    }
                    
                    // Add coordinate to current pattern
                    var coordinate = new Coordinate(
                        reader.GetDouble("x_coordinate"),
                        reader.GetDouble("y_coordinate")
                    );
                    currentPattern?.Coordinates.Add(coordinate);
                }
                
                // Add the last pattern
                if (currentPattern != null)
                {
                    spatialPatterns.Add(currentPattern);
                }

                Console.WriteLine($"Loaded {spatialPatterns.Count} spatial event patterns before event {beforeEventId}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading spatial data: {ex.Message}");
            }

            return spatialPatterns;
        }

        public List<Coordinate> GetActualCoordinatesForEvent(int eventId)
        {
            var coordinates = new List<Coordinate>();

            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                string query = @"
                    SELECT x_coordinate, y_coordinate 
                    FROM spatial_coordinates 
                    WHERE event_id = @eventId 
                    ORDER BY coordinate_order";

                using var command = new SqlCommand(query, connection);
                command.Parameters.AddWithValue("@eventId", eventId);

                using var reader = command.ExecuteReader();
                
                while (reader.Read())
                {
                    coordinates.Add(new Coordinate(
                        reader.GetDouble("x_coordinate"),
                        reader.GetDouble("y_coordinate")
                    ));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading actual coordinates for event {eventId}: {ex.Message}");
            }

            return coordinates;
        }

        public bool SpatialEventExists(int eventId)
        {
            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                string query = "SELECT COUNT(*) FROM spatial_events WHERE id = @eventId";
                using var command = new SqlCommand(query, connection);
                command.Parameters.AddWithValue("@eventId", eventId);

                var count = (int)command.ExecuteScalar();
                return count > 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error checking if spatial event {eventId} exists: {ex.Message}");
                return false;
            }
        }

        public bool InsertSpatialEventData(int eventId, DayOfWeek eventDay, DateTime eventTime, List<Coordinate> coordinates)
        {
            if (coordinates.Count != 7)
            {
                Console.WriteLine("Error: Each spatial event must have exactly 7 coordinates");
                return false;
            }

            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();
                
                using var transaction = connection.BeginTransaction();
                
                try
                {
                    // Insert the spatial event
                    string insertEventQuery = @"
                        INSERT INTO spatial_events (id, event_date, event_day, event_time) 
                        VALUES (@id, @eventDate, @eventDay, @eventTime)";
                    
                    using var eventCommand = new SqlCommand(insertEventQuery, connection, transaction);
                    eventCommand.Parameters.AddWithValue("@id", eventId);
                    eventCommand.Parameters.AddWithValue("@eventDate", eventTime.Date);
                    eventCommand.Parameters.AddWithValue("@eventDay", eventDay.ToString());
                    eventCommand.Parameters.AddWithValue("@eventTime", eventTime.TimeOfDay);
                    
                    eventCommand.ExecuteNonQuery();
                    
                    // Insert coordinates
                    string insertCoordQuery = @"
                        INSERT INTO spatial_coordinates (event_id, coordinate_order, x_coordinate, y_coordinate) 
                        VALUES (@eventId, @order, @x, @y)";
                    
                    for (int i = 0; i < coordinates.Count; i++)
                    {
                        using var coordCommand = new SqlCommand(insertCoordQuery, connection, transaction);
                        coordCommand.Parameters.AddWithValue("@eventId", eventId);
                        coordCommand.Parameters.AddWithValue("@order", i + 1);
                        coordCommand.Parameters.AddWithValue("@x", coordinates[i].X);
                        coordCommand.Parameters.AddWithValue("@y", coordinates[i].Y);
                        
                        coordCommand.ExecuteNonQuery();
                    }
                    
                    transaction.Commit();
                    Console.WriteLine($"✅ Successfully inserted spatial event {eventId} with {coordinates.Count} coordinates");
                    return true;
                }
                catch (Exception ex)
                {
                    transaction.Rollback();
                    Console.WriteLine($"Error inserting spatial event data: {ex.Message}");
                    return false;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Database connection error: {ex.Message}");
                return false;
            }
        }

        public List<SpatialEventPattern> LoadAllSpatialEvents()
        {
            return LoadHistoricalSpatialDataBefore(int.MaxValue);
        }

        public Dictionary<DayOfWeek, List<SpatialEventPattern>> GetEventsByDay()
        {
            var allEvents = LoadAllSpatialEvents();
            return allEvents.GroupBy(e => e.EventDay)
                           .ToDictionary(g => g.Key, g => g.ToList());
        }

        public (double minX, double maxX, double minY, double maxY) GetCoordinateBounds()
        {
            // Use discrete coordinate system bounds
            return (0, 2, 0, 9);
        }

        public Dictionary<string, int> GetDensityDistribution(double gridSize = 2.0)
        {
            var density = new Dictionary<string, int>();

            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                string query = "SELECT x_coordinate, y_coordinate FROM spatial_coordinates";
                using var command = new SqlCommand(query, connection);
                using var reader = command.ExecuteReader();
                
                while (reader.Read())
                {
                    var x = reader.GetDouble("x_coordinate");
                    var y = reader.GetDouble("y_coordinate");
                    
                    var gridX = Math.Floor(x / gridSize) * gridSize;
                    var gridY = Math.Floor(y / gridSize) * gridSize;
                    var gridKey = $"{gridX:F1},{gridY:F1}";
                    
                    if (density.ContainsKey(gridKey))
                        density[gridKey]++;
                    else
                        density[gridKey] = 1;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error calculating density distribution: {ex.Message}");
            }

            return density;
        }

        public int GetTotalEventsCount()
        {
            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                string query = "SELECT COUNT(*) FROM spatial_events";
                using var command = new SqlCommand(query, connection);
                
                return (int)command.ExecuteScalar();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error getting total events count: {ex.Message}");
                return 0;
            }
        }

        public bool ValidateSpatialEventData(int eventId, List<Coordinate> coordinates)
        {
            // Use discrete coordinate system validation
            var validation = DiscreteCoordinateSystem.ValidateEventCoordinates(coordinates);
            
            if (!validation.isValid)
            {
                foreach (var error in validation.errors)
                {
                    Console.WriteLine($"❌ {error}");
                }
                return false;
            }

            Console.WriteLine("✅ Spatial event data validation passed");
            return true;
        }

        public DayOfWeek CalculateEventDay(int eventId)
        {
            // Event 3121 was Wednesday, calculate the day for any event ID
            var eventDays = new[] { DayOfWeek.Wednesday, DayOfWeek.Friday, DayOfWeek.Sunday };
            var dayIndex = (eventId - 3121) % 3;
            
            // Handle negative indices
            if (dayIndex < 0) dayIndex += 3;
            
            return eventDays[dayIndex];
        }

        public DateTime CalculateEventDateTime(int eventId)
        {
            // Calculate the date based on event schedule (Wed/Fri/Sun at 22:30 Chilean time)
            var baseDate = new DateTime(2024, 1, 1); // Adjust base date as needed
            var eventDay = CalculateEventDay(eventId);
            var eventTime = new TimeSpan(22, 30, 0);
            
            // Calculate days since base event
            var daysSinceBase = (eventId - 3000) / 3 * 7; // Rough calculation
            var targetDate = baseDate.AddDays(daysSinceBase);
            
            // Adjust to the correct day of week
            while (targetDate.DayOfWeek != eventDay)
            {
                targetDate = targetDate.AddDays(1);
            }
            
            return targetDate.Date.Add(eventTime);
        }

        public void CreateSpatialDatabaseSchema()
        {
            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                string createEventsTable = @"
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='spatial_events' AND xtype='U')
                    CREATE TABLE spatial_events (
                        id INT PRIMARY KEY,
                        event_date DATE NOT NULL,
                        event_day NVARCHAR(10) NOT NULL,
                        event_time TIME NOT NULL,
                        created_date DATETIME DEFAULT GETDATE()
                    )";

                string createCoordinatesTable = @"
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='spatial_coordinates' AND xtype='U')
                    CREATE TABLE spatial_coordinates (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        event_id INT NOT NULL,
                        coordinate_order INT NOT NULL,
                        x_coordinate FLOAT NOT NULL,
                        y_coordinate FLOAT NOT NULL,
                        FOREIGN KEY (event_id) REFERENCES spatial_events(id)
                    )";

                using var command1 = new SqlCommand(createEventsTable, connection);
                command1.ExecuteNonQuery();

                using var command2 = new SqlCommand(createCoordinatesTable, connection);
                command2.ExecuteNonQuery();

                Console.WriteLine("✅ Spatial database schema created successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error creating spatial database schema: {ex.Message}");
            }
        }
    }
}
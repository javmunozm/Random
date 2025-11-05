using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Data.SqlClient;

namespace DataProcessor.Connections
{
    public class DatabaseConnection
    {
        private readonly string connectionString;

        public DatabaseConnection()
        {
            connectionString = "Server=DESKTOP-QR14EDK\\SQLEXPRESS01;Database=LuckyDb;Integrated Security=true;TrustServerCertificate=true;";
        }

        public List<SeriesData> LoadHistoricalDataBefore(int beforeSeriesId)
        {
            var seriesData = new List<SeriesData>();

            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                var query = @"
                    SELECT e.Id as SeriesId,
                           el.Element1, el.Element2, el.Element3, el.Element4, el.Element5, el.Element6, el.Element7,
                           el.Element8, el.Element9, el.Element10, el.Element11, el.Element12, el.Element13, el.Element14
                    FROM dbo.event e
                    INNER JOIN dbo.elements el ON e.Id = el.IdEvents
                    WHERE e.Id < @BeforeSeriesId
                    ORDER BY e.Id, el.Id";

                using var command = new SqlCommand(query, connection);
                command.Parameters.AddWithValue("@BeforeSeriesId", beforeSeriesId);

                using var reader = command.ExecuteReader();
                var currentSeriesId = -1;
                var currentCombinations = new List<List<int>>();

                while (reader.Read())
                {
                    var seriesId = Convert.ToInt32(reader["SeriesId"]);
                    
                    if (seriesId != currentSeriesId)
                    {
                        // Save previous series if exists
                        if (currentSeriesId != -1 && currentCombinations.Any())
                        {
                            seriesData.Add(new SeriesData
                            {
                                SeriesId = currentSeriesId,
                                AllCombinations = new List<List<int>>(currentCombinations)
                            });
                        }
                        
                        currentSeriesId = seriesId;
                        currentCombinations.Clear();
                    }

                    // Read the 14 elements for this combination
                    var combination = new List<int>();
                    for (int i = 1; i <= 14; i++)
                    {
                        var value = reader[$"Element{i}"];
                        if (value != DBNull.Value)
                        {
                            combination.Add(Convert.ToInt32(value));
                        }
                    }

                    if (combination.Count == 14)
                    {
                        combination.Sort();
                        currentCombinations.Add(combination);
                    }
                }

                // Don't forget the last series
                if (currentSeriesId != -1 && currentCombinations.Any())
                {
                    seriesData.Add(new SeriesData
                    {
                        SeriesId = currentSeriesId,
                        AllCombinations = new List<List<int>>(currentCombinations)
                    });
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading historical data: {ex.Message}");
            }

            return seriesData;
        }

        public List<List<int>> GetActualResultsForSeries(int seriesId)
        {
            var results = new List<List<int>>();

            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                var query = @"
                    SELECT el.Element1, el.Element2, el.Element3, el.Element4, el.Element5, el.Element6, el.Element7,
                           el.Element8, el.Element9, el.Element10, el.Element11, el.Element12, el.Element13, el.Element14
                    FROM dbo.elements el
                    INNER JOIN dbo.event e ON e.Id = el.IdEvents
                    WHERE e.Id = @SeriesId
                    ORDER BY el.Id";

                using var command = new SqlCommand(query, connection);
                command.Parameters.AddWithValue("@SeriesId", seriesId);

                using var reader = command.ExecuteReader();

                while (reader.Read())
                {
                    var combination = new List<int>();
                    for (int i = 1; i <= 14; i++)
                    {
                        var value = reader[$"Element{i}"];
                        if (value != DBNull.Value)
                        {
                            combination.Add(Convert.ToInt32(value));
                        }
                    }

                    if (combination.Count == 14)
                    {
                        combination.Sort();
                        results.Add(combination);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading actual results for series {seriesId}: {ex.Message}");
            }

            return results;
        }

        public bool SeriesExists(int seriesId)
        {
            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                var query = "SELECT COUNT(*) FROM dbo.event WHERE Id = @SeriesId";
                using var command = new SqlCommand(query, connection);
                command.Parameters.AddWithValue("@SeriesId", seriesId);

                var count = (int)command.ExecuteScalar();
                return count > 0;
            }
            catch
            {
                return false;
            }
        }

        public int GetLatestSeriesId()
        {
            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                var query = "SELECT MAX(Id) FROM dbo.event";
                using var command = new SqlCommand(query, connection);

                var result = command.ExecuteScalar();
                return result == DBNull.Value ? 0 : Convert.ToInt32(result);
            }
            catch
            {
                return 0;
            }
        }

        public bool InsertSeriesData(int seriesId, List<List<int>> combinations)
        {
            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                // First, insert into event table
                var eventQuery = "INSERT INTO dbo.event (Id) VALUES (@SeriesId)";
                using var eventCommand = new SqlCommand(eventQuery, connection);
                eventCommand.Parameters.AddWithValue("@SeriesId", seriesId);
                eventCommand.ExecuteNonQuery();

                // Then insert each combination into elements table
                foreach (var combination in combinations)
                {
                    if (combination.Count == 14)
                    {
                        var elementsQuery = @"
                            INSERT INTO dbo.elements (IdEvents, Element1, Element2, Element3, Element4, Element5, Element6, Element7,
                                                    Element8, Element9, Element10, Element11, Element12, Element13, Element14)
                            VALUES (@IdEvents, @E1, @E2, @E3, @E4, @E5, @E6, @E7, @E8, @E9, @E10, @E11, @E12, @E13, @E14)";
                        
                        using var elementsCommand = new SqlCommand(elementsQuery, connection);
                        elementsCommand.Parameters.AddWithValue("@IdEvents", seriesId);
                        
                        for (int i = 0; i < 14; i++)
                        {
                            elementsCommand.Parameters.AddWithValue($"@E{i + 1}", combination[i]);
                        }
                        
                        elementsCommand.ExecuteNonQuery();
                    }
                }

                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error inserting series data: {ex.Message}");
                return false;
            }
        }

        public bool DeleteSeriesData(int seriesId)
        {
            try
            {
                using var connection = new SqlConnection(connectionString);
                connection.Open();

                // First, delete from elements table
                var elementsQuery = "DELETE FROM dbo.elements WHERE IdEvents = @SeriesId";
                using var elementsCommand = new SqlCommand(elementsQuery, connection);
                elementsCommand.Parameters.AddWithValue("@SeriesId", seriesId);
                var deletedElements = elementsCommand.ExecuteNonQuery();

                // Then delete from event table
                var eventQuery = "DELETE FROM dbo.event WHERE Id = @SeriesId";
                using var eventCommand = new SqlCommand(eventQuery, connection);
                eventCommand.Parameters.AddWithValue("@SeriesId", seriesId);
                var deletedEvents = eventCommand.ExecuteNonQuery();

                Console.WriteLine($"Deleted {deletedElements} element records and {deletedEvents} event records for series {seriesId}");
                return deletedEvents > 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error deleting series data: {ex.Message}");
                return false;
            }
        }
    }

    public class SeriesData
    {
        public int SeriesId { get; set; }
        public List<List<int>> AllCombinations { get; set; } = new();
        public DateTime Date { get; set; } = DateTime.Now;
    }
}
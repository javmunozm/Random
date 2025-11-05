using System;
using Microsoft.Data.SqlClient;

namespace DatabaseQuery
{
    class Program
    {
        static void Main(string[] args)
        {
            string connectionString = "Server=DESKTOP-QR14EDK\\SQLEXPRESS01;Database=LuckyDb;Integrated Security=true;TrustServerCertificate=true;";

            try
            {
                using (SqlConnection connection = new SqlConnection(connectionString))
                {
                    connection.Open();
                    Console.WriteLine("✅ Successfully connected to LuckyDb database");
                    Console.WriteLine("================================================");

                    // Query 1: Count of events (series)
                    string eventCountQuery = "SELECT COUNT(*) FROM dbo.event";
                    using (SqlCommand command = new SqlCommand(eventCountQuery, connection))
                    {
                        int eventCount = (int)command.ExecuteScalar();
                        Console.WriteLine($"📊 Total Events/Series: {eventCount}");
                    }

                    // Query 2: Count of elements (combinations)
                    string elementsCountQuery = "SELECT COUNT(*) FROM dbo.elements";
                    using (SqlCommand command = new SqlCommand(elementsCountQuery, connection))
                    {
                        int elementsCount = (int)command.ExecuteScalar();
                        Console.WriteLine($"📊 Total Element Combinations: {elementsCount}");
                    }

                    // Query 3: Min and Max series IDs
                    string rangeQuery = "SELECT MIN(Id), MAX(Id) FROM dbo.event";
                    using (SqlCommand command = new SqlCommand(rangeQuery, connection))
                    {
                        using (SqlDataReader reader = command.ExecuteReader())
                        {
                            if (reader.Read())
                            {
                                var minId = reader.IsDBNull(0) ? (int?)null : Convert.ToInt32(reader.GetValue(0));
                                var maxId = reader.IsDBNull(1) ? (int?)null : Convert.ToInt32(reader.GetValue(1));
                                
                                Console.WriteLine($"📊 Series ID Range: {minId} to {maxId}");
                                
                                if (minId.HasValue && maxId.HasValue)
                                {
                                    int range = maxId.Value - minId.Value + 1;
                                    Console.WriteLine($"📊 Total Series Range Span: {range}");
                                }
                            }
                        }
                    }

                    // Additional Query: Sample of recent series
                    Console.WriteLine("\n🔍 Sample of Most Recent Series:");
                    string recentSeriesQuery = "SELECT TOP 10 Id FROM dbo.event ORDER BY Id DESC";
                    using (SqlCommand command = new SqlCommand(recentSeriesQuery, connection))
                    {
                        using (SqlDataReader reader = command.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                int seriesId = Convert.ToInt32(reader.GetValue(0));
                                Console.WriteLine($"   - Series: {seriesId}");
                            }
                        }
                    }
                }
            }
            catch (SqlException ex)
            {
                Console.WriteLine($"❌ SQL Error: {ex.Message}");
                Console.WriteLine($"Error Number: {ex.Number}");
                Console.WriteLine($"Severity: {ex.Class}");
                Console.WriteLine($"State: {ex.State}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ General Error: {ex.Message}");
            }

            Console.WriteLine("\n✅ Database analysis complete.");
        }
    }
}
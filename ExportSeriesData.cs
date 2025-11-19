using System;
using System.Collections.Generic;
using System.Data;
using Microsoft.Data.SqlClient;
using System.Text.Json;
using System.IO;

class ExportSeriesData
{
    static void Main(string[] args)
    {
        int startSeries = 3141;
        int endSeries = 3150;

        if (args.Length >= 2)
        {
            startSeries = int.Parse(args[0]);
            endSeries = int.Parse(args[1]);
        }

        var allData = new Dictionary<string, object>();
        var seriesData = new List<object>();

        string connectionString = "Server=localhost;Database=LuckyDb;User Id=lottery_app;Password=SecurePassword123!;TrustServerCertificate=True;";

        using (var connection = new SqlConnection(connectionString))
        {
            connection.Open();

            for (int seriesId = startSeries; seriesId <= endSeries; seriesId++)
            {
                Console.WriteLine($"Loading Series {seriesId}...");

                string query = @"
                    SELECT e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12, e13, e14
                    FROM elements el
                    JOIN event ev ON el.event_id = ev.event_id
                    WHERE ev.series_id = @seriesId
                    ORDER BY el.combination_id";

                using (var command = new SqlCommand(query, connection))
                {
                    command.Parameters.AddWithValue("@seriesId", seriesId);

                    var events = new List<List<int>>();

                    using (var reader = command.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            var numbers = new List<int>();
                            for (int i = 0; i < 14; i++)
                            {
                                numbers.Add(reader.GetInt32(i));
                            }
                            numbers.Sort();
                            events.Add(numbers);
                        }
                    }

                    seriesData.Add(new
                    {
                        series_id = seriesId,
                        events = events,
                        event_count = events.Count
                    });

                    Console.WriteLine($"  Loaded {events.Count} events");
                }
            }
        }

        allData["start_series"] = startSeries;
        allData["end_series"] = endSeries;
        allData["series_data"] = seriesData;
        allData["export_date"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

        string outputFile = "python_ml/series_3141_3150_data.json";
        string json = JsonSerializer.Serialize(allData, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(outputFile, json);

        Console.WriteLine($"\n✅ Data exported to: {outputFile}");
        Console.WriteLine($"Series: {startSeries}-{endSeries}");
        Console.WriteLine($"Total series: {seriesData.Count}");
    }
}

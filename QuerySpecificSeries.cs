using System;
using System.Collections.Generic;
using DataProcessor.Connections;

class QuerySpecificSeries
{
    static void Main()
    {
        var db = new DatabaseConnection();

        // Check series 3125, 3126, 3127, and 3128
        foreach (int seriesId in new[] { 3125, 3126, 3127, 3128 })
        {
            Console.WriteLine($"=== Series {seriesId} Actual Results ===");

            var results = db.GetActualResultsForSeries(seriesId);

            if (results.Count > 0)
            {
                Console.WriteLine($"Found {results.Count} combinations for Series {seriesId}:");

                for (int i = 0; i < results.Count; i++)
                {
                    var combination = string.Join(" ", results[i].Select(n => n.ToString("D2")));
                    Console.WriteLine($"Event {i + 1}: {combination}");
                }
            }
            else
            {
                Console.WriteLine($"No data found for Series {seriesId}");
            }
            Console.WriteLine();
        }
    }
}
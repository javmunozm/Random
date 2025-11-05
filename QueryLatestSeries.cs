using System;
using DataProcessor.Connections;

namespace DataProcessor
{
    class QueryLatestSeries
    {
        static void Main(string[] args)
        {
            var db = new DatabaseConnection();

            Console.WriteLine("=== Querying Latest Series in Database ===");
            Console.WriteLine();

            int latestSeriesId = db.GetLatestSeriesId();

            if (latestSeriesId > 0)
            {
                Console.WriteLine($"Latest Series ID: {latestSeriesId}");
                Console.WriteLine();

                // Get the actual results for this series
                var results = db.GetActualResultsForSeries(latestSeriesId);

                if (results.Count > 0)
                {
                    Console.WriteLine($"Number of events in Series {latestSeriesId}: {results.Count}");
                    Console.WriteLine();

                    for (int i = 0; i < results.Count; i++)
                    {
                        Console.WriteLine($"Event {i + 1}: {string.Join(" ", results[i].Select(n => n.ToString("D2")))}");
                    }
                }
                else
                {
                    Console.WriteLine($"No data found for Series {latestSeriesId}");
                }
            }
            else
            {
                Console.WriteLine("No series found in database.");
            }
        }
    }
}

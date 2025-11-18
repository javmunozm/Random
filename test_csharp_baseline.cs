using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Models;
using DataProcessor.Connections;

namespace DataProcessor
{
    /// <summary>
    /// Test C# TrueLearningModel baseline performance on Series 3146-3150
    /// This establishes the performance benchmark that Python should match
    /// </summary>
    class TestCSharpBaseline
    {
        static void Main(string[] args)
        {
            Console.WriteLine("================================================================================");
            Console.WriteLine("C# TRUELEARNINGMODEL BASELINE TEST - SERIES 3146-3150");
            Console.WriteLine("================================================================================\n");

            var db = new DatabaseConnection();
            var model = new TrueLearningModel();

            // Training series: 2980-3145
            Console.WriteLine("Phase 1: Loading training data (Series 2980-3145)...");
            var trainingSeries = db.LoadHistoricalDataBefore(3146);
            Console.WriteLine($"Loaded {trainingSeries.Count} training series\n");

            foreach (var series in trainingSeries)
            {
                model.LearnFromSeries(series);
            }

            // Validation series: 3146-3150
            var validationSeriesIds = new[] { 3146, 3147, 3148, 3149, 3150 };
            var accuracies = new List<double>();
            var bestMatches = new List<int>();

            Console.WriteLine("Phase 2: Iterative validation on Series 3146-3150");
            Console.WriteLine("================================================================================\n");

            foreach (var seriesId in validationSeriesIds)
            {
                Console.WriteLine($"\n--- Series {seriesId} ---");

                // Get actual results
                var actualResults = db.GetActualResultsForSeries(seriesId);
                if (actualResults == null || !actualResults.Any())
                {
                    Console.WriteLine($"❌ No data found for Series {seriesId}");
                    continue;
                }

                // Generate prediction
                var prediction = model.PredictBestCombination(seriesId);
                Console.WriteLine($"🎯 Prediction: {string.Join(" ", prediction.Select(n => n.ToString("D2")))}");

                // Calculate best match across all 7 events
                int bestMatch = 0;
                List<int> bestEvent = null;
                int eventNum = 1;

                foreach (var actual in actualResults)
                {
                    var matchCount = prediction.Intersect(actual).Count();
                    if (matchCount > bestMatch)
                    {
                        bestMatch = matchCount;
                        bestEvent = actual;
                    }
                    Console.WriteLine($"   Event {eventNum}: {matchCount}/14 match");
                    eventNum++;
                }

                var accuracy = (bestMatch / 14.0) * 100.0;
                accuracies.Add(accuracy);
                bestMatches.Add(bestMatch);

                Console.WriteLine($"✅ Best Match: {bestMatch}/14 ({accuracy:F1}%)");
                Console.WriteLine($"   Best Event: {string.Join(" ", bestEvent.Select(n => n.ToString("D2")))}");

                // Learn from this series
                model.ValidateAndLearn(seriesId, prediction, actualResults);
            }

            // Summary
            Console.WriteLine("\n================================================================================");
            Console.WriteLine("C# MODEL SUMMARY");
            Console.WriteLine("================================================================================");

            var avgAccuracy = accuracies.Average();
            var avgBestMatch = bestMatches.Average();
            var peakAccuracy = accuracies.Max();
            var peakMatch = bestMatches.Max();

            Console.WriteLine($"\nTest Series: 3146-3150 (5 series)");
            Console.WriteLine($"Training Data: 2980-3145 ({trainingSeries.Count} series)");
            Console.WriteLine();
            Console.WriteLine($"Average Accuracy: {avgAccuracy:F1}% ({avgBestMatch:F1}/14 numbers)");
            Console.WriteLine($"Peak Accuracy: {peakAccuracy:F1}% ({peakMatch}/14 numbers)");
            Console.WriteLine();
            Console.WriteLine("Individual Results:");
            for (int i = 0; i < validationSeriesIds.Length; i++)
            {
                Console.WriteLine($"  Series {validationSeriesIds[i]}: {bestMatches[i]}/14 ({accuracies[i]:F1}%)");
            }

            Console.WriteLine("\n================================================================================");
            Console.WriteLine("C# MODEL PARAMETERS");
            Console.WriteLine("================================================================================");
            Console.WriteLine("RECENT_SERIES_LOOKBACK: 16");
            Console.WriteLine("Cold/Hot Boost: 50.0x");
            Console.WriteLine("Pair Affinity Multiplier: 25.0x");
            Console.WriteLine("Triplet Affinity Multiplier: 35.0x");
            Console.WriteLine("Candidate Pool: 10,000");
            Console.WriteLine("Candidates to Score: 1,000");
            Console.WriteLine("================================================================================\n");
        }
    }
}

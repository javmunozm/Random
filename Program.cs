using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Methods;
using DataProcessor.Models;
using DataProcessor.Connections;

namespace DataProcessor
{
    class TrainingResult
    {
        public int SeriesId { get; set; }
        public double BestAccuracy { get; set; }
        public double AvgAccuracy { get; set; }
    }

    class Program
    {
        // Series ID validation constants
        private const int MIN_SERIES_ID = 2898;  // First series in database
        private const int MAX_SERIES_ID = 3200;  // Maximum reasonable series ID
        private const int CURRENT_LATEST_SERIES = 3135;  // Latest series with actual results

        /// <summary>
        /// Validates that a series ID is within acceptable range
        /// </summary>
        private static bool ValidateSeriesId(int seriesId, out string errorMessage)
        {
            if (seriesId < MIN_SERIES_ID)
            {
                errorMessage = $"Series ID {seriesId} is too old. Minimum series ID is {MIN_SERIES_ID}.";
                return false;
            }

            if (seriesId > MAX_SERIES_ID)
            {
                errorMessage = $"Series ID {seriesId} is beyond reasonable range. Maximum is {MAX_SERIES_ID}.";
                return false;
            }

            if (seriesId <= CURRENT_LATEST_SERIES)
            {
                // Warning for historical series (valid but informational)
                errorMessage = $"Note: Series {seriesId} is historical. Latest series with actual results is {CURRENT_LATEST_SERIES}.";
            }
            else
            {
                errorMessage = string.Empty;
            }

            return true;
        }

        static void Main(string[] args)
        {
            Console.WriteLine("True Learning Prediction System - Phase 1 ENHANCED");
            Console.WriteLine("===================================================");
            Console.WriteLine();

            // Default to real-train if no arguments provided
            if (args.Length == 0)
            {
                args = new[] { "real-train" };
                Console.WriteLine("ℹ️  No command specified - running default command: real-train");
                Console.WriteLine();
            }

            try
            {
                switch (args[0].ToLower())
                {
                    case "predict":
                        if (args.Length > 1 && int.TryParse(args[1], out int seriesId))
                        {
                            if (!ValidateSeriesId(seriesId, out string validationMessage))
                            {
                                Console.WriteLine($"❌ {validationMessage}");
                                Console.WriteLine();
                                break;
                            }

                            if (!string.IsNullOrEmpty(validationMessage))
                            {
                                Console.WriteLine($"ℹ️  {validationMessage}");
                                Console.WriteLine();
                            }

                            Console.WriteLine($"=== Predicting Series {seriesId} ===");
                            var engine = new LearningEngine();
                            engine.PredictAndValidate(seriesId);
                        }
                        else
                        {
                            Console.WriteLine("Usage: dotnet run predict <series_id>");
                            Console.WriteLine("Example: dotnet run predict 3133");
                        }
                        break;

                    case "insert":
                        if (args.Length > 1 && int.TryParse(args[1], out int insertSeriesId))
                        {
                            if (!ValidateSeriesId(insertSeriesId, out string insertValidationMessage))
                            {
                                Console.WriteLine($"❌ {insertValidationMessage}");
                                Console.WriteLine();
                                break;
                            }

                            var engine = new LearningEngine();
                            engine.InsertActualResults(insertSeriesId);
                        }
                        else
                        {
                            Console.WriteLine("Usage: dotnet run insert <series_id>");
                            Console.WriteLine("Example: dotnet run insert 3144");
                        }
                        break;

                    case "real-train":
                        Console.WriteLine("========================================");
                        Console.WriteLine("REAL ITERATIVE ML TRAINING");
                        Console.WriteLine("========================================");
                        Console.WriteLine();

                        var db = new DatabaseConnection();
                        var model = new TrueLearningModel();

                        // Get latest series from database
                        int latestSeries = db.GetLatestSeriesId();

                        // Define validation window size (number of most recent series to validate on)
                        // OPTIMIZED: Reduced from 16 to 8 for better bulk training while keeping iterative learning
                        int validationWindowSize = 8;

                        // Calculate validation start (use last N series for validation)
                        // Train on ALL data before the validation window
                        int validationStart = latestSeries - validationWindowSize + 1;
                        int trainingEnd = validationStart - 1;

                        // Train on all historical data before validation window
                        Console.WriteLine($"Phase 1: Training on all historical data up to series {trainingEnd}");
                        Console.WriteLine($"         (Optimized: Using {validationWindowSize} series for iterative validation)");
                        Console.WriteLine("====================================");
                        var trainingData = db.LoadHistoricalDataBefore(validationStart);

                        foreach (var series in trainingData)
                        {
                            var pattern = new SeriesPattern
                            {
                                SeriesId = series.SeriesId,
                                Combinations = series.AllCombinations
                            };
                            model.LearnFromSeries(pattern);
                        }

                        Console.WriteLine($"✅ Trained on {trainingData.Count} historical series");
                        Console.WriteLine();

                        // Iterative training: validation start -> latest series
                        // Build list of series IDs that actually exist in database
                        var seriesIds = new List<int>();
                        for (int sid = validationStart; sid <= latestSeries; sid++)
                        {
                            if (db.SeriesExists(sid))
                            {
                                seriesIds.Add(sid);
                            }
                        }

                        Console.WriteLine($"Phase 2: Iterative validation on {seriesIds.Count} series ({validationStart}-{latestSeries})");
                        Console.WriteLine("====================================");
                        Console.WriteLine();

                        var resultsList = new List<TrainingResult>();

                        foreach (var sid in seriesIds)
                        {
                            Console.WriteLine($"========================================");
                            Console.WriteLine($"Series {sid}");
                            Console.WriteLine($"========================================");

                            // Generate prediction
                            Console.WriteLine($"🔮 Generating prediction for Series {sid}...");
                            var prediction = model.PredictBestCombination(sid);
                            Console.WriteLine($"Prediction: {string.Join(" ", prediction.Select(n => n.ToString("D2")))}");
                            Console.WriteLine();

                            // Get actual results
                            var actualResults = db.GetActualResultsForSeries(sid);

                            if (actualResults.Count == 0)
                            {
                                Console.WriteLine($"❌ ERROR: No actual results found for Series {sid}");
                                break;
                            }

                            // Calculate accuracy for each event
                            Console.WriteLine("📊 Validation against actual results:");
                            var accuracies = new List<double>();
                            for (int i = 0; i < actualResults.Count; i++)
                            {
                                var actual = actualResults[i];
                                var matches = prediction.Intersect(actual).Count();
                                var accuracy = (double)matches / 14.0;
                                accuracies.Add(accuracy);

                                Console.WriteLine($"  Event {i+1}: {matches}/14 ({accuracy:P1})");
                            }

                            var bestAccuracy = accuracies.Max();
                            var avgAccuracy = accuracies.Average();

                            Console.WriteLine();
                            Console.WriteLine($"✨ Best Match: {bestAccuracy:P1}");
                            Console.WriteLine($"📊 Average: {avgAccuracy:P1}");
                            Console.WriteLine();

                            // LEARN from the results (this is the KEY difference)
                            model.ValidateAndLearn(sid, prediction, actualResults);
                            Console.WriteLine();

                            resultsList.Add(new TrainingResult { SeriesId = sid, BestAccuracy = bestAccuracy, AvgAccuracy = avgAccuracy });
                        }

                        // Summary
                        Console.WriteLine("========================================");
                        Console.WriteLine("TRAINING SUMMARY");
                        Console.WriteLine("========================================");
                        Console.WriteLine();
                        Console.WriteLine("Series | Best Match | Average");
                        Console.WriteLine("-------|------------|--------");
                        foreach (var result in resultsList)
                        {
                            Console.WriteLine($" {result.SeriesId} | {result.BestAccuracy,10:P1} | {result.AvgAccuracy:P1}");
                        }
                        Console.WriteLine();

                        var avgBest = resultsList.Average(r => r.BestAccuracy);
                        var avgAvg = resultsList.Average(r => r.AvgAccuracy);
                        Console.WriteLine($"📈 Overall Best Average: {avgBest:P1}");
                        Console.WriteLine($"📊 Overall Average: {avgAvg:P1}");
                        Console.WriteLine();

                        // Check for improvement
                        if (resultsList.Count >= 6)
                        {
                            var firstThree = resultsList.Take(3).Average(r => r.AvgAccuracy);
                            var lastThree = resultsList.TakeLast(3).Average(r => r.AvgAccuracy);
                            var improvement = lastThree - firstThree;

                            Console.WriteLine($"📉 First 3 series average: {firstThree:P1}");
                            Console.WriteLine($"📈 Last 3 series average: {lastThree:P1}");
                            Console.WriteLine($"🎯 Improvement: {improvement:+0.0%;-0.0%;0.0%} ({(improvement > 0 ? "✅ LEARNING DETECTED" : "❌ NO IMPROVEMENT")})");
                            Console.WriteLine();
                        }

                        // Save training summary to JSON file
                        var summaryjson = new
                        {
                            validation_range = $"{validationStart}-{latestSeries}",
                            validation_series_count = seriesIds.Count,
                            overall_best_average = avgBest,
                            overall_average = avgAvg,
                            series_results = resultsList.Select(r => new
                            {
                                series_id = r.SeriesId,
                                best_accuracy = r.BestAccuracy,
                                avg_accuracy = r.AvgAccuracy
                            }).ToList(),
                            improvement_analysis = resultsList.Count >= 6 ? new
                            {
                                first_three_avg = resultsList.Take(3).Average(r => r.AvgAccuracy),
                                last_three_avg = resultsList.TakeLast(3).Average(r => r.AvgAccuracy),
                                improvement = resultsList.TakeLast(3).Average(r => r.AvgAccuracy) - resultsList.Take(3).Average(r => r.AvgAccuracy)
                            } : null
                        };
                        var summaryPath = Path.Combine("Results", "real_train_validation_summary.json");
                        File.WriteAllText(summaryPath, System.Text.Json.JsonSerializer.Serialize(summaryjson, new System.Text.Json.JsonSerializerOptions { WriteIndented = true }));
                        Console.WriteLine($"📁 Validation summary saved to: {summaryPath}");
                        Console.WriteLine();

                        // Final prediction for next series
                        int nextSeries = latestSeries + 1;
                        Console.WriteLine("========================================");
                        Console.WriteLine($"FINAL PREDICTION: Series {nextSeries}");
                        Console.WriteLine("========================================");
                        Console.WriteLine();

                        var finalPrediction = model.PredictBestCombination(nextSeries);
                        Console.WriteLine($"🎯 Prediction: {string.Join(" ", finalPrediction.Select(n => n.ToString("D2")))}");
                        Console.WriteLine();
                        Console.WriteLine($"✅ Trained on {model.GetTrainingSize()} series");
                        Console.WriteLine($"✅ Model has learned from actual results of {validationStart}-{latestSeries} ({seriesIds.Count} series)");
                        Console.WriteLine();
                        break;

                    case "status":
                        Console.WriteLine("=== Database Status ===");
                        Console.WriteLine();

                        var statusDb = new DatabaseConnection();
                        int latestSeriesId = statusDb.GetLatestSeriesId();

                        if (latestSeriesId > 0)
                        {
                            Console.WriteLine($"Latest Series ID in Database: {latestSeriesId}");
                            Console.WriteLine();

                            // Get the actual results for this series
                            var statusResults = statusDb.GetActualResultsForSeries(latestSeriesId);

                            if (statusResults.Count > 0)
                            {
                                Console.WriteLine($"Number of events in Series {latestSeriesId}: {statusResults.Count}");
                                Console.WriteLine();

                                for (int i = 0; i < statusResults.Count; i++)
                                {
                                    Console.WriteLine($"Event {i + 1}: {string.Join(" ", statusResults[i].Select(n => n.ToString("D2")))}");
                                }

                                // Show critical numbers
                                Console.WriteLine();
                                var allNumbers = statusResults.SelectMany(r => r).ToList();
                                var numberFrequency = allNumbers.GroupBy(n => n)
                                    .Select(g => new { Number = g.Key, Count = g.Count() })
                                    .OrderByDescending(x => x.Count)
                                    .ToList();

                                var criticalNumbers = numberFrequency.Where(x => x.Count >= 5).ToList();
                                if (criticalNumbers.Any())
                                {
                                    Console.WriteLine($"🔥 Critical Numbers (5+ events): {string.Join(" ", criticalNumbers.Select(x => $"{x.Number:D2}({x.Count})"))}");
                                }
                            }
                            else
                            {
                                Console.WriteLine($"❌ No data found for Series {latestSeriesId}");
                            }
                        }
                        else
                        {
                            Console.WriteLine("❌ No series found in database.");
                        }
                        Console.WriteLine();
                        break;

                    case "evolve":
                        Console.WriteLine("================================================================================");
                        Console.WriteLine("EVOLUTIONARY ML SYSTEM - CONTINUOUS LEARNING & IMPROVEMENT");
                        Console.WriteLine("================================================================================");
                        Console.WriteLine();

                        var evolModel = new EvolutionaryModel();
                        var dbEvolve = new DatabaseConnection();

                        // Load all training data
                        var trainingDataEvolve = dbEvolve.LoadHistoricalDataBefore(3124);

                        Console.WriteLine($"📚 Pre-training on {trainingDataEvolve.Count} historical series...");
                        foreach (var seriesEvolve in trainingDataEvolve)
                        {
                            var patternEvolve = new SeriesPattern
                            {
                                SeriesId = seriesEvolve.SeriesId,
                                Combinations = seriesEvolve.AllCombinations
                            };
                            evolModel.Evolve(patternEvolve);
                        }
                        Console.WriteLine($"✅ Pre-training complete - Generation {evolModel.GetGeneration()}");
                        Console.WriteLine();

                        // Evolutionary learning: 3124 -> 3132
                        var evolutionSeriesIds = new[] { 3124, 3125, 3126, 3127, 3128, 3129, 3130, 3132 };
                        var evolutionResults = new List<(int seriesId, double accuracy, int generation)>();

                        Console.WriteLine(new string('=', 80));
                        Console.WriteLine("EVOLUTIONARY TRAINING");
                        Console.WriteLine(new string('=', 80));
                        Console.WriteLine();

                        foreach (var evoSeriesId in evolutionSeriesIds)
                        {
                            Console.WriteLine($"Generation {evolModel.GetGeneration()} → Series {evoSeriesId}");
                            Console.WriteLine(new string('-', 80));

                            var evoPrediction = evolModel.Predict(evoSeriesId);
                            Console.WriteLine($"Prediction: {string.Join(" ", evoPrediction.Select(n => n.ToString("D2")))}");

                            var evoActualResults = dbEvolve.GetActualResultsForSeries(evoSeriesId);

                            if (evoActualResults.Count == 0)
                            {
                                Console.WriteLine($"❌ No actual results for Series {evoSeriesId}");
                                break;
                            }

                            var evoBestMatch = evoActualResults.Max(actual => evoPrediction.Intersect(actual).Count());
                            var evoAccuracy = (double)evoBestMatch / 14.0;

                            evolModel.ValidateAndEvolve(evoSeriesId, evoPrediction, evoActualResults);
                            evolutionResults.Add((evoSeriesId, evoAccuracy, evolModel.GetGeneration()));

                            Console.WriteLine();
                        }

                        // Save checkpoint
                        evolModel.SaveCheckpoint();

                        // Performance summary
                        Console.WriteLine(new string('=', 80));
                        Console.WriteLine("EVOLUTIONARY PERFORMANCE");
                        Console.WriteLine(new string('=', 80));
                        Console.WriteLine();

                        var perfHistory = evolModel.GetPerformanceHistory();
                        if (perfHistory.Count >= 7)
                        {
                            var last8 = perfHistory.TakeLast(8).ToList();
                            Console.WriteLine("Recent Performance:");
                            foreach (var perf in last8)
                            {
                                var gen = evolutionResults.FirstOrDefault(r => r.seriesId == perf.SeriesId).generation;
                                Console.WriteLine($"  Gen {gen}: " +
                                    $"Series {perf.SeriesId} - {perf.BestAccuracy:P1} " +
                                    $"(Critical: {perf.CriticalNumbersHit.Count}/{perf.CriticalNumbersHit.Count + perf.CriticalNumbersMissed.Count})");
                            }
                            Console.WriteLine();

                            var first3Avg = last8.Take(3).Average(p => p.BestAccuracy);
                            var last3Avg = last8.TakeLast(3).Average(p => p.BestAccuracy);
                            var evolImprovement = last3Avg - first3Avg;

                            Console.WriteLine($"First 3 series avg: {first3Avg:P1}");
                            Console.WriteLine($"Last 3 series avg: {last3Avg:P1}");
                            Console.WriteLine($"Evolution: {evolImprovement:+0.0%;-0.0%;0.0%} " +
                                $"({(evolImprovement > 0 ? "✅ EVOLVING" : evolImprovement < 0 ? "⚠️  DEGRADING" : "➖ STABLE")})");
                        }

                        Console.WriteLine();

                        // Final prediction for 3133
                        Console.WriteLine(new string('=', 80));
                        Console.WriteLine($"FINAL PREDICTION - Generation {evolModel.GetGeneration()}");
                        Console.WriteLine(new string('=', 80));
                        Console.WriteLine();

                        var finalEvoPrediction = evolModel.Predict(3133);
                        Console.WriteLine($"🎯 Series 3133: {string.Join(" ", finalEvoPrediction.Select(n => n.ToString("D2")))}");
                        Console.WriteLine();
                        Console.WriteLine($"✅ Model saved to: Models/evolution_checkpoint.json");
                        Console.WriteLine($"✅ Generation: {evolModel.GetGeneration()}");
                        Console.WriteLine($"✅ Can continue evolving with new data");
                        Console.WriteLine();
                        break;

                    case "help":
                    case "--help":
                    case "-h":
                        ShowUsage();
                        break;

                    default:
                        Console.WriteLine($"❌ Unknown command: {args[0]}");
                        Console.WriteLine();
                        ShowUsage();
                        break;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error: {ex.Message}");
                Console.WriteLine();
                Console.WriteLine("Stack Trace:");
                Console.WriteLine(ex.StackTrace);
                Environment.Exit(1);
            }
        }

        static void ShowUsage()
        {
            Console.WriteLine("=== TRUE LEARNING MODEL - ACTIVE COMMANDS ===");
            Console.WriteLine();
            Console.WriteLine("PRIMARY COMMANDS:");
            Console.WriteLine("  dotnet run                        - ✅ DEFAULT: Run real-train (recommended)");
            Console.WriteLine("  dotnet run real-train             - OPTIMIZED: Bulk train + 8 iterative validations");
            Console.WriteLine("  dotnet run predict <series_id>    - Quick prediction using TrueLearningModel");
            Console.WriteLine("  dotnet run insert <series_id>     - Insert actual results for series");
            Console.WriteLine("  dotnet run status                 - Show latest database entry and critical numbers");
            Console.WriteLine("  dotnet run evolve                 - Evolutionary training with checkpoints");
            Console.WriteLine();
            Console.WriteLine("EXAMPLES:");
            Console.WriteLine("  dotnet run                        - ✅ Run full training cycle (DEFAULT)");
            Console.WriteLine("  dotnet run insert 3140            - Insert actual results after draw");
            Console.WriteLine("  dotnet run                        - Generate next prediction with updated data");
            Console.WriteLine("  dotnet run predict 3140           - Quick prediction (less accurate)");
            Console.WriteLine("  dotnet run status                 - Check latest series in database");
            Console.WriteLine();
            Console.WriteLine("SYSTEM STATUS:");
            Console.WriteLine("  Model: TrueLearningModel (Phase 1 ENHANCED + OPTIMIZED)");
            Console.WriteLine("  Performance: 69.0% avg, 78.6% peak (only 3 numbers from perfect!)");
            Console.WriteLine("  Training: Bulk (163 series) + Iterative (8 validations) [OPTIMIZED]");
            Console.WriteLine("  Candidate Pool: 5000 (optimized)");
            Console.WriteLine();
            Console.WriteLine("For more information, see CLAUDE.md");
        }
    }
}

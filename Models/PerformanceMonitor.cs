using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text.Json;

namespace DataProcessor.Models
{
    public class PerformanceMonitor
    {
        private List<PerformancePredictionResult> results;
        private Dictionary<string, ModelMetrics> modelPerformance;
        private AutoTuningParameters currentParams;
        private Random random;

        public PerformanceMonitor()
        {
            results = new List<PerformancePredictionResult>();
            modelPerformance = new Dictionary<string, ModelMetrics>();
            currentParams = new AutoTuningParameters();
            random = new Random(42);
        }

        public void LogPrediction(string modelName, int seriesId, List<int> prediction,
                                 List<int> actual = null, double confidence = 0.0)
        {
            var result = new PerformancePredictionResult
            {
                ModelName = modelName,
                SeriesId = seriesId,
                Prediction = prediction,
                Actual = actual,
                Confidence = confidence,
                Timestamp = DateTime.UtcNow,
                Accuracy = actual != null ? CalculateAccuracy(prediction, actual) : 0.0
            };

            results.Add(result);

            // Update model metrics
            if (!modelPerformance.ContainsKey(modelName))
            {
                modelPerformance[modelName] = new ModelMetrics { ModelName = modelName };
            }

            var metrics = modelPerformance[modelName];
            metrics.TotalPredictions++;

            if (actual != null)
            {
                metrics.AccuracyHistory.Add(result.Accuracy);
                metrics.ConfidenceHistory.Add(confidence);
                metrics.UpdateStatistics();
            }

            Console.WriteLine($"📊 Logged prediction for {modelName}: Series {seriesId}, Accuracy: {result.Accuracy:F1}%");
        }

        private double CalculateAccuracy(List<int> prediction, List<int> actual)
        {
            if (prediction == null || actual == null || !actual.Any()) return 0.0;

            int matches = prediction.Intersect(actual).Count();
            return (double)matches / prediction.Count * 100.0;
        }

        public ModelComparison CompareModels()
        {
            Console.WriteLine("\n=== MODEL PERFORMANCE COMPARISON ===");

            var comparison = new ModelComparison();

            foreach (var model in modelPerformance.Values)
            {
                if (model.ValidPredictions > 0)
                {
                    Console.WriteLine($"\n{model.ModelName}:");
                    Console.WriteLine($"  Average Accuracy: {model.AverageAccuracy:F2}%");
                    Console.WriteLine($"  Best Accuracy: {model.BestAccuracy:F2}%");
                    Console.WriteLine($"  Consistency: {model.ConsistencyScore:F3}");
                    Console.WriteLine($"  Total Predictions: {model.TotalPredictions}");
                    Console.WriteLine($"  Valid Predictions: {model.ValidPredictions}");

                    comparison.ModelRankings.Add(new ModelRanking
                    {
                        ModelName = model.ModelName,
                        OverallScore = CalculateOverallScore(model),
                        AverageAccuracy = model.AverageAccuracy,
                        ConsistencyScore = model.ConsistencyScore
                    });
                }
            }

            comparison.ModelRankings = comparison.ModelRankings
                .OrderByDescending(r => r.OverallScore)
                .ToList();

            Console.WriteLine($"\n🏆 BEST PERFORMING MODEL: {comparison.ModelRankings.FirstOrDefault()?.ModelName ?? "None"}");

            return comparison;
        }

        private double CalculateOverallScore(ModelMetrics metrics)
        {
            // Weighted score combining accuracy, consistency, and reliability
            double accuracyWeight = 0.5;
            double consistencyWeight = 0.3;
            double reliabilityWeight = 0.2;

            double reliabilityScore = Math.Min(1.0, metrics.ValidPredictions / 10.0); // Scale with number of predictions

            return (metrics.AverageAccuracy / 100.0) * accuracyWeight +
                   metrics.ConsistencyScore * consistencyWeight +
                   reliabilityScore * reliabilityWeight;
        }

        public AutoTuningRecommendations GenerateAutoTuningRecommendations()
        {
            Console.WriteLine("\n=== AUTO-TUNING ANALYSIS ===");

            var recommendations = new AutoTuningRecommendations();

            // Analyze performance trends
            var recentResults = results.Where(r => r.Actual != null)
                                     .OrderByDescending(r => r.Timestamp)
                                     .Take(20)
                                     .ToList();

            if (recentResults.Count >= 5)
            {
                var recentAccuracy = recentResults.Average(r => r.Accuracy);
                var trend = CalculateAccuracyTrend(recentResults);

                Console.WriteLine($"Recent Average Accuracy: {recentAccuracy:F2}%");
                Console.WriteLine($"Accuracy Trend: {(trend > 0 ? "Improving" : trend < 0 ? "Declining" : "Stable")}");

                // Learning rate recommendations
                if (trend < -2.0) // Declining performance
                {
                    recommendations.LearningRateAdjustment = currentParams.LearningRate * 0.8;
                    recommendations.Reasoning.Add("Decreasing learning rate due to declining performance");
                }
                else if (trend > 2.0 && recentAccuracy < 70) // Improving but still low
                {
                    recommendations.LearningRateAdjustment = currentParams.LearningRate * 1.1;
                    recommendations.Reasoning.Add("Increasing learning rate to accelerate improvement");
                }

                // Architecture recommendations
                if (recentAccuracy < 60)
                {
                    recommendations.HiddenUnitsAdjustment = currentParams.HiddenUnits + 32;
                    recommendations.LayersAdjustment = Math.Min(5, currentParams.Layers + 1);
                    recommendations.Reasoning.Add("Increasing model complexity due to low accuracy");
                }
                else if (recentAccuracy > 80 && GetModelComplexity() > 0.8)
                {
                    recommendations.HiddenUnitsAdjustment = Math.Max(64, currentParams.HiddenUnits - 16);
                    recommendations.Reasoning.Add("Reducing complexity to prevent overfitting");
                }

                // Sequence length recommendations
                var consecutiveAccuracy = AnalyzeConsecutivePatterns(recentResults);
                if (consecutiveAccuracy > 0.3)
                {
                    recommendations.SequenceLengthAdjustment = Math.Min(15, currentParams.SequenceLength + 2);
                    recommendations.Reasoning.Add("Increasing sequence length due to strong temporal patterns");
                }

                // Ensemble recommendations
                var modelVariance = CalculateModelVariance();
                if (modelVariance > 0.2)
                {
                    recommendations.EnsembleCountAdjustment = Math.Min(10, currentParams.EnsembleCount + 2);
                    recommendations.Reasoning.Add("Increasing ensemble size due to high model variance");
                }
            }

            return recommendations;
        }

        private double CalculateAccuracyTrend(List<PerformancePredictionResult> results)
        {
            if (results.Count < 3) return 0;

            var accuracies = results.Select(r => r.Accuracy).ToList();
            var n = accuracies.Count;

            // Simple linear regression slope
            var sumX = 0.0;
            var sumY = accuracies.Sum();
            var sumXY = 0.0;
            var sumX2 = 0.0;

            for (int i = 0; i < n; i++)
            {
                sumX += i;
                sumXY += i * accuracies[i];
                sumX2 += i * i;
            }

            var slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
            return slope;
        }

        private double GetModelComplexity()
        {
            // Simplified complexity metric
            return (currentParams.HiddenUnits * currentParams.Layers) / 1000.0;
        }

        private double AnalyzeConsecutivePatterns(List<PerformancePredictionResult> results)
        {
            double consecutiveScore = 0;
            foreach (var result in results)
            {
                if (result.Actual != null)
                {
                    var consecutive = CountConsecutive(result.Actual);
                    consecutiveScore += consecutive / 14.0; // Normalize
                }
            }
            return consecutiveScore / results.Count;
        }

        private int CountConsecutive(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            int count = 0;
            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] == sorted[i - 1] + 1) count++;
            }
            return count;
        }

        private double CalculateModelVariance()
        {
            var accuracies = modelPerformance.Values
                .Where(m => m.ValidPredictions > 0)
                .Select(m => m.AverageAccuracy)
                .ToList();

            if (accuracies.Count < 2) return 0;

            var mean = accuracies.Average();
            var variance = accuracies.Sum(acc => Math.Pow(acc - mean, 2)) / accuracies.Count;
            return Math.Sqrt(variance) / 100.0; // Normalize
        }

        public void ApplyAutoTuning(AutoTuningRecommendations recommendations)
        {
            Console.WriteLine("\n=== APPLYING AUTO-TUNING RECOMMENDATIONS ===");

            bool applied = false;

            if (recommendations.LearningRateAdjustment.HasValue)
            {
                currentParams.LearningRate = recommendations.LearningRateAdjustment.Value;
                Console.WriteLine($"✅ Learning rate adjusted to: {currentParams.LearningRate:F6}");
                applied = true;
            }

            if (recommendations.HiddenUnitsAdjustment.HasValue)
            {
                currentParams.HiddenUnits = recommendations.HiddenUnitsAdjustment.Value;
                Console.WriteLine($"✅ Hidden units adjusted to: {currentParams.HiddenUnits}");
                applied = true;
            }

            if (recommendations.LayersAdjustment.HasValue)
            {
                currentParams.Layers = recommendations.LayersAdjustment.Value;
                Console.WriteLine($"✅ Layers adjusted to: {currentParams.Layers}");
                applied = true;
            }

            if (recommendations.SequenceLengthAdjustment.HasValue)
            {
                currentParams.SequenceLength = recommendations.SequenceLengthAdjustment.Value;
                Console.WriteLine($"✅ Sequence length adjusted to: {currentParams.SequenceLength}");
                applied = true;
            }

            if (recommendations.EnsembleCountAdjustment.HasValue)
            {
                currentParams.EnsembleCount = recommendations.EnsembleCountAdjustment.Value;
                Console.WriteLine($"✅ Ensemble count adjusted to: {currentParams.EnsembleCount}");
                applied = true;
            }

            if (!applied)
            {
                Console.WriteLine("ℹ️ No auto-tuning adjustments needed at this time");
            }

            Console.WriteLine("\nReasons for adjustments:");
            foreach (var reason in recommendations.Reasoning)
            {
                Console.WriteLine($"  • {reason}");
            }
        }

        public void SavePerformanceReport(string filePath = null)
        {
            filePath ??= $"Results/performance_report_{DateTime.Now:yyyyMMdd_HHmmss}.json";

            var report = new
            {
                generation_timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                total_predictions = results.Count,
                models_analyzed = modelPerformance.Count,
                model_performance = modelPerformance.Values.ToList(),
                recent_results = results.OrderByDescending(r => r.Timestamp).Take(50).ToList(),
                current_parameters = currentParams,
                summary = new
                {
                    best_model = modelPerformance.Values
                        .Where(m => m.ValidPredictions > 0)
                        .OrderByDescending(m => CalculateOverallScore(m))
                        .FirstOrDefault()?.ModelName ?? "None",
                    average_accuracy_all_models = modelPerformance.Values
                        .Where(m => m.ValidPredictions > 0)
                        .Average(m => m.AverageAccuracy),
                    most_consistent_model = modelPerformance.Values
                        .Where(m => m.ValidPredictions > 0)
                        .OrderByDescending(m => m.ConsistencyScore)
                        .FirstOrDefault()?.ModelName ?? "None"
                }
            };

            Directory.CreateDirectory("Results");
            var json = JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(filePath, json);

            Console.WriteLine($"📊 Performance report saved to: {filePath}");
        }

        public AutoTuningParameters GetCurrentParameters() => currentParams;
        public List<PerformancePredictionResult> GetResults() => results;
        public Dictionary<string, ModelMetrics> GetModelPerformance() => modelPerformance;
    }

    public class PerformancePredictionResult
    {
        public string ModelName { get; set; }
        public int SeriesId { get; set; }
        public List<int> Prediction { get; set; }
        public List<int> Actual { get; set; }
        public double Accuracy { get; set; }
        public double Confidence { get; set; }
        public DateTime Timestamp { get; set; }
    }

    public class ModelMetrics
    {
        public string ModelName { get; set; }
        public int TotalPredictions { get; set; }
        public int ValidPredictions => AccuracyHistory.Count;
        public List<double> AccuracyHistory { get; set; } = new();
        public List<double> ConfidenceHistory { get; set; } = new();
        public double AverageAccuracy { get; private set; }
        public double BestAccuracy { get; private set; }
        public double WorstAccuracy { get; private set; }
        public double ConsistencyScore { get; private set; } // Lower variance = higher consistency

        public void UpdateStatistics()
        {
            if (AccuracyHistory.Any())
            {
                AverageAccuracy = AccuracyHistory.Average();
                BestAccuracy = AccuracyHistory.Max();
                WorstAccuracy = AccuracyHistory.Min();

                // Calculate consistency (1 - normalized standard deviation)
                if (AccuracyHistory.Count > 1)
                {
                    var variance = AccuracyHistory.Sum(acc => Math.Pow(acc - AverageAccuracy, 2)) / AccuracyHistory.Count;
                    var stdDev = Math.Sqrt(variance);
                    ConsistencyScore = Math.Max(0, 1 - (stdDev / 100.0)); // Normalize to 0-1
                }
                else
                {
                    ConsistencyScore = 1.0;
                }
            }
        }
    }

    public class ModelComparison
    {
        public List<ModelRanking> ModelRankings { get; set; } = new();
        public DateTime ComparisonTimestamp { get; set; } = DateTime.UtcNow;
    }

    public class ModelRanking
    {
        public string ModelName { get; set; }
        public double OverallScore { get; set; }
        public double AverageAccuracy { get; set; }
        public double ConsistencyScore { get; set; }
    }

    public class AutoTuningParameters
    {
        public double LearningRate { get; set; } = 0.001;
        public int HiddenUnits { get; set; } = 128;
        public int Layers { get; set; } = 3;
        public int SequenceLength { get; set; } = 10;
        public int EnsembleCount { get; set; } = 5;
        public DateTime LastTuned { get; set; } = DateTime.UtcNow;
    }

    public class AutoTuningRecommendations
    {
        public double? LearningRateAdjustment { get; set; }
        public int? HiddenUnitsAdjustment { get; set; }
        public int? LayersAdjustment { get; set; }
        public int? SequenceLengthAdjustment { get; set; }
        public int? EnsembleCountAdjustment { get; set; }
        public List<string> Reasoning { get; set; } = new();
        public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;
    }
}
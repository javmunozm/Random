using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text.Json;
using DataProcessor.Models;
using DataProcessor.Connections;

namespace DataProcessor.Methods
{
    public class AdaptiveLearningEngine
    {
        private readonly DatabaseConnection dbConnection;
        private readonly PerformanceMonitor performanceMonitor;
        private readonly AdvancedLSTMModel advancedLSTM;
        private readonly TrueLearningModel trueLearningModel;

        private AdaptiveParameters adaptiveParams;
        private List<SeriesPattern> recentTrainingData;
        private Dictionary<string, double> modelWeights;
        private Random random;

        // Real-time learning components
        private double realtimeLearningRate;
        private int adaptationThreshold;
        private DateTime lastAdaptation;

        public AdaptiveLearningEngine()
        {
            dbConnection = new DatabaseConnection();
            performanceMonitor = new PerformanceMonitor();
            advancedLSTM = new AdvancedLSTMModel();
            trueLearningModel = new TrueLearningModel();

            adaptiveParams = new AdaptiveParameters();
            recentTrainingData = new List<SeriesPattern>();
            modelWeights = InitializeModelWeights();
            random = new Random(42);

            realtimeLearningRate = 0.1;
            adaptationThreshold = 5;
            lastAdaptation = DateTime.UtcNow;
        }

        private Dictionary<string, double> InitializeModelWeights()
        {
            return new Dictionary<string, double>
            {
                ["AdvancedLSTM"] = 0.3,
                ["TrueLearning"] = 0.25,
                ["StatisticalEnsemble"] = 0.2,
                ["SpatialTemporal"] = 0.15,
                ["FrequencyBased"] = 0.1
            };
        }

        public AdaptivePredictionResult PredictWithAdaptiveLearning(int targetSeriesId)
        {
            Console.WriteLine($"\n🧠 Adaptive Learning Prediction for Series {targetSeriesId}");
            Console.WriteLine("=" + new string('=', 50));

            // Load and prepare training data
            var historicalData = LoadAndPrepareTrainingData(targetSeriesId);

            // Check if adaptive learning is needed
            var needsAdaptation = ShouldPerformAdaptation(targetSeriesId);

            if (needsAdaptation)
            {
                Console.WriteLine("🔄 Performing adaptive model updates...");
                PerformAdaptiveUpdates(historicalData);
            }

            // Generate predictions from multiple adaptive models
            var predictions = GenerateAdaptivePredictions(targetSeriesId, historicalData);

            // Use adaptive ensemble weighting
            var finalPrediction = CombinePredictionsAdaptively(predictions);

            // Calculate confidence based on model agreement
            var confidence = CalculateAdaptiveConfidence(predictions, finalPrediction);

            // Log prediction for performance monitoring
            performanceMonitor.LogPrediction("AdaptiveLearning", targetSeriesId, finalPrediction.Numbers, null, confidence);

            // Save adaptive prediction
            var result = new AdaptivePredictionResult
            {
                SeriesId = targetSeriesId,
                Prediction = finalPrediction,
                Confidence = confidence,
                ModelWeights = new Dictionary<string, double>(modelWeights),
                AdaptationsPerformed = needsAdaptation,
                TrainingDataSize = historicalData.Count,
                AllPredictions = predictions
            };

            SaveAdaptivePrediction(result);

            return result;
        }

        private List<SeriesPattern> LoadAndPrepareTrainingData(int beforeSeriesId)
        {
            var rawData = dbConnection.LoadHistoricalDataBefore(beforeSeriesId);
            var patterns = new List<SeriesPattern>();

            foreach (var series in rawData)
            {
                var pattern = new SeriesPattern
                {
                    SeriesId = series.SeriesId,
                    Combinations = series.AllCombinations
                };

                // Calculate advanced features for adaptive learning
                CalculateAdaptiveFeatures(pattern);
                patterns.Add(pattern);
            }

            // Keep recent data for real-time adaptation
            recentTrainingData = patterns.TakeLast(50).ToList();

            Console.WriteLine($"📊 Loaded {patterns.Count} training patterns with adaptive features");
            return patterns;
        }

        private void CalculateAdaptiveFeatures(SeriesPattern pattern)
        {
            pattern.Features = new Dictionary<string, double>();

            if (pattern.Combinations.Count > 0)
            {
                var combo = pattern.Combinations[0];

                // Basic statistical features
                pattern.Features["mean"] = combo.Average();
                pattern.Features["sum"] = combo.Sum();
                pattern.Features["variance"] = CalculateVariance(combo);
                pattern.Features["std_dev"] = Math.Sqrt(pattern.Features["variance"]);

                // Advanced adaptive features
                pattern.Features["entropy"] = CalculateEntropy(combo);
                pattern.Features["skewness"] = CalculateSkewness(combo);
                pattern.Features["kurtosis"] = CalculateKurtosis(combo);
                pattern.Features["range_density"] = CalculateRangeDensity(combo);
                pattern.Features["consecutive_score"] = CountConsecutivePairs(combo) / 13.0;
                pattern.Features["gap_regularity"] = CalculateGapRegularity(combo);

                // Temporal features (based on series ID)
                pattern.Features["temporal_position"] = (pattern.SeriesId % 100) / 100.0;
                pattern.Features["cycle_position"] = (pattern.SeriesId % 7) / 7.0; // Weekly cycle

                // Distribution features
                pattern.Features["low_density"] = combo.Count(n => n <= 8) / 14.0;
                pattern.Features["mid_density"] = combo.Count(n => n >= 9 && n <= 17) / 14.0;
                pattern.Features["high_density"] = combo.Count(n => n >= 18) / 14.0;
            }
        }

        private bool ShouldPerformAdaptation(int seriesId)
        {
            // Check time since last adaptation
            var timeSinceAdaptation = DateTime.UtcNow - lastAdaptation;
            if (timeSinceAdaptation.TotalMinutes < 30) return false;

            // Check recent performance
            var recentResults = performanceMonitor.GetResults()
                .Where(r => r.Actual != null)
                .OrderByDescending(r => r.Timestamp)
                .Take(adaptationThreshold)
                .ToList();

            if (recentResults.Count < adaptationThreshold) return true; // Not enough data, adapt

            var recentAccuracy = recentResults.Average(r => r.Accuracy);
            var expectedAccuracy = adaptiveParams.TargetAccuracy;

            // Adapt if performance is below target or declining
            var isPerformingPoorly = recentAccuracy < expectedAccuracy - 5.0;
            var isDeclining = CalculateAccuracyTrend(recentResults) < -1.0;

            return isPerformingPoorly || isDeclining;
        }

        private void PerformAdaptiveUpdates(List<SeriesPattern> historicalData)
        {
            Console.WriteLine("🔄 Performing adaptive model updates...");

            // Update model weights based on recent performance
            UpdateModelWeightsAdaptively();

            // Retrain advanced LSTM with recent data
            if (historicalData.Count >= 20)
            {
                Console.WriteLine("🧠 Retraining Advanced LSTM with recent patterns...");
                var recentPatterns = historicalData.TakeLast(50).ToList();
                advancedLSTM.PrepareAdvancedTrainingData(recentPatterns);
                advancedLSTM.TrainAdvancedModel(epochs: 30, validationSplit: 0.3);
            }

            // Update TrueLearning model with latest patterns
            foreach (var pattern in historicalData.TakeLast(10))
            {
                trueLearningModel.LearnFromSeries(pattern);
            }

            // Update adaptive parameters based on performance analysis
            UpdateAdaptiveParameters();

            lastAdaptation = DateTime.UtcNow;
            Console.WriteLine("✅ Adaptive updates completed");
        }

        private void UpdateModelWeightsAdaptively()
        {
            var modelPerformance = performanceMonitor.GetModelPerformance();
            var totalWeight = 0.0;

            // Calculate new weights based on recent performance
            var newWeights = new Dictionary<string, double>();

            foreach (var modelName in modelWeights.Keys.ToList())
            {
                if (modelPerformance.ContainsKey(modelName) && modelPerformance[modelName].ValidPredictions > 0)
                {
                    var metrics = modelPerformance[modelName];
                    var performanceScore = metrics.AverageAccuracy / 100.0;
                    var consistencyScore = metrics.ConsistencyScore;

                    // Combine performance and consistency
                    var adaptiveScore = (performanceScore * 0.7) + (consistencyScore * 0.3);
                    newWeights[modelName] = Math.Max(0.05, adaptiveScore); // Minimum weight
                    totalWeight += newWeights[modelName];
                }
                else
                {
                    newWeights[modelName] = modelWeights[modelName] * 0.9; // Slightly reduce unused models
                    totalWeight += newWeights[modelName];
                }
            }

            // Normalize weights
            if (totalWeight > 0)
            {
                foreach (var key in newWeights.Keys.ToList())
                {
                    modelWeights[key] = newWeights[key] / totalWeight;
                }

                Console.WriteLine("📊 Updated model weights:");
                foreach (var weight in modelWeights)
                {
                    Console.WriteLine($"  {weight.Key}: {weight.Value:F3}");
                }
            }
        }

        private void UpdateAdaptiveParameters()
        {
            var recommendations = performanceMonitor.GenerateAutoTuningRecommendations();

            // Apply recommendations to adaptive parameters
            if (recommendations.LearningRateAdjustment.HasValue)
            {
                realtimeLearningRate = recommendations.LearningRateAdjustment.Value;
            }

            // Update target accuracy based on recent performance
            var recentResults = performanceMonitor.GetResults()
                .Where(r => r.Actual != null)
                .OrderByDescending(r => r.Timestamp)
                .Take(10)
                .ToList();

            if (recentResults.Any())
            {
                var recentAccuracy = recentResults.Average(r => r.Accuracy);
                adaptiveParams.TargetAccuracy = Math.Max(60, Math.Min(85, recentAccuracy + 2)); // Gradual improvement
            }
        }

        private List<WeightedPrediction> GenerateAdaptivePredictions(int targetSeriesId, List<SeriesPattern> historicalData)
        {
            var predictions = new List<WeightedPrediction>();

            // Advanced LSTM prediction
            if (modelWeights["AdvancedLSTM"] > 0.1)
            {
                try
                {
                    var lstmPrediction = advancedLSTM.PredictAdvanced(historicalData);
                    predictions.Add(new WeightedPrediction
                    {
                        ModelName = "AdvancedLSTM",
                        Numbers = lstmPrediction,
                        Weight = modelWeights["AdvancedLSTM"],
                        Confidence = 0.8
                    });
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Advanced LSTM prediction failed: {ex.Message}");
                }
            }

            // TrueLearning prediction
            if (modelWeights["TrueLearning"] > 0.1)
            {
                var truePrediction = trueLearningModel.PredictBestCombination(targetSeriesId);
                predictions.Add(new WeightedPrediction
                {
                    ModelName = "TrueLearning",
                    Numbers = truePrediction,
                    Weight = modelWeights["TrueLearning"],
                    Confidence = 0.75
                });
            }

            // Statistical ensemble prediction
            if (modelWeights["StatisticalEnsemble"] > 0.1)
            {
                var statisticalPrediction = GenerateStatisticalEnsemblePrediction(historicalData);
                predictions.Add(new WeightedPrediction
                {
                    ModelName = "StatisticalEnsemble",
                    Numbers = statisticalPrediction,
                    Weight = modelWeights["StatisticalEnsemble"],
                    Confidence = 0.7
                });
            }

            // Frequency-based prediction
            if (modelWeights["FrequencyBased"] > 0.1)
            {
                var frequencyPrediction = GenerateAdaptiveFrequencyPrediction(historicalData);
                predictions.Add(new WeightedPrediction
                {
                    ModelName = "FrequencyBased",
                    Numbers = frequencyPrediction,
                    Weight = modelWeights["FrequencyBased"],
                    Confidence = 0.6
                });
            }

            Console.WriteLine($"📊 Generated {predictions.Count} adaptive predictions");
            return predictions;
        }

        private List<int> GenerateStatisticalEnsemblePrediction(List<SeriesPattern> historicalData)
        {
            // Generate multiple statistical predictions and combine
            var predictions = new List<List<int>>();

            // Mean-based prediction
            var meanTarget = historicalData.TakeLast(20).Average(p => p.Features.GetValueOrDefault("mean", 13));
            predictions.Add(GenerateTargetMeanPrediction(meanTarget));

            // Variance-based prediction
            var varianceTarget = historicalData.TakeLast(20).Average(p => p.Features.GetValueOrDefault("variance", 50));
            predictions.Add(GenerateTargetVariancePrediction(varianceTarget));

            // Entropy-based prediction
            var entropyTarget = historicalData.TakeLast(20).Average(p => p.Features.GetValueOrDefault("entropy", 2.2));
            predictions.Add(GenerateTargetEntropyPrediction(entropyTarget));

            // Combine using voting
            return CombineByVoting(predictions);
        }

        private List<int> GenerateAdaptiveFrequencyPrediction(List<SeriesPattern> historicalData)
        {
            // Calculate adaptive frequency weights
            var frequencies = new Dictionary<int, double>();
            for (int i = 1; i <= 25; i++) frequencies[i] = 0;

            // Weight recent data more heavily
            for (int i = 0; i < historicalData.Count; i++)
            {
                var pattern = historicalData[i];
                var weight = Math.Pow(0.95, historicalData.Count - i - 1); // Exponential decay

                foreach (var combo in pattern.Combinations)
                {
                    foreach (var num in combo)
                    {
                        frequencies[num] += weight;
                    }
                }
            }

            // Select top numbers with some randomization
            var candidates = frequencies
                .OrderByDescending(kvp => kvp.Value)
                .Take(18)
                .Select(kvp => kvp.Key)
                .ToList();

            var prediction = new List<int>();
            while (prediction.Count < 14 && candidates.Any())
            {
                var index = Math.Min(candidates.Count - 1, (int)(Math.Pow(random.NextDouble(), 2) * candidates.Count));
                prediction.Add(candidates[index]);
                candidates.RemoveAt(index);
            }

            return prediction.OrderBy(x => x).ToList();
        }

        private WeightedPrediction CombinePredictionsAdaptively(List<WeightedPrediction> predictions)
        {
            if (!predictions.Any()) return new WeightedPrediction { Numbers = GenerateRandomCombination() };

            // Use weighted voting with adaptive confidence
            var numberVotes = new Dictionary<int, double>();
            for (int i = 1; i <= 25; i++) numberVotes[i] = 0;

            foreach (var prediction in predictions)
            {
                var weight = prediction.Weight * prediction.Confidence;
                foreach (var number in prediction.Numbers)
                {
                    numberVotes[number] += weight;
                }
            }

            // Select top 14 numbers
            var finalNumbers = numberVotes
                .OrderByDescending(kvp => kvp.Value)
                .Take(14)
                .Select(kvp => kvp.Key)
                .OrderBy(x => x)
                .ToList();

            // Calculate overall confidence
            var totalWeight = predictions.Sum(p => p.Weight);
            var avgConfidence = predictions.Sum(p => p.Confidence * p.Weight) / totalWeight;

            return new WeightedPrediction
            {
                ModelName = "AdaptiveEnsemble",
                Numbers = finalNumbers,
                Weight = 1.0,
                Confidence = avgConfidence
            };
        }

        private double CalculateAdaptiveConfidence(List<WeightedPrediction> predictions, WeightedPrediction finalPrediction)
        {
            if (!predictions.Any()) return 0.5;

            // Calculate agreement between predictions
            double totalAgreement = 0;
            int comparisons = 0;

            foreach (var pred1 in predictions)
            {
                foreach (var pred2 in predictions)
                {
                    if (pred1.ModelName != pred2.ModelName)
                    {
                        var overlap = pred1.Numbers.Intersect(pred2.Numbers).Count();
                        totalAgreement += overlap / 14.0;
                        comparisons++;
                    }
                }
            }

            var agreementScore = comparisons > 0 ? totalAgreement / comparisons : 0.5;

            // Combine with individual confidences
            var avgIndividualConfidence = predictions.Average(p => p.Confidence);

            return (agreementScore * 0.6) + (avgIndividualConfidence * 0.4);
        }

        // Helper methods for statistical predictions
        private List<int> GenerateTargetMeanPrediction(double targetMean)
        {
            var numbers = new List<int>();
            var currentSum = 0.0;
            var available = Enumerable.Range(1, 25).ToList();

            while (numbers.Count < 14 && available.Any())
            {
                var remaining = 14 - numbers.Count;
                var neededSum = (targetMean * 14) - currentSum;
                var avgNeeded = neededSum / remaining;

                var closest = available
                    .OrderBy(n => Math.Abs(n - avgNeeded))
                    .First();

                numbers.Add(closest);
                currentSum += closest;
                available.Remove(closest);
            }

            return numbers.OrderBy(x => x).ToList();
        }

        private List<int> GenerateTargetVariancePrediction(double targetVariance)
        {
            var attempts = 0;
            while (attempts < 100)
            {
                var candidate = Enumerable.Range(1, 25)
                    .OrderBy(x => random.Next())
                    .Take(14)
                    .OrderBy(x => x)
                    .ToList();

                var variance = CalculateVariance(candidate);
                if (Math.Abs(variance - targetVariance) < 10)
                {
                    return candidate;
                }
                attempts++;
            }

            return GenerateRandomCombination();
        }

        private List<int> GenerateTargetEntropyPrediction(double targetEntropy)
        {
            var attempts = 0;
            while (attempts < 100)
            {
                var candidate = Enumerable.Range(1, 25)
                    .OrderBy(x => random.Next())
                    .Take(14)
                    .OrderBy(x => x)
                    .ToList();

                var entropy = CalculateEntropy(candidate);
                if (Math.Abs(entropy - targetEntropy) < 0.3)
                {
                    return candidate;
                }
                attempts++;
            }

            return GenerateRandomCombination();
        }

        private List<int> CombineByVoting(List<List<int>> predictions)
        {
            var votes = new Dictionary<int, int>();
            for (int i = 1; i <= 25; i++) votes[i] = 0;

            foreach (var prediction in predictions)
            {
                foreach (var number in prediction)
                {
                    votes[number]++;
                }
            }

            return votes
                .OrderByDescending(kvp => kvp.Value)
                .ThenBy(kvp => random.Next())
                .Take(14)
                .Select(kvp => kvp.Key)
                .OrderBy(x => x)
                .ToList();
        }

        private List<int> GenerateRandomCombination()
        {
            return Enumerable.Range(1, 25)
                .OrderBy(x => random.Next())
                .Take(14)
                .OrderBy(x => x)
                .ToList();
        }

        // Statistical calculation helpers
        private double CalculateVariance(List<int> numbers)
        {
            var mean = numbers.Average();
            return numbers.Sum(n => Math.Pow(n - mean, 2)) / numbers.Count;
        }

        private double CalculateEntropy(List<int> numbers)
        {
            var ranges = new int[5];
            foreach (var num in numbers)
            {
                ranges[(num - 1) / 5]++;
            }

            double entropy = 0;
            foreach (var count in ranges)
            {
                if (count > 0)
                {
                    double p = (double)count / numbers.Count;
                    entropy -= p * Math.Log2(p);
                }
            }
            return entropy;
        }

        private double CalculateSkewness(List<int> numbers)
        {
            var mean = numbers.Average();
            var variance = CalculateVariance(numbers);
            var stdDev = Math.Sqrt(variance);

            if (stdDev == 0) return 0;

            return numbers.Sum(n => Math.Pow((n - mean) / stdDev, 3)) / numbers.Count;
        }

        private double CalculateKurtosis(List<int> numbers)
        {
            var mean = numbers.Average();
            var variance = CalculateVariance(numbers);
            var stdDev = Math.Sqrt(variance);

            if (stdDev == 0) return 0;

            return numbers.Sum(n => Math.Pow((n - mean) / stdDev, 4)) / numbers.Count - 3;
        }

        private double CalculateRangeDensity(List<int> numbers)
        {
            var range = numbers.Max() - numbers.Min();
            return range == 0 ? 0 : numbers.Count / (double)range;
        }

        private int CountConsecutivePairs(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            int count = 0;
            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] == sorted[i - 1] + 1) count++;
            }
            return count;
        }

        private double CalculateGapRegularity(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var gaps = new List<int>();
            for (int i = 1; i < sorted.Count; i++)
            {
                gaps.Add(sorted[i] - sorted[i - 1]);
            }

            if (!gaps.Any()) return 0;

            var avgGap = gaps.Average();
            var gapVariance = gaps.Sum(g => Math.Pow(g - avgGap, 2)) / gaps.Count;
            return 1.0 / (1.0 + Math.Sqrt(gapVariance)); // Higher = more regular
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

        private void SaveAdaptivePrediction(AdaptivePredictionResult result)
        {
            var fileName = $"Results/adaptive_prediction_{result.SeriesId}.json";
            Directory.CreateDirectory("Results");

            var json = JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(fileName, json);

            Console.WriteLine($"💾 Adaptive prediction saved to: {fileName}");
        }

        public void ValidateAndLearnFromActual(int seriesId, List<List<int>> actualResults)
        {
            Console.WriteLine($"\n🎯 Learning from actual results for series {seriesId}");

            // Get our prediction
            var predictionFile = $"Results/adaptive_prediction_{seriesId}.json";
            if (File.Exists(predictionFile))
            {
                try
                {
                    var predictionJson = File.ReadAllText(predictionFile);
                    var savedResult = JsonSerializer.Deserialize<AdaptivePredictionResult>(predictionJson);

                    if (savedResult?.Prediction?.Numbers != null)
                    {
                        var bestActual = actualResults.OrderByDescending(actual =>
                            savedResult.Prediction.Numbers.Intersect(actual).Count()).First();

                        var accuracy = (double)savedResult.Prediction.Numbers.Intersect(bestActual).Count() / 14.0 * 100.0;

                        // Log the result
                        performanceMonitor.LogPrediction("AdaptiveLearning", seriesId,
                            savedResult.Prediction.Numbers, bestActual, savedResult.Confidence);

                        // Update models with actual results
                        var actualPattern = new SeriesPattern
                        {
                            SeriesId = seriesId,
                            Combinations = actualResults
                        };

                        trueLearningModel.LearnFromSeries(actualPattern);

                        Console.WriteLine($"✅ Learned from series {seriesId}: {accuracy:F1}% accuracy");

                        // Trigger adaptation if performance is poor
                        if (accuracy < 50)
                        {
                            Console.WriteLine("🔄 Poor performance detected, triggering immediate adaptation");
                            var historicalData = LoadAndPrepareTrainingData(seriesId + 1);
                            PerformAdaptiveUpdates(historicalData);
                        }
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ Error processing actual results: {ex.Message}");
                }
            }
        }

        public PerformanceMonitor GetPerformanceMonitor() => performanceMonitor;
        public Dictionary<string, double> GetCurrentModelWeights() => new(modelWeights);
        public AdaptiveParameters GetAdaptiveParameters() => adaptiveParams;
    }

    public class AdaptivePredictionResult
    {
        public int SeriesId { get; set; }
        public WeightedPrediction Prediction { get; set; }
        public double Confidence { get; set; }
        public Dictionary<string, double> ModelWeights { get; set; }
        public bool AdaptationsPerformed { get; set; }
        public int TrainingDataSize { get; set; }
        public List<WeightedPrediction> AllPredictions { get; set; }
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    public class WeightedPrediction
    {
        public string ModelName { get; set; }
        public List<int> Numbers { get; set; }
        public double Weight { get; set; }
        public double Confidence { get; set; }
    }

    public class AdaptiveParameters
    {
        public double TargetAccuracy { get; set; } = 72.0;
        public double LearningDecayRate { get; set; } = 0.95;
        public int AdaptationFrequency { get; set; } = 5; // Every 5 predictions
        public double MinModelWeight { get; set; } = 0.05;
        public double ConfidenceThreshold { get; set; } = 0.6;
        public DateTime LastUpdate { get; set; } = DateTime.UtcNow;
    }
}
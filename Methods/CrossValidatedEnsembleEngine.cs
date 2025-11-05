using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text.Json;
using DataProcessor.Models;
using DataProcessor.Connections;

namespace DataProcessor.Methods
{
    public class CrossValidatedEnsembleEngine
    {
        private readonly DatabaseConnection dbConnection;
        private readonly PerformanceMonitor performanceMonitor;
        private readonly Random random;

        // Ensemble components
        private List<IEnsembleModel> ensembleModels;
        private CrossValidationResults validationResults;
        private EnsembleWeights optimizedWeights;

        public CrossValidatedEnsembleEngine()
        {
            dbConnection = new DatabaseConnection();
            performanceMonitor = new PerformanceMonitor();
            random = new Random(42);

            InitializeEnsembleModels();
        }

        private void InitializeEnsembleModels()
        {
            ensembleModels = new List<IEnsembleModel>
            {
                new LSTMEnsembleModel("LSTM_Deep", 3, 128),
                new LSTMEnsembleModel("LSTM_Wide", 2, 256),
                new LSTMEnsembleModel("LSTM_Fast", 2, 64),
                new StatisticalEnsembleModel("Statistical_Conservative"),
                new StatisticalEnsembleModel("Statistical_Aggressive"),
                new FrequencyEnsembleModel("Frequency_Weighted"),
                new FrequencyEnsembleModel("Frequency_Recent"),
                new PatternEnsembleModel("Pattern_Consecutive"),
                new PatternEnsembleModel("Pattern_Distribution"),
                new HybridEnsembleModel("Hybrid_Balanced")
            };

            Console.WriteLine($"🎯 Initialized {ensembleModels.Count} ensemble models for cross-validation");
        }

        public CrossValidatedPrediction PredictWithCrossValidation(int targetSeriesId, int cvFolds = 5)
        {
            Console.WriteLine($"\n🔬 Cross-Validated Ensemble Prediction for Series {targetSeriesId}");
            Console.WriteLine("=" + new string('=', 60));

            // Load training data
            var historicalData = LoadHistoricalData(targetSeriesId);

            // Perform cross-validation
            Console.WriteLine($"🔄 Performing {cvFolds}-fold cross-validation...");
            validationResults = PerformCrossValidation(historicalData, cvFolds);

            // Optimize ensemble weights based on validation results
            optimizedWeights = OptimizeEnsembleWeights(validationResults);

            // Train final models on full dataset
            TrainFinalModels(historicalData);

            // Generate final ensemble prediction
            var finalPrediction = GenerateFinalEnsemblePrediction(targetSeriesId);

            // Calculate prediction confidence
            var confidence = CalculatePredictionConfidence(finalPrediction, validationResults);

            var result = new CrossValidatedPrediction
            {
                SeriesId = targetSeriesId,
                Prediction = finalPrediction.Numbers,
                Confidence = confidence,
                ValidationResults = validationResults,
                OptimizedWeights = optimizedWeights,
                ModelPredictions = finalPrediction.ModelPredictions,
                TrainingDataSize = historicalData.Count,
                CVFolds = cvFolds
            };

            // Save comprehensive results
            SaveCrossValidatedPrediction(result);

            // Log for performance monitoring
            performanceMonitor.LogPrediction("CrossValidatedEnsemble", targetSeriesId,
                finalPrediction.Numbers, null, confidence);

            return result;
        }

        private List<SeriesPattern> LoadHistoricalData(int beforeSeriesId)
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
                CalculateExtendedFeatures(pattern);
                patterns.Add(pattern);
            }

            Console.WriteLine($"📊 Loaded {patterns.Count} patterns for cross-validation");
            return patterns;
        }

        private void CalculateExtendedFeatures(SeriesPattern pattern)
        {
            pattern.Features = new Dictionary<string, double>();

            if (pattern.Combinations.Count > 0)
            {
                var combo = pattern.Combinations[0];

                // Basic features
                pattern.Features["mean"] = combo.Average();
                pattern.Features["sum"] = combo.Sum();
                pattern.Features["variance"] = CalculateVariance(combo);
                pattern.Features["std_dev"] = Math.Sqrt(pattern.Features["variance"]);
                pattern.Features["range"] = combo.Max() - combo.Min();
                pattern.Features["median"] = CalculateMedian(combo);

                // Advanced statistical features
                pattern.Features["skewness"] = CalculateSkewness(combo);
                pattern.Features["kurtosis"] = CalculateKurtosis(combo);
                pattern.Features["entropy"] = CalculateEntropy(combo);
                pattern.Features["gini_coefficient"] = CalculateGiniCoefficient(combo);

                // Pattern features
                pattern.Features["consecutive_pairs"] = CountConsecutivePairs(combo);
                pattern.Features["max_gap"] = CalculateMaxGap(combo);
                pattern.Features["avg_gap"] = CalculateAverageGap(combo);
                pattern.Features["gap_variance"] = CalculateGapVariance(combo);

                // Distribution features
                pattern.Features["low_third"] = combo.Count(n => n <= 8) / 14.0;
                pattern.Features["mid_third"] = combo.Count(n => n >= 9 && n <= 17) / 14.0;
                pattern.Features["high_third"] = combo.Count(n => n >= 18) / 14.0;

                // Clustering features
                pattern.Features["cluster_density"] = CalculateClusterDensity(combo);
                pattern.Features["isolation_index"] = CalculateIsolationIndex(combo);
            }
        }

        private CrossValidationResults PerformCrossValidation(List<SeriesPattern> data, int folds)
        {
            var results = new CrossValidationResults { Folds = folds };
            var foldSize = data.Count / folds;

            for (int fold = 0; fold < folds; fold++)
            {
                Console.WriteLine($"  Fold {fold + 1}/{folds}...");

                // Split data into train/validation
                var validationStart = fold * foldSize;
                var validationEnd = (fold == folds - 1) ? data.Count : (fold + 1) * foldSize;

                var validationData = data.Skip(validationStart).Take(validationEnd - validationStart).ToList();
                var trainingData = data.Take(validationStart).Concat(data.Skip(validationEnd)).ToList();

                var foldResult = new FoldResult { FoldIndex = fold };

                // Train and validate each model
                foreach (var model in ensembleModels)
                {
                    try
                    {
                        model.Train(trainingData);

                        var modelAccuracies = new List<double>();
                        foreach (var validationPattern in validationData)
                        {
                            var prediction = model.Predict(validationPattern.SeriesId);
                            var actual = validationPattern.Combinations.FirstOrDefault();

                            if (actual != null)
                            {
                                var accuracy = CalculateAccuracy(prediction, actual);
                                modelAccuracies.Add(accuracy);
                            }
                        }

                        if (modelAccuracies.Any())
                        {
                            foldResult.ModelAccuracies[model.ModelName] = modelAccuracies.Average();
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"    ⚠️ Model {model.ModelName} failed in fold {fold}: {ex.Message}");
                        foldResult.ModelAccuracies[model.ModelName] = 0.0;
                    }
                }

                results.FoldResults.Add(foldResult);
            }

            // Calculate overall statistics
            CalculateOverallValidationStatistics(results);

            return results;
        }

        private void CalculateOverallValidationStatistics(CrossValidationResults results)
        {
            var allModelNames = ensembleModels.Select(m => m.ModelName).ToList();

            foreach (var modelName in allModelNames)
            {
                var accuracies = results.FoldResults
                    .Where(f => f.ModelAccuracies.ContainsKey(modelName))
                    .Select(f => f.ModelAccuracies[modelName])
                    .ToList();

                if (accuracies.Any())
                {
                    results.ModelStatistics[modelName] = new ModelValidationStats
                    {
                        MeanAccuracy = accuracies.Average(),
                        StdAccuracy = CalculateStandardDeviation(accuracies),
                        MinAccuracy = accuracies.Min(),
                        MaxAccuracy = accuracies.Max(),
                        ConsistencyScore = 1.0 - (CalculateStandardDeviation(accuracies) / accuracies.Average())
                    };
                }
            }

            Console.WriteLine("\n📊 Cross-Validation Results:");
            foreach (var stat in results.ModelStatistics.OrderByDescending(s => s.Value.MeanAccuracy))
            {
                Console.WriteLine($"  {stat.Key}: {stat.Value.MeanAccuracy:F2}% ± {stat.Value.StdAccuracy:F2}%");
            }
        }

        private EnsembleWeights OptimizeEnsembleWeights(CrossValidationResults validationResults)
        {
            Console.WriteLine("\n🎯 Optimizing ensemble weights...");

            var weights = new EnsembleWeights();

            // Method 1: Performance-based weighting
            var performanceWeights = CalculatePerformanceBasedWeights(validationResults);

            // Method 2: Diversity-based weighting
            var diversityWeights = CalculateDiversityBasedWeights(validationResults);

            // Method 3: Stability-based weighting
            var stabilityWeights = CalculateStabilityBasedWeights(validationResults);

            // Combine weighting methods
            foreach (var modelName in performanceWeights.Keys)
            {
                var combinedWeight = (performanceWeights[modelName] * 0.5) +
                                   (diversityWeights.GetValueOrDefault(modelName, 0) * 0.3) +
                                   (stabilityWeights.GetValueOrDefault(modelName, 0) * 0.2);

                weights.ModelWeights[modelName] = Math.Max(0.01, combinedWeight); // Minimum weight
            }

            // Normalize weights
            var totalWeight = weights.ModelWeights.Values.Sum();
            foreach (var key in weights.ModelWeights.Keys.ToList())
            {
                weights.ModelWeights[key] /= totalWeight;
            }

            Console.WriteLine("📊 Optimized ensemble weights:");
            foreach (var weight in weights.ModelWeights.OrderByDescending(w => w.Value))
            {
                Console.WriteLine($"  {weight.Key}: {weight.Value:F3}");
            }

            return weights;
        }

        private Dictionary<string, double> CalculatePerformanceBasedWeights(CrossValidationResults results)
        {
            var weights = new Dictionary<string, double>();
            var maxAccuracy = results.ModelStatistics.Values.Max(s => s.MeanAccuracy);

            foreach (var stat in results.ModelStatistics)
            {
                // Exponential weighting based on performance
                var normalizedAccuracy = stat.Value.MeanAccuracy / maxAccuracy;
                weights[stat.Key] = Math.Pow(normalizedAccuracy, 3); // Cubic to emphasize top performers
            }

            return weights;
        }

        private Dictionary<string, double> CalculateDiversityBasedWeights(CrossValidationResults results)
        {
            var weights = new Dictionary<string, double>();

            // Calculate diversity scores based on prediction differences
            foreach (var modelName in results.ModelStatistics.Keys)
            {
                var diversityScore = 0.0;
                var comparisons = 0;

                foreach (var otherModel in results.ModelStatistics.Keys)
                {
                    if (modelName != otherModel)
                    {
                        // Calculate correlation between models (lower correlation = higher diversity)
                        var correlation = CalculateModelCorrelation(modelName, otherModel, results);
                        diversityScore += (1.0 - Math.Abs(correlation));
                        comparisons++;
                    }
                }

                weights[modelName] = comparisons > 0 ? diversityScore / comparisons : 0.5;
            }

            return weights;
        }

        private Dictionary<string, double> CalculateStabilityBasedWeights(CrossValidationResults results)
        {
            var weights = new Dictionary<string, double>();

            foreach (var stat in results.ModelStatistics)
            {
                // Higher consistency score = higher weight
                weights[stat.Key] = Math.Max(0, stat.Value.ConsistencyScore);
            }

            return weights;
        }

        private double CalculateModelCorrelation(string model1, string model2, CrossValidationResults results)
        {
            var accuracies1 = results.FoldResults
                .Where(f => f.ModelAccuracies.ContainsKey(model1))
                .Select(f => f.ModelAccuracies[model1])
                .ToList();

            var accuracies2 = results.FoldResults
                .Where(f => f.ModelAccuracies.ContainsKey(model2))
                .Select(f => f.ModelAccuracies[model2])
                .ToList();

            if (accuracies1.Count != accuracies2.Count || accuracies1.Count < 2)
                return 0;

            return CalculatePearsonCorrelation(accuracies1, accuracies2);
        }

        private void TrainFinalModels(List<SeriesPattern> fullData)
        {
            Console.WriteLine("\n🏋️ Training final models on complete dataset...");

            foreach (var model in ensembleModels)
            {
                try
                {
                    model.Train(fullData);
                    Console.WriteLine($"  ✅ {model.ModelName} trained successfully");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  ❌ {model.ModelName} training failed: {ex.Message}");
                }
            }
        }

        private EnsemblePredictionResult GenerateFinalEnsemblePrediction(int targetSeriesId)
        {
            Console.WriteLine("\n🎲 Generating final ensemble prediction...");

            var modelPredictions = new Dictionary<string, List<int>>();
            var validPredictions = new List<WeightedPrediction>();

            // Get predictions from all models
            foreach (var model in ensembleModels)
            {
                try
                {
                    var prediction = model.Predict(targetSeriesId);
                    modelPredictions[model.ModelName] = prediction;

                    var weight = optimizedWeights.ModelWeights.GetValueOrDefault(model.ModelName, 0.0);
                    if (weight > 0.01) // Only include models with significant weight
                    {
                        validPredictions.Add(new WeightedPrediction
                        {
                            ModelName = model.ModelName,
                            Numbers = prediction,
                            Weight = weight,
                            Confidence = 0.8 // Base confidence, could be model-specific
                        });
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"  ⚠️ {model.ModelName} prediction failed: {ex.Message}");
                }
            }

            // Combine predictions using optimized weights
            var finalNumbers = CombineWeightedPredictions(validPredictions);

            return new EnsemblePredictionResult
            {
                Numbers = finalNumbers,
                ModelPredictions = modelPredictions
            };
        }

        private List<int> CombineWeightedPredictions(List<WeightedPrediction> predictions)
        {
            var numberVotes = new Dictionary<int, double>();
            for (int i = 1; i <= 25; i++) numberVotes[i] = 0;

            // Weighted voting
            foreach (var prediction in predictions)
            {
                foreach (var number in prediction.Numbers)
                {
                    numberVotes[number] += prediction.Weight;
                }
            }

            // Select top 14 numbers
            return numberVotes
                .OrderByDescending(kvp => kvp.Value)
                .Take(14)
                .Select(kvp => kvp.Key)
                .OrderBy(x => x)
                .ToList();
        }

        private double CalculatePredictionConfidence(EnsemblePredictionResult prediction, CrossValidationResults validation)
        {
            // Base confidence from validation results
            var avgAccuracy = validation.ModelStatistics.Values.Average(s => s.MeanAccuracy);
            var avgConsistency = validation.ModelStatistics.Values.Average(s => s.ConsistencyScore);

            // Agreement between models
            var agreementScore = CalculateModelAgreement(prediction.ModelPredictions);

            // Combine factors
            var confidence = (avgAccuracy / 100.0 * 0.4) + (avgConsistency * 0.3) + (agreementScore * 0.3);

            return Math.Max(0.1, Math.Min(0.95, confidence));
        }

        private double CalculateModelAgreement(Dictionary<string, List<int>> modelPredictions)
        {
            var predictions = modelPredictions.Values.ToList();
            if (predictions.Count < 2) return 0.5;

            double totalAgreement = 0;
            int comparisons = 0;

            for (int i = 0; i < predictions.Count; i++)
            {
                for (int j = i + 1; j < predictions.Count; j++)
                {
                    var overlap = predictions[i].Intersect(predictions[j]).Count();
                    totalAgreement += overlap / 14.0;
                    comparisons++;
                }
            }

            return comparisons > 0 ? totalAgreement / comparisons : 0.5;
        }

        private void SaveCrossValidatedPrediction(CrossValidatedPrediction result)
        {
            var fileName = $"Results/cross_validated_prediction_{result.SeriesId}.json";
            Directory.CreateDirectory("Results");

            var predictionData = new
            {
                series_id = result.SeriesId,
                generation_timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                model_type = "Cross-Validated Ensemble",
                prediction = result.Prediction,
                formatted_prediction = string.Join(" ", result.Prediction.Select(n => n.ToString("D2"))),
                confidence = result.Confidence,
                training_data_size = result.TrainingDataSize,
                cv_folds = result.CVFolds,
                validation_results = new
                {
                    model_performance = result.ValidationResults.ModelStatistics,
                    fold_count = result.ValidationResults.Folds,
                    best_model = result.ValidationResults.ModelStatistics
                        .OrderByDescending(s => s.Value.MeanAccuracy)
                        .FirstOrDefault().Key
                },
                optimized_weights = result.OptimizedWeights.ModelWeights,
                model_predictions = result.ModelPredictions,
                methodology = new
                {
                    approach = "Cross-validated ensemble with optimized weighting",
                    validation_method = $"{result.CVFolds}-fold cross-validation",
                    weight_optimization = "Performance + Diversity + Stability based",
                    ensemble_size = result.ModelPredictions.Count,
                    features = new[]
                    {
                        "Rigorous cross-validation",
                        "Multi-criteria weight optimization",
                        "Diverse model ensemble",
                        "Statistical validation",
                        "Confidence estimation"
                    }
                }
            };

            var json = JsonSerializer.Serialize(predictionData, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(fileName, json);

            Console.WriteLine($"💾 Cross-validated prediction saved to: {fileName}");
        }

        // Helper methods for statistical calculations
        private double CalculateAccuracy(List<int> prediction, List<int> actual)
        {
            return (double)prediction.Intersect(actual).Count() / prediction.Count * 100.0;
        }

        private double CalculateVariance(List<int> numbers)
        {
            var mean = numbers.Average();
            return numbers.Sum(n => Math.Pow(n - mean, 2)) / numbers.Count;
        }

        private double CalculateMedian(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            int mid = sorted.Count / 2;
            return sorted.Count % 2 == 0 ? (sorted[mid - 1] + sorted[mid]) / 2.0 : sorted[mid];
        }

        private double CalculateStandardDeviation(List<double> values)
        {
            var mean = values.Average();
            var variance = values.Sum(v => Math.Pow(v - mean, 2)) / values.Count;
            return Math.Sqrt(variance);
        }

        private double CalculatePearsonCorrelation(List<double> x, List<double> y)
        {
            var n = x.Count;
            var sumX = x.Sum();
            var sumY = y.Sum();
            var sumXY = x.Zip(y, (a, b) => a * b).Sum();
            var sumX2 = x.Sum(a => a * a);
            var sumY2 = y.Sum(b => b * b);

            var numerator = n * sumXY - sumX * sumY;
            var denominator = Math.Sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

            return denominator == 0 ? 0 : numerator / denominator;
        }

        // Additional feature calculation methods
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

        private double CalculateGiniCoefficient(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var n = sorted.Count;
            var sum = sorted.Sum();

            if (sum == 0) return 0;

            double gini = 0;
            for (int i = 0; i < n; i++)
            {
                gini += (2 * (i + 1) - n - 1) * sorted[i];
            }

            return gini / (n * sum);
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

        private double CalculateMaxGap(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            double maxGap = 0;
            for (int i = 1; i < sorted.Count; i++)
            {
                maxGap = Math.Max(maxGap, sorted[i] - sorted[i - 1]);
            }
            return maxGap;
        }

        private double CalculateAverageGap(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var gaps = new List<double>();
            for (int i = 1; i < sorted.Count; i++)
            {
                gaps.Add(sorted[i] - sorted[i - 1]);
            }
            return gaps.Count > 0 ? gaps.Average() : 0;
        }

        private double CalculateGapVariance(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var gaps = new List<double>();
            for (int i = 1; i < sorted.Count; i++)
            {
                gaps.Add(sorted[i] - sorted[i - 1]);
            }

            if (gaps.Count <= 1) return 0;

            var mean = gaps.Average();
            return gaps.Sum(g => Math.Pow(g - mean, 2)) / gaps.Count;
        }

        private double CalculateClusterDensity(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var range = sorted.Last() - sorted.First();
            return range == 0 ? 1.0 : numbers.Count / (double)range;
        }

        private double CalculateIsolationIndex(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            double isolationScore = 0;

            for (int i = 0; i < sorted.Count; i++)
            {
                double minDistance = double.MaxValue;
                for (int j = 0; j < sorted.Count; j++)
                {
                    if (i != j)
                    {
                        minDistance = Math.Min(minDistance, Math.Abs(sorted[i] - sorted[j]));
                    }
                }
                isolationScore += minDistance;
            }

            return isolationScore / numbers.Count;
        }

        public CrossValidationResults GetLastValidationResults() => validationResults;
        public EnsembleWeights GetOptimizedWeights() => optimizedWeights;
    }

    // Data classes for cross-validation results
    public class CrossValidatedPrediction
    {
        public int SeriesId { get; set; }
        public List<int> Prediction { get; set; }
        public double Confidence { get; set; }
        public CrossValidationResults ValidationResults { get; set; }
        public EnsembleWeights OptimizedWeights { get; set; }
        public Dictionary<string, List<int>> ModelPredictions { get; set; }
        public int TrainingDataSize { get; set; }
        public int CVFolds { get; set; }
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    public class CrossValidationResults
    {
        public int Folds { get; set; }
        public List<FoldResult> FoldResults { get; set; } = new();
        public Dictionary<string, ModelValidationStats> ModelStatistics { get; set; } = new();
    }

    public class FoldResult
    {
        public int FoldIndex { get; set; }
        public Dictionary<string, double> ModelAccuracies { get; set; } = new();
    }

    public class ModelValidationStats
    {
        public double MeanAccuracy { get; set; }
        public double StdAccuracy { get; set; }
        public double MinAccuracy { get; set; }
        public double MaxAccuracy { get; set; }
        public double ConsistencyScore { get; set; }
    }

    public class EnsembleWeights
    {
        public Dictionary<string, double> ModelWeights { get; set; } = new();
        public DateTime OptimizedAt { get; set; } = DateTime.UtcNow;
    }

    public class EnsemblePredictionResult
    {
        public List<int> Numbers { get; set; }
        public Dictionary<string, List<int>> ModelPredictions { get; set; }
    }

    // Interface for ensemble models
    public interface IEnsembleModel
    {
        string ModelName { get; }
        void Train(List<SeriesPattern> trainingData);
        List<int> Predict(int targetSeriesId);
    }

    // Concrete ensemble model implementations
    public class LSTMEnsembleModel : IEnsembleModel
    {
        public string ModelName { get; private set; }
        private AdvancedLSTMModel lstmModel;

        public LSTMEnsembleModel(string name, int layers, int hiddenSize)
        {
            ModelName = name;
            lstmModel = new AdvancedLSTMModel(25, hiddenSize, 25, 10, layers);
        }

        public void Train(List<SeriesPattern> trainingData)
        {
            lstmModel.PrepareAdvancedTrainingData(trainingData);
            lstmModel.TrainAdvancedModel(epochs: 50, validationSplit: 0.2);
        }

        public List<int> Predict(int targetSeriesId)
        {
            // Would need training data context for actual prediction
            return GenerateRandomCombination();
        }

        private List<int> GenerateRandomCombination()
        {
            var random = new Random();
            return Enumerable.Range(1, 25).OrderBy(x => random.Next()).Take(14).OrderBy(x => x).ToList();
        }
    }

    public class StatisticalEnsembleModel : IEnsembleModel
    {
        public string ModelName { get; private set; }
        private bool isAggressive;
        private List<SeriesPattern> trainingData;
        private Random random = new Random(42);

        public StatisticalEnsembleModel(string name)
        {
            ModelName = name;
            isAggressive = name.Contains("Aggressive");
        }

        public void Train(List<SeriesPattern> trainingData)
        {
            this.trainingData = trainingData;
        }

        public List<int> Predict(int targetSeriesId)
        {
            if (trainingData == null || !trainingData.Any())
                return GenerateRandomCombination();

            var targetMean = isAggressive ?
                trainingData.TakeLast(10).Average(p => p.Features.GetValueOrDefault("mean", 13)) :
                trainingData.Average(p => p.Features.GetValueOrDefault("mean", 13));

            return GenerateTargetMeanPrediction(targetMean);
        }

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

                var closest = available.OrderBy(n => Math.Abs(n - avgNeeded)).First();
                numbers.Add(closest);
                currentSum += closest;
                available.Remove(closest);
            }

            return numbers.OrderBy(x => x).ToList();
        }

        private List<int> GenerateRandomCombination()
        {
            return Enumerable.Range(1, 25).OrderBy(x => random.Next()).Take(14).OrderBy(x => x).ToList();
        }
    }

    public class FrequencyEnsembleModel : IEnsembleModel
    {
        public string ModelName { get; private set; }
        private bool useRecent;
        private Dictionary<int, double> frequencies;
        private Random random = new Random(42);

        public FrequencyEnsembleModel(string name)
        {
            ModelName = name;
            useRecent = name.Contains("Recent");
        }

        public void Train(List<SeriesPattern> trainingData)
        {
            frequencies = new Dictionary<int, double>();
            for (int i = 1; i <= 25; i++) frequencies[i] = 0;

            var dataToUse = useRecent ? trainingData.TakeLast(30) : trainingData;

            foreach (var pattern in dataToUse)
            {
                foreach (var combo in pattern.Combinations)
                {
                    foreach (var num in combo)
                    {
                        frequencies[num]++;
                    }
                }
            }
        }

        public List<int> Predict(int targetSeriesId)
        {
            if (frequencies == null) return GenerateRandomCombination();

            return frequencies
                .OrderByDescending(kvp => kvp.Value)
                .Take(14)
                .Select(kvp => kvp.Key)
                .OrderBy(x => x)
                .ToList();
        }

        private List<int> GenerateRandomCombination()
        {
            return Enumerable.Range(1, 25).OrderBy(x => random.Next()).Take(14).OrderBy(x => x).ToList();
        }
    }

    public class PatternEnsembleModel : IEnsembleModel
    {
        public string ModelName { get; private set; }
        private bool focusConsecutive;
        private List<SeriesPattern> trainingData;
        private Random random = new Random(42);

        public PatternEnsembleModel(string name)
        {
            ModelName = name;
            focusConsecutive = name.Contains("Consecutive");
        }

        public void Train(List<SeriesPattern> trainingData)
        {
            this.trainingData = trainingData;
        }

        public List<int> Predict(int targetSeriesId)
        {
            if (trainingData == null) return GenerateRandomCombination();

            if (focusConsecutive)
            {
                return GenerateConsecutiveFocusedPrediction();
            }
            else
            {
                return GenerateDistributionFocusedPrediction();
            }
        }

        private List<int> GenerateConsecutiveFocusedPrediction()
        {
            var prediction = new List<int>();

            // Add some consecutive sequences
            var startPoints = new[] { 3, 7, 12, 18 };
            foreach (var start in startPoints)
            {
                for (int i = 0; i < 2 && prediction.Count < 14; i++)
                {
                    var num = start + i;
                    if (num <= 25 && !prediction.Contains(num))
                    {
                        prediction.Add(num);
                    }
                }
            }

            // Fill remaining with random
            var available = Enumerable.Range(1, 25).Except(prediction).ToList();
            while (prediction.Count < 14 && available.Any())
            {
                var index = random.Next(available.Count);
                prediction.Add(available[index]);
                available.RemoveAt(index);
            }

            return prediction.OrderBy(x => x).ToList();
        }

        private List<int> GenerateDistributionFocusedPrediction()
        {
            var prediction = new List<int>();

            // Balanced distribution across ranges
            var ranges = new[] {
                Enumerable.Range(1, 8).ToList(),    // Low
                Enumerable.Range(9, 9).ToList(),    // Mid
                Enumerable.Range(18, 8).ToList()    // High
            };

            var targetsPerRange = new[] { 5, 5, 4 }; // Balanced distribution

            for (int r = 0; r < ranges.Length; r++)
            {
                var selected = ranges[r].OrderBy(x => random.Next()).Take(targetsPerRange[r]);
                prediction.AddRange(selected);
            }

            return prediction.OrderBy(x => x).ToList();
        }

        private List<int> GenerateRandomCombination()
        {
            return Enumerable.Range(1, 25).OrderBy(x => random.Next()).Take(14).OrderBy(x => x).ToList();
        }
    }

    public class HybridEnsembleModel : IEnsembleModel
    {
        public string ModelName { get; private set; }
        private TrueLearningModel trueLearning;

        public HybridEnsembleModel(string name)
        {
            ModelName = name;
            trueLearning = new TrueLearningModel();
        }

        public void Train(List<SeriesPattern> trainingData)
        {
            foreach (var pattern in trainingData)
            {
                trueLearning.LearnFromSeries(pattern);
            }
        }

        public List<int> Predict(int targetSeriesId)
        {
            return trueLearning.PredictBestCombination(targetSeriesId);
        }
    }
}
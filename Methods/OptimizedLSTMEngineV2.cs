using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Models;
using DataProcessor.Connections;

namespace DataProcessor.Methods
{
    public class OptimizedLSTMEngineV2
    {
        private readonly DatabaseConnection dbConnection;
        private List<SeriesPattern> historicalData;
        
        // Test different LSTM configurations
        private List<ImprovedLSTMSequenceModel> lstmModels;
        private List<TrueLearningModel> statisticalModels;

        public OptimizedLSTMEngineV2()
        {
            dbConnection = new DatabaseConnection();
            historicalData = new List<SeriesPattern>();
            InitializeModels();
        }

        private void InitializeModels()
        {
            lstmModels = new List<ImprovedLSTMSequenceModel>
            {
                // Configuration 1: Small and fast
                new ImprovedLSTMSequenceModel(25, 16, 25, 4),
                
                // Configuration 2: Balanced
                new ImprovedLSTMSequenceModel(25, 32, 25, 6),
                
                // Configuration 3: Larger capacity
                new ImprovedLSTMSequenceModel(25, 48, 25, 8),
                
                // Configuration 4: Deep sequence
                new ImprovedLSTMSequenceModel(25, 24, 25, 10)
            };

            statisticalModels = new List<TrueLearningModel>
            {
                new TrueLearningModel(),
                new TrueLearningModel(),
                new TrueLearningModel()
            };
        }

        public List<int> OptimizedPredict(int targetSeriesId)
        {
            Console.WriteLine("🚀 Running Optimized Ensemble Prediction System");
            Console.WriteLine("==============================================");

            LoadHistoricalData(targetSeriesId);
            
            // Train all models
            var lstmPredictions = TrainAndPredictLSTMs();
            var statisticalPredictions = TrainAndPredictStatistical(targetSeriesId);
            
            // Combine all predictions
            var allPredictions = lstmPredictions.Concat(statisticalPredictions).ToList();
            
            // Find best prediction using multiple criteria
            var bestPrediction = SelectBestPrediction(allPredictions, targetSeriesId);
            
            SaveOptimizedPrediction(targetSeriesId, bestPrediction, allPredictions);
            
            return bestPrediction.Numbers;
        }

        private void LoadHistoricalData(int beforeSeriesId)
        {
            Console.WriteLine($"📊 Loading optimized historical data before series {beforeSeriesId}...");
            
            var rawData = dbConnection.LoadHistoricalDataBefore(beforeSeriesId);
            historicalData.Clear();

            // Use more data for better training, but limit for performance
            var limitedData = rawData.TakeLast(Math.Min(rawData.Count, 120)).ToList();

            foreach (var series in limitedData)
            {
                var pattern = new SeriesPattern
                {
                    SeriesId = series.SeriesId,
                    Combinations = series.AllCombinations
                };
                
                CalculateAdvancedFeatures(pattern);
                historicalData.Add(pattern);
            }

            Console.WriteLine($"✅ Loaded {historicalData.Count} series for ensemble training");
        }

        private void CalculateAdvancedFeatures(SeriesPattern pattern)
        {
            pattern.Features = new Dictionary<string, double>();

            if (pattern.Combinations.Count > 0)
            {
                var combo = pattern.Combinations[0];
                
                // Basic features
                pattern.Features["avg_number"] = combo.Average();
                pattern.Features["sum_total"] = combo.Sum();
                pattern.Features["variance"] = CalculateVariance(combo);
                pattern.Features["consecutive_count"] = CountConsecutive(combo);
                
                // Advanced features for better pattern recognition
                pattern.Features["spread"] = combo.Max() - combo.Min();
                pattern.Features["median"] = CalculateMedian(combo);
                pattern.Features["std_dev"] = Math.Sqrt(pattern.Features["variance"]);
                pattern.Features["skewness"] = CalculateSkewness(combo);
                
                // Distribution features
                pattern.Features["low_count"] = combo.Count(n => n <= 8);
                pattern.Features["mid_count"] = combo.Count(n => n >= 9 && n <= 17);
                pattern.Features["high_count"] = combo.Count(n => n >= 18);
                
                // Pattern features
                pattern.Features["even_count"] = combo.Count(n => n % 2 == 0);
                pattern.Features["prime_count"] = combo.Count(IsPrime);
                pattern.Features["gap_analysis"] = CalculateAverageGap(combo);
            }
        }

        private List<PredictionCandidate> TrainAndPredictLSTMs()
        {
            var predictions = new List<PredictionCandidate>();
            
            Console.WriteLine("🧠 Training multiple LSTM configurations...");
            
            for (int i = 0; i < lstmModels.Count; i++)
            {
                var model = lstmModels[i];
                var startTime = DateTime.UtcNow;
                
                try
                {
                    // Prepare training data
                    model.PrepareTrainingData(historicalData);
                    
                    // Train with different parameters based on model size
                    var epochs = i switch
                    {
                        0 => 15, // Fast model
                        1 => 20, // Balanced
                        2 => 25, // Large capacity
                        3 => 30  // Deep sequence
                    };
                    
                    var learningRate = i switch
                    {
                        0 => 0.015, // Faster learning for small model
                        1 => 0.01,  // Standard
                        2 => 0.008, // Slower for larger model
                        3 => 0.005  // Very careful for deep model
                    };
                    
                    model.TrainModel(epochs, learningRate);
                    
                    var trainingTime = DateTime.UtcNow - startTime;
                    
                    // Get prediction
                    var recentHistory = historicalData.TakeLast(model.GetModelInfo()["sequence_length"] is int seqLen ? seqLen : 6).ToList();
                    var prediction = model.PredictNextSequence(recentHistory);
                    
                    var candidate = new PredictionCandidate
                    {
                        Numbers = prediction,
                        Score = CalculateAdvancedScore(prediction, recentHistory, i),
                        FeatureScores = CalculateFeatureScores(prediction)
                    };
                    
                    predictions.Add(candidate);
                    
                    Console.WriteLine($"   LSTM Config {i + 1}: Score {candidate.Score:F3}, Time {trainingTime.TotalSeconds:F2}s");
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"   LSTM Config {i + 1}: Failed - {ex.Message}");
                }
            }
            
            return predictions;
        }

        private List<PredictionCandidate> TrainAndPredictStatistical(int targetSeriesId)
        {
            var predictions = new List<PredictionCandidate>();
            
            Console.WriteLine("📊 Training statistical models...");
            
            for (int i = 0; i < statisticalModels.Count; i++)
            {
                var model = statisticalModels[i];
                
                // Train with historical data
                foreach (var pattern in historicalData)
                {
                    model.LearnFromSeries(pattern);
                }
                
                // Get multiple predictions with different approaches
                var topPredictions = model.PredictTopCombinations(targetSeriesId, 3);
                
                for (int j = 0; j < topPredictions.Count; j++)
                {
                    var prediction = topPredictions[j];
                    var candidate = new PredictionCandidate
                    {
                        Numbers = prediction,
                        Score = CalculateStatisticalScore(prediction, j),
                        FeatureScores = CalculateFeatureScores(prediction)
                    };
                    
                    predictions.Add(candidate);
                }
                
                Console.WriteLine($"   Statistical Model {i + 1}: Generated {topPredictions.Count} predictions");
            }
            
            return predictions;
        }

        private double CalculateAdvancedScore(List<int> prediction, List<SeriesPattern> history, int modelIndex)
        {
            double score = 0;
            
            // Base score from distribution
            var low = prediction.Count(n => n <= 8);
            var mid = prediction.Count(n => n >= 9 && n <= 17);
            var high = prediction.Count(n => n >= 18);
            
            var idealLow = 4.7;
            var idealMid = 4.7;
            var idealHigh = 4.6;
            
            var distributionScore = 1.0 - (Math.Abs(low - idealLow) + Math.Abs(mid - idealMid) + Math.Abs(high - idealHigh)) / 14.0;
            score += distributionScore * 0.3;
            
            // Sum score
            var sum = prediction.Sum();
            var avgHistoricalSum = history.Average(h => h.Features.GetValueOrDefault("sum_total", 200));
            var sumScore = 1.0 - Math.Abs(sum - avgHistoricalSum) / avgHistoricalSum;
            score += Math.Max(0, sumScore) * 0.25;
            
            // Consecutive patterns
            var consecutiveCount = CountConsecutive(prediction);
            var avgConsecutive = history.Average(h => h.Features.GetValueOrDefault("consecutive_count", 2));
            var consecutiveScore = 1.0 - Math.Abs(consecutiveCount - avgConsecutive) / Math.Max(avgConsecutive, 1);
            score += Math.Max(0, consecutiveScore) * 0.2;
            
            // Variance score
            var variance = CalculateVariance(prediction);
            var avgVariance = history.Average(h => h.Features.GetValueOrDefault("variance", 50));
            var varianceScore = 1.0 - Math.Abs(variance - avgVariance) / avgVariance;
            score += Math.Max(0, varianceScore) * 0.15;
            
            // Model-specific bonuses
            var modelBonus = modelIndex switch
            {
                0 => 0.05, // Fast model bonus
                1 => 0.1,  // Balanced model bonus
                2 => 0.08, // Large capacity bonus
                3 => 0.06, // Deep sequence bonus
                _ => 0
            };
            
            score += modelBonus;
            
            return Math.Max(0, Math.Min(1, score));
        }

        private double CalculateStatisticalScore(List<int> prediction, int rank)
        {
            // Statistical models get base score based on rank
            var baseScore = 0.8 - (rank * 0.1);
            
            // Additional scoring based on prediction quality
            var sum = prediction.Sum();
            var variance = CalculateVariance(prediction);
            var consecutiveCount = CountConsecutive(prediction);
            
            // Prefer predictions with good balance
            if (sum >= 180 && sum <= 220) baseScore += 0.1;
            if (variance >= 30 && variance <= 70) baseScore += 0.05;
            if (consecutiveCount >= 1 && consecutiveCount <= 4) baseScore += 0.05;
            
            return Math.Max(0, Math.Min(1, baseScore));
        }

        private PredictionCandidate SelectBestPrediction(List<PredictionCandidate> predictions, int targetSeriesId)
        {
            Console.WriteLine($"🎯 Evaluating {predictions.Count} predictions...");
            
            var scored = predictions.OrderByDescending(p => p.Score).ToList();
            
            Console.WriteLine("Top 5 predictions:");
            for (int i = 0; i < Math.Min(5, scored.Count); i++)
            {
                var pred = scored[i];
                Console.WriteLine($"   #{i + 1}: {string.Join(" ", pred.Numbers.Select(n => n.ToString("D2")))} - Score: {pred.Score:F3}");
            }
            
            return scored.First();
        }

        private void SaveOptimizedPrediction(int seriesId, PredictionCandidate bestPrediction, List<PredictionCandidate> allPredictions)
        {
            try
            {
                System.IO.Directory.CreateDirectory("Results");
                var fileName = $"Results/optimized_ensemble_{seriesId}.json";
                
                var predictionData = new
                {
                    series_id = seriesId,
                    generation_timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                    model_type = "Optimized Ensemble V2 (LSTM + Statistical)",
                    best_prediction = new
                    {
                        numbers = bestPrediction.Numbers,
                        formatted = string.Join(" ", bestPrediction.Numbers.Select(n => n.ToString("D2"))),
                        score = bestPrediction.Score,
                        feature_scores = bestPrediction.FeatureScores
                    },
                    ensemble_details = new
                    {
                        total_models = lstmModels.Count + (statisticalModels.Count * 3),
                        lstm_configurations = lstmModels.Count,
                        statistical_models = statisticalModels.Count,
                        total_predictions_evaluated = allPredictions.Count
                    },
                    all_predictions = allPredictions.Select(p => new
                    {
                        numbers = string.Join(" ", p.Numbers.Select(n => n.ToString("D2"))),
                        score = p.Score
                    }).OrderByDescending(p => p.score).Take(10).ToArray(),
                    performance_improvements = new
                    {
                        multiple_lstm_configs = "4 different LSTM architectures tested",
                        statistical_ensemble = "3 TrueLearning models with top predictions",
                        advanced_scoring = "Multi-criteria evaluation system",
                        feature_engineering = "Enhanced pattern recognition"
                    }
                };

                var json = System.Text.Json.JsonSerializer.Serialize(predictionData, new System.Text.Json.JsonSerializerOptions 
                { 
                    WriteIndented = true 
                });
                System.IO.File.WriteAllText(fileName, json);
                
                Console.WriteLine($"💾 Optimized ensemble prediction saved to: {fileName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error saving optimized prediction: {ex.Message}");
            }
        }

        private Dictionary<string, double> CalculateFeatureScores(List<int> combination)
        {
            return new Dictionary<string, double>
            {
                ["consecutive"] = CountConsecutive(combination),
                ["sum"] = combination.Sum(),
                ["variance"] = CalculateVariance(combination),
                ["spread"] = combination.Max() - combination.Min(),
                ["median"] = CalculateMedian(combination),
                ["distribution_balance"] = CalculateDistributionBalance(combination)
            };
        }

        private double CalculateDistributionBalance(List<int> numbers)
        {
            var low = numbers.Count(n => n <= 8);
            var mid = numbers.Count(n => n >= 9 && n <= 17);
            var high = numbers.Count(n => n >= 18);
            
            var ideal = 14.0 / 3.0; // ~4.67 per range
            var balance = 1.0 - (Math.Abs(low - ideal) + Math.Abs(mid - ideal) + Math.Abs(high - ideal)) / 14.0;
            return Math.Max(0, balance);
        }

        // Helper methods
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

        private double CalculateSkewness(List<int> numbers)
        {
            var mean = numbers.Average();
            var stdDev = Math.Sqrt(CalculateVariance(numbers));
            if (stdDev == 0) return 0;
            
            return numbers.Sum(n => Math.Pow((n - mean) / stdDev, 3)) / numbers.Count;
        }

        private double CalculateAverageGap(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var gaps = new List<int>();
            for (int i = 1; i < sorted.Count; i++)
            {
                gaps.Add(sorted[i] - sorted[i - 1]);
            }
            return gaps.Count > 0 ? gaps.Average() : 0;
        }

        private int CountConsecutive(List<int> numbers)
        {
            var consecutive = 0;
            var sorted = numbers.OrderBy(x => x).ToList();
            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] == sorted[i-1] + 1)
                    consecutive++;
            }
            return consecutive;
        }

        private bool IsPrime(int n)
        {
            if (n < 2) return false;
            for (int i = 2; i <= Math.Sqrt(n); i++)
            {
                if (n % i == 0) return false;
            }
            return true;
        }
    }
}
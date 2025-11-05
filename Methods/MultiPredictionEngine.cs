using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text.Json;
using DataProcessor.Connections;
using DataProcessor.Models;

namespace DataProcessor.Methods
{
    /// <summary>
    /// Multi-Prediction Engine - Generates 7 diverse predictions per series
    /// Each prediction targets different event patterns to maximize coverage
    /// Highlights the most likely prediction based on confidence scoring
    /// </summary>
    public class MultiPredictionEngine
    {
        private readonly DatabaseConnection dbConnection;
        private readonly Random random;
        private readonly TrueLearningModel trueLearningModel;
        private readonly AdvancedLSTMModel advancedLSTMModel;
        private readonly AdaptiveLearningEngine adaptiveLearningEngine;

        public class MultiPredictionResult
        {
            public int SeriesId { get; set; }
            public List<PredictionCandidate> AllPredictions { get; set; } = new();
            public PredictionCandidate MostLikely { get; set; }
            public DateTime Timestamp { get; set; }
            public int TrainingDataSize { get; set; }
        }

        public class PredictionCandidate
        {
            public int PredictionNumber { get; set; }
            public string Strategy { get; set; }
            public List<int> Numbers { get; set; } = new();
            public double ConfidenceScore { get; set; }
            public string TargetEventType { get; set; }
            public Dictionary<string, double> FeatureScores { get; set; } = new();
            public bool IsMostLikely { get; set; }
        }

        public MultiPredictionEngine()
        {
            dbConnection = new DatabaseConnection();
            random = new Random();
            trueLearningModel = new TrueLearningModel();
            advancedLSTMModel = new AdvancedLSTMModel();
            adaptiveLearningEngine = new AdaptiveLearningEngine();
        }

        /// <summary>
        /// Generate 7 diverse predictions for a series
        /// </summary>
        public MultiPredictionResult GenerateMultiplePredictions(int seriesId)
        {
            Console.WriteLine($"\n🎯 Multi-Prediction Engine - Generating 7 Diverse Predictions");
            Console.WriteLine($"   Series: {seriesId}");
            Console.WriteLine($"   Strategy: Maximize coverage across different event patterns");
            Console.WriteLine();

            var historicalData = dbConnection.LoadHistoricalDataBefore(seriesId);
            var result = new MultiPredictionResult
            {
                SeriesId = seriesId,
                Timestamp = DateTime.Now,
                TrainingDataSize = historicalData.Count
            };

            // Generate 7 different predictions with diverse strategies
            // Mix ML models with pattern-based strategies
            var predictions = new List<PredictionCandidate>
            {
                GenerateTrueLearningPrediction(seriesId, historicalData, 1),
                GenerateAdvancedLSTMPrediction(seriesId, historicalData, 2),
                GenerateAdaptivePrediction(seriesId, historicalData, 3),
                GenerateBalancedPrediction(historicalData, 4),
                GenerateConsecutivePatternPrediction(historicalData, 5),
                GenerateStatisticalMeanPrediction(historicalData, 6),
                GenerateContrarianPrediction(historicalData, 7)
            };

            result.AllPredictions = predictions;

            // Score and rank predictions
            ScorePredictions(result.AllPredictions, historicalData);

            // Identify most likely prediction
            result.MostLikely = result.AllPredictions.OrderByDescending(p => p.ConfidenceScore).First();
            result.MostLikely.IsMostLikely = true;

            // Display results
            DisplayResults(result);

            // Save to file
            SaveResults(result);

            return result;
        }

        /// <summary>
        /// Strategy 1: TrueLearning ML Model (71%+ accuracy)
        /// </summary>
        private PredictionCandidate GenerateTrueLearningPrediction(int seriesId, List<Connections.SeriesData> historicalData, int predNumber)
        {
            var prediction = trueLearningModel.PredictBestCombination(seriesId);

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "TrueLearning ML (71%+ Accuracy)",
                Numbers = prediction,
                TargetEventType = "ML-trained pattern recognition",
                FeatureScores = new Dictionary<string, double>
                {
                    { "ml_confidence", 0.71 }
                }
            };
        }

        /// <summary>
        /// Strategy 2: Advanced LSTM Neural Network
        /// </summary>
        private PredictionCandidate GenerateAdvancedLSTMPrediction(int seriesId, List<Connections.SeriesData> historicalData, int predNumber)
        {
            var patterns = historicalData.Select(series => new Models.SeriesPattern
            {
                SeriesId = series.SeriesId,
                Combinations = series.AllCombinations
            }).ToList();

            var prediction = advancedLSTMModel.PredictAdvanced(patterns);

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "Advanced LSTM Neural Network",
                Numbers = prediction,
                TargetEventType = "Deep learning sequence patterns",
                FeatureScores = new Dictionary<string, double>
                {
                    { "lstm_depth", 2.0 }
                }
            };
        }

        /// <summary>
        /// Strategy 3: Adaptive Learning Engine (Real-time ML)
        /// </summary>
        private PredictionCandidate GenerateAdaptivePrediction(int seriesId, List<Connections.SeriesData> historicalData, int predNumber)
        {
            var adaptiveResult = adaptiveLearningEngine.PredictWithAdaptiveLearning(seriesId);

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "Adaptive ML Ensemble (Real-time Learning)",
                Numbers = adaptiveResult.Prediction.Numbers,
                TargetEventType = "Adaptive multi-model consensus",
                FeatureScores = new Dictionary<string, double>
                {
                    { "adaptive_confidence", adaptiveResult.Confidence }
                }
            };
        }

        /// <summary>
        /// Strategy 4: Balanced column distribution (pattern-based)
        /// </summary>
        private PredictionCandidate GenerateBalancedPrediction(List<Connections.SeriesData> historicalData, int predNumber)
        {
            var weights = new Dictionary<int, double>();
            for (int i = 1; i <= 25; i++)
            {
                // Higher weight for low numbers
                weights[i] = i <= 12 ? 2.0 : 0.5;
            }

            var prediction = GenerateWeightedSelection(weights, historicalData);

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "Low-Biased (1-12 Preference)",
                Numbers = prediction,
                TargetEventType = "Events with more low numbers",
                FeatureScores = new Dictionary<string, double>
                {
                    { "low_number_ratio", prediction.Count(n => n <= 12) / 14.0 }
                }
            };
        }

        /// <summary>
        /// Strategy 5: Consecutive pattern (more consecutive numbers)
        /// </summary>
        private PredictionCandidate GenerateConsecutivePatternPrediction(List<Connections.SeriesData> historicalData, int predNumber)
        {
            var prediction = new List<int>();
            var used = new HashSet<int>();

            // Start with a random number and build consecutive sequences
            int current = random.Next(1, 20);
            int consecutiveCount = 0;

            while (prediction.Count < 14)
            {
                if (current <= 25 && !used.Contains(current))
                {
                    prediction.Add(current);
                    used.Add(current);
                    consecutiveCount++;

                    // 70% chance to continue consecutive, 30% to jump
                    if (random.NextDouble() < 0.7 && consecutiveCount < 4)
                    {
                        current++;
                    }
                    else
                    {
                        current = random.Next(1, 26);
                        consecutiveCount = 0;
                    }
                }
                else
                {
                    current = random.Next(1, 26);
                }
            }

            prediction.Sort();

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "Consecutive Pattern (More Sequences)",
                Numbers = prediction,
                TargetEventType = "Events with consecutive number groups",
                FeatureScores = new Dictionary<string, double>
                {
                    { "consecutive_groups", CountConsecutiveGroups(prediction) }
                }
            };
        }

        /// <summary>
        /// Strategy 5: Gap pattern (more spacing between numbers)
        /// </summary>
        private PredictionCandidate GenerateGapPatternPrediction(List<Connections.SeriesData> historicalData, int predNumber)
        {
            var prediction = new List<int>();
            var used = new HashSet<int>();

            int current = random.Next(1, 6);
            prediction.Add(current);
            used.Add(current);

            while (prediction.Count < 14)
            {
                // Jump by 2-3 numbers
                int gap = random.Next(2, 4);
                current += gap;

                if (current > 25)
                {
                    current = Enumerable.Range(1, 25).Where(n => !used.Contains(n)).OrderBy(x => random.Next()).FirstOrDefault();
                    if (current == 0) break;
                }

                if (!used.Contains(current))
                {
                    prediction.Add(current);
                    used.Add(current);
                }
            }

            // Fill remaining with random
            while (prediction.Count < 14)
            {
                int num = random.Next(1, 26);
                if (!used.Contains(num))
                {
                    prediction.Add(num);
                    used.Add(num);
                }
            }

            prediction.Sort();

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "Gap Pattern (Spaced Numbers)",
                Numbers = prediction,
                TargetEventType = "Events with larger gaps between numbers",
                FeatureScores = new Dictionary<string, double>
                {
                    { "average_gap", CalculateAverageGap(prediction) }
                }
            };
        }

        /// <summary>
        /// Strategy 6: Statistical mean (closest to historical average)
        /// </summary>
        private PredictionCandidate GenerateStatisticalMeanPrediction(List<Connections.SeriesData> historicalData, int predNumber)
        {
            // Calculate frequency of each number
            var frequencies = new Dictionary<int, int>();
            for (int i = 1; i <= 25; i++)
            {
                frequencies[i] = 0;
            }

            foreach (var series in historicalData.TakeLast(50))
            {
                foreach (var combination in series.AllCombinations)
                {
                    foreach (var num in combination)
                    {
                        frequencies[num]++;
                    }
                }
            }

            // Select top 14 most frequent
            var prediction = frequencies
                .OrderByDescending(kvp => kvp.Value)
                .ThenBy(x => random.Next())
                .Take(14)
                .Select(kvp => kvp.Key)
                .OrderBy(n => n)
                .ToList();

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "Statistical Mean (Most Frequent)",
                Numbers = prediction,
                TargetEventType = "Events matching historical frequency patterns",
                FeatureScores = new Dictionary<string, double>
                {
                    { "frequency_alignment", CalculateFrequencyAlignment(prediction, frequencies) }
                }
            };
        }

        /// <summary>
        /// Strategy 7: Contrarian (opposite of recent trends)
        /// </summary>
        private PredictionCandidate GenerateContrarianPrediction(List<Connections.SeriesData> historicalData, int predNumber)
        {
            // Calculate frequency in last 10 series
            var recentFreq = new Dictionary<int, int>();
            for (int i = 1; i <= 25; i++)
            {
                recentFreq[i] = 0;
            }

            foreach (var series in historicalData.TakeLast(10))
            {
                foreach (var combination in series.AllCombinations)
                {
                    foreach (var num in combination)
                    {
                        recentFreq[num]++;
                    }
                }
            }

            // Select 14 LEAST frequent (contrarian to recent trends)
            var prediction = recentFreq
                .OrderBy(kvp => kvp.Value)
                .ThenBy(x => random.Next())
                .Take(14)
                .Select(kvp => kvp.Key)
                .OrderBy(n => n)
                .ToList();

            return new PredictionCandidate
            {
                PredictionNumber = predNumber,
                Strategy = "Contrarian (Opposite Recent Trends)",
                Numbers = prediction,
                TargetEventType = "Events with numbers due to appear",
                FeatureScores = new Dictionary<string, double>
                {
                    { "contrarian_score", CalculateContrarianScore(prediction, recentFreq) }
                }
            };
        }

        /// <summary>
        /// Generate weighted selection based on custom weights
        /// </summary>
        private List<int> GenerateWeightedSelection(Dictionary<int, double> weights, List<Connections.SeriesData> historicalData)
        {
            var selected = new List<int>();
            var available = Enumerable.Range(1, 25).ToList();

            while (selected.Count < 14)
            {
                var totalWeight = available.Sum(n => weights[n]);
                var randomValue = random.NextDouble() * totalWeight;

                double cumulative = 0;
                foreach (var num in available)
                {
                    cumulative += weights[num];
                    if (randomValue <= cumulative)
                    {
                        selected.Add(num);
                        available.Remove(num);
                        break;
                    }
                }
            }

            selected.Sort();
            return selected;
        }

        /// <summary>
        /// Score all predictions based on historical patterns
        /// </summary>
        private void ScorePredictions(List<PredictionCandidate> predictions, List<Connections.SeriesData> historicalData)
        {
            foreach (var pred in predictions)
            {
                double score = 0;

                // ML Model Bonus: Prioritize machine learning models (weight: 35%)
                bool isMLModel = pred.Strategy.Contains("ML") || pred.Strategy.Contains("LSTM") || pred.Strategy.Contains("Adaptive");
                if (isMLModel)
                {
                    // ML models get a significant bonus based on their historical performance
                    if (pred.Strategy.Contains("TrueLearning"))
                        score += 0.71 * 0.35;  // 71% historical accuracy
                    else if (pred.Strategy.Contains("LSTM"))
                        score += 0.75 * 0.35;  // LSTM tends to perform well
                    else if (pred.Strategy.Contains("Adaptive"))
                        score += 0.70 * 0.35;  // Adaptive ensemble
                }

                // Factor 1: Column balance (weight: 15%, reduced from 25%)
                score += CalculateColumnBalance(pred.Numbers) * 0.15;

                // Factor 2: Sum proximity to historical mean (weight: 15%, reduced from 20%)
                score += CalculateSumProximity(pred.Numbers, historicalData) * 0.15;

                // Factor 3: Variance similarity (weight: 10%, reduced from 15%)
                score += CalculateVarianceSimilarity(pred.Numbers, historicalData) * 0.10;

                // Factor 4: Pattern diversity (weight: 10%, reduced from 15%)
                score += CalculatePatternDiversity(pred.Numbers) * 0.10;

                // Factor 5: Historical frequency alignment (weight: 15%, reduced from 25%)
                score += CalculateHistoricalAlignment(pred.Numbers, historicalData) * 0.15;

                pred.ConfidenceScore = Math.Round(score * 100, 2);
            }
        }

        // Helper scoring methods
        private double CalculateColumnBalance(List<int> numbers)
        {
            int col0 = numbers.Count(n => n >= 1 && n <= 9);
            int col1 = numbers.Count(n => n >= 10 && n <= 19);
            int col2 = numbers.Count(n => n >= 20 && n <= 25);

            // Ideal: 5-5-4 or close
            double ideal0 = 5.0, ideal1 = 5.0, ideal2 = 4.0;
            double deviation = Math.Abs(col0 - ideal0) + Math.Abs(col1 - ideal1) + Math.Abs(col2 - ideal2);

            return Math.Max(0, 1.0 - (deviation / 14.0));
        }

        private double CalculateSumProximity(List<int> numbers, List<Connections.SeriesData> historicalData)
        {
            double predictedSum = numbers.Sum();
            var historicalSums = historicalData.SelectMany(s => s.AllCombinations).Select(c => c.Sum()).ToList();
            double avgSum = historicalSums.Average();
            double stdDev = Math.Sqrt(historicalSums.Average(s => Math.Pow(s - avgSum, 2)));

            double deviation = Math.Abs(predictedSum - avgSum);
            return Math.Max(0, 1.0 - (deviation / (2 * stdDev)));
        }

        private double CalculateVarianceSimilarity(List<int> numbers, List<Connections.SeriesData> historicalData)
        {
            double predictedVariance = CalculateVariance(numbers);
            var historicalVariances = historicalData.SelectMany(s => s.AllCombinations).Select(c => CalculateVariance(c)).ToList();
            double avgVariance = historicalVariances.Average();

            double deviation = Math.Abs(predictedVariance - avgVariance);
            return Math.Max(0, 1.0 - (deviation / avgVariance));
        }

        private double CalculatePatternDiversity(List<int> numbers)
        {
            // Reward having some consecutive and some gaps
            int consecutiveCount = CountConsecutiveGroups(numbers);
            double avgGap = CalculateAverageGap(numbers);

            // Ideal: 2-4 consecutive groups, average gap 1.5-2.0
            double consecutiveScore = consecutiveCount >= 2 && consecutiveCount <= 4 ? 1.0 : 0.5;
            double gapScore = avgGap >= 1.5 && avgGap <= 2.0 ? 1.0 : 0.5;

            return (consecutiveScore + gapScore) / 2.0;
        }

        private double CalculateHistoricalAlignment(List<int> numbers, List<Connections.SeriesData> historicalData)
        {
            var frequencies = new Dictionary<int, int>();
            for (int i = 1; i <= 25; i++) frequencies[i] = 0;

            foreach (var series in historicalData.TakeLast(50))
            {
                foreach (var combination in series.AllCombinations)
                {
                    foreach (var num in combination)
                    {
                        frequencies[num]++;
                    }
                }
            }

            double totalFreq = frequencies.Values.Sum();
            double predictionScore = numbers.Sum(n => frequencies[n]) / totalFreq;

            return predictionScore * 14; // Normalize
        }

        private double CalculateVariance(List<int> numbers)
        {
            double mean = numbers.Average();
            return numbers.Average(n => Math.Pow(n - mean, 2));
        }

        private int CountConsecutiveGroups(List<int> numbers)
        {
            int groups = 0;
            for (int i = 0; i < numbers.Count - 1; i++)
            {
                if (numbers[i + 1] == numbers[i] + 1)
                {
                    if (i == 0 || numbers[i] != numbers[i - 1] + 1)
                    {
                        groups++;
                    }
                }
            }
            return groups;
        }

        private double CalculateAverageGap(List<int> numbers)
        {
            if (numbers.Count < 2) return 0;

            double totalGap = 0;
            for (int i = 0; i < numbers.Count - 1; i++)
            {
                totalGap += numbers[i + 1] - numbers[i];
            }

            return totalGap / (numbers.Count - 1);
        }

        private double CalculateFrequencyAlignment(List<int> numbers, Dictionary<int, int> frequencies)
        {
            double totalFreq = frequencies.Values.Sum();
            double predictionFreq = numbers.Sum(n => frequencies[n]);
            return predictionFreq / totalFreq;
        }

        private double CalculateContrarianScore(List<int> numbers, Dictionary<int, int> recentFreq)
        {
            double avgFreq = recentFreq.Values.Average();
            double predictionFreq = numbers.Average(n => recentFreq[n]);
            return Math.Max(0, 1.0 - (predictionFreq / avgFreq));
        }

        /// <summary>
        /// Display results to console
        /// </summary>
        private void DisplayResults(MultiPredictionResult result)
        {
            Console.WriteLine($"\n{new string('=', 100)}");
            Console.WriteLine($"MULTI-PREDICTION RESULTS - Series {result.SeriesId}");
            Console.WriteLine($"{new string('=', 100)}");
            Console.WriteLine($"Training Data: {result.TrainingDataSize} series");
            Console.WriteLine($"Generated: {result.Timestamp:yyyy-MM-dd HH:mm:ss}");
            Console.WriteLine();

            Console.WriteLine($"🎯 MOST LIKELY PREDICTION (Confidence: {result.MostLikely.ConfidenceScore}%):");
            Console.WriteLine($"   #{result.MostLikely.PredictionNumber}: {string.Join(" ", result.MostLikely.Numbers.Select(n => n.ToString("D2")))}");
            Console.WriteLine($"   Strategy: {result.MostLikely.Strategy}");
            Console.WriteLine($"   Target: {result.MostLikely.TargetEventType}");
            Console.WriteLine();

            Console.WriteLine($"📊 ALL 7 PREDICTIONS (Ranked by Confidence):");
            Console.WriteLine($"{new string('-', 100)}");

            foreach (var pred in result.AllPredictions.OrderByDescending(p => p.ConfidenceScore))
            {
                string marker = pred.IsMostLikely ? "⭐" : "  ";
                Console.WriteLine($"{marker} #{pred.PredictionNumber} [{pred.ConfidenceScore:F1}%] {pred.Strategy}");
                Console.WriteLine($"      {string.Join(" ", pred.Numbers.Select(n => n.ToString("D2")))}");
                Console.WriteLine($"      Target: {pred.TargetEventType}");
                Console.WriteLine();
            }

            Console.WriteLine($"{new string('=', 100)}");
        }

        /// <summary>
        /// Save results to JSON file
        /// </summary>
        private void SaveResults(MultiPredictionResult result)
        {
            var filePath = Path.Combine("Results", $"multi_prediction_{result.SeriesId}.json");
            var json = JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(filePath, json);

            Console.WriteLine($"💾 Results saved to: {filePath}");
        }
    }
}

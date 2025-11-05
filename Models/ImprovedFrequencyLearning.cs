using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Connections;

namespace DataProcessor.Models
{
    public class ImprovedFrequencyLearning
    {
        private Dictionary<int, double> frequencyWeights;
        private Dictionary<int, double> recentPatternWeights;
        private Dictionary<int, double> rangeWeights;
        private Dictionary<int, int> consecutivePatternWeights;
        private DatabaseConnection dbConnection;
        private const int RECENT_SERIES_WEIGHT = 10; // Recent series have higher weight
        private const double LOWER_RANGE_MULTIPLIER = 2.5; // Boost for numbers 1-3
        private const double HIGH_FREQUENCY_THRESHOLD = 0.6; // 60% appearance rate

        public ImprovedFrequencyLearning()
        {
            frequencyWeights = new Dictionary<int, double>();
            recentPatternWeights = new Dictionary<int, double>();
            rangeWeights = new Dictionary<int, double>();
            consecutivePatternWeights = new Dictionary<int, int>();
            dbConnection = new DatabaseConnection();
            InitializeWeights();
        }

        private void InitializeWeights()
        {
            // Initialize all numbers with base weight
            for (int i = 1; i <= 25; i++)
            {
                frequencyWeights[i] = 1.0;
                recentPatternWeights[i] = 1.0;
                rangeWeights[i] = 1.0;
                consecutivePatternWeights[i] = 1;
            }

            // Apply range-specific multipliers based on analysis
            ApplyRangeWeights();
            UpdateWithHistoricalData();
        }

        private void ApplyRangeWeights()
        {
            // Lower numbers (1-3) - heavily under-predicted, need boost
            for (int i = 1; i <= 3; i++)
            {
                rangeWeights[i] = LOWER_RANGE_MULTIPLIER;
            }

            // Mid-low range (4-9) - moderately under-predicted
            for (int i = 4; i <= 9; i++)
            {
                rangeWeights[i] = 1.8;
            }

            // Mid range (10-15) - mixed performance
            for (int i = 10; i <= 15; i++)
            {
                rangeWeights[i] = 1.5;
            }

            // Higher range (16-25) - over-predicted, reduce weight
            for (int i = 16; i <= 25; i++)
            {
                rangeWeights[i] = 0.8;
            }

            // Special cases based on 3126 analysis
            rangeWeights[2] = 3.0;  // Number 2 appeared 100% of time
            rangeWeights[15] = 2.8; // Number 15 completely missed
            rangeWeights[23] = 2.2; // Number 23 under-predicted
            rangeWeights[12] = 2.0; // Number 12 high frequency
        }

        public void UpdateWithHistoricalData()
        {
            var historicalData = dbConnection.LoadHistoricalDataBefore(3127); // Include 3126

            // Calculate frequency weights with recent bias
            var totalFrequencies = new Dictionary<int, int>();
            var recentFrequencies = new Dictionary<int, int>();

            for (int i = 1; i <= 25; i++)
            {
                totalFrequencies[i] = 0;
                recentFrequencies[i] = 0;
            }

            int totalSeries = historicalData.Count;
            int recentSeriesCount = Math.Min(20, totalSeries); // Last 20 series for recent patterns

            // Count frequencies
            for (int seriesIndex = 0; seriesIndex < historicalData.Count; seriesIndex++)
            {
                var series = historicalData[seriesIndex];
                bool isRecent = seriesIndex >= (totalSeries - recentSeriesCount);

                foreach (var combination in series.AllCombinations)
                {
                    foreach (int number in combination)
                    {
                        totalFrequencies[number]++;
                        if (isRecent)
                        {
                            recentFrequencies[number]++;
                        }
                    }
                }
            }

            // Update frequency weights
            int totalCombinations = totalFrequencies.Values.Sum();
            int recentCombinations = recentFrequencies.Values.Sum();

            for (int i = 1; i <= 25; i++)
            {
                // Base frequency weight
                double baseFrequency = (double)totalFrequencies[i] / totalCombinations;
                frequencyWeights[i] = Math.Max(0.1, baseFrequency * 10); // Scale and minimum

                // Recent pattern weight (higher influence)
                if (recentCombinations > 0)
                {
                    double recentFrequency = (double)recentFrequencies[i] / recentCombinations;
                    recentPatternWeights[i] = Math.Max(0.2, recentFrequency * RECENT_SERIES_WEIGHT);
                }
            }

            // Update consecutive pattern weights
            UpdateConsecutivePatternWeights(historicalData);
        }

        private void UpdateConsecutivePatternWeights(List<DataProcessor.Connections.SeriesData> historicalData)
        {
            var consecutiveCounts = new Dictionary<int, int>();
            for (int i = 1; i <= 25; i++)
            {
                consecutiveCounts[i] = 0;
            }

            foreach (var series in historicalData)
            {
                foreach (var combination in series.AllCombinations)
                {
                    var sortedCombo = combination.OrderBy(x => x).ToList();

                    // Find consecutive sequences
                    for (int i = 0; i < sortedCombo.Count - 1; i++)
                    {
                        if (sortedCombo[i + 1] - sortedCombo[i] == 1)
                        {
                            consecutiveCounts[sortedCombo[i]]++;
                            consecutiveCounts[sortedCombo[i + 1]]++;
                        }
                    }
                }
            }

            // Update weights based on consecutive appearance
            foreach (var kvp in consecutiveCounts)
            {
                consecutivePatternWeights[kvp.Key] = Math.Max(1, kvp.Value / 10); // Scale down
            }
        }

        public double GetCombinedWeight(int number)
        {
            double baseFrequency = frequencyWeights.GetValueOrDefault(number, 1.0);
            double recentPattern = recentPatternWeights.GetValueOrDefault(number, 1.0);
            double rangeWeight = rangeWeights.GetValueOrDefault(number, 1.0);
            double consecutiveWeight = consecutivePatternWeights.GetValueOrDefault(number, 1);

            // Combined formula emphasizing recent patterns and range corrections
            return (baseFrequency * 0.3 + recentPattern * 0.4 + rangeWeight * 0.2 + consecutiveWeight * 0.1);
        }

        public List<int> GenerateImprovedPrediction(int targetSeries, int count = 14)
        {
            // Update weights with latest data
            UpdateWithHistoricalData();

            var weightedNumbers = new List<(int number, double weight)>();

            for (int i = 1; i <= 25; i++)
            {
                double combinedWeight = GetCombinedWeight(i);
                weightedNumbers.Add((i, combinedWeight));
            }

            // Sort by combined weight (descending)
            weightedNumbers = weightedNumbers.OrderByDescending(x => x.weight).ToList();

            // Select top numbers with some randomization for diversity
            var selectedNumbers = new List<int>();
            var random = new Random(42 + targetSeries); // Deterministic but series-specific

            // Take top performers with slight randomization
            for (int i = 0; i < Math.Min(count + 3, weightedNumbers.Count); i++)
            {
                if (selectedNumbers.Count >= count) break;

                var candidate = weightedNumbers[i];

                // Higher probability for higher weights, but allow some diversity
                double selectionProbability = Math.Min(0.95, candidate.weight / weightedNumbers[0].weight);

                if (random.NextDouble() < selectionProbability || selectedNumbers.Count >= count - 2)
                {
                    selectedNumbers.Add(candidate.number);
                }
            }

            // Ensure we have exactly the required count
            while (selectedNumbers.Count < count)
            {
                var remaining = weightedNumbers.Where(x => !selectedNumbers.Contains(x.number)).ToList();
                if (remaining.Any())
                {
                    selectedNumbers.Add(remaining.First().number);
                }
                else break;
            }

            return selectedNumbers.Take(count).OrderBy(x => x).ToList();
        }

        public void LearnFromActualResults(int seriesId, List<int> actualCombination)
        {
            // Boost weights for numbers that appeared in actual results
            foreach (int number in actualCombination)
            {
                frequencyWeights[number] = Math.Min(5.0, frequencyWeights[number] * 1.2);
                recentPatternWeights[number] = Math.Min(8.0, recentPatternWeights[number] * 1.3);
            }

            // Slightly reduce weights for numbers that didn't appear
            var allNumbers = Enumerable.Range(1, 25).ToList();
            var missedNumbers = allNumbers.Except(actualCombination).ToList();

            foreach (int number in missedNumbers)
            {
                frequencyWeights[number] = Math.Max(0.1, frequencyWeights[number] * 0.95);
            }

            Console.WriteLine($"📈 Learned from series {seriesId}: Boosted {actualCombination.Count} numbers, reduced {missedNumbers.Count} numbers");
        }

        public Dictionary<string, object> GetWeightingAnalysis()
        {
            var analysis = new Dictionary<string, object>();

            var topFrequencyWeights = frequencyWeights.OrderByDescending(x => x.Value).Take(10).ToDictionary(x => x.Key, x => x.Value);
            var topRecentWeights = recentPatternWeights.OrderByDescending(x => x.Value).Take(10).ToDictionary(x => x.Key, x => x.Value);
            var topRangeWeights = rangeWeights.OrderByDescending(x => x.Value).Take(10).ToDictionary(x => x.Key, x => x.Value);

            analysis["TopFrequencyWeights"] = topFrequencyWeights;
            analysis["TopRecentWeights"] = topRecentWeights;
            analysis["TopRangeWeights"] = topRangeWeights;

            return analysis;
        }
    }
}
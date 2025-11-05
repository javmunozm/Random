using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Connections;

namespace DataProcessor.Models
{
    public class UniquenessValidator
    {
        private readonly DatabaseConnection dbConnection;
        private readonly int lookbackWindow;

        public UniquenessValidator(int lookbackWindow = 151)
        {
            dbConnection = new DatabaseConnection();
            this.lookbackWindow = lookbackWindow;
        }

        public bool IsUniqueCombination(List<int> combination, int targetSeriesId)
        {
            // Load historical data for the lookback window
            var startSeriesId = Math.Max(targetSeriesId - lookbackWindow, 1);
            var recentData = LoadRecentCombinations(startSeriesId, targetSeriesId - 1);
            
            // Convert combination to comparable string
            var combinationStr = string.Join(",", combination.OrderBy(x => x));
            
            // Check if this combination exists in recent data
            return !recentData.Contains(combinationStr);
        }

        public List<List<int>> FilterUniqueCombinations(List<List<int>> combinations, int targetSeriesId)
        {
            var uniqueCombinations = new List<List<int>>();
            
            // Load recent combinations once for efficiency
            var startSeriesId = Math.Max(targetSeriesId - lookbackWindow, 1);
            var recentCombinations = LoadRecentCombinations(startSeriesId, targetSeriesId - 1);
            
            foreach (var combination in combinations)
            {
                var combinationStr = string.Join(",", combination.OrderBy(x => x));
                
                if (!recentCombinations.Contains(combinationStr))
                {
                    uniqueCombinations.Add(combination);
                }
            }
            
            return uniqueCombinations;
        }

        public List<int> GenerateUniqueCombination(int targetSeriesId, int maxAttempts = 1000)
        {
            // Load recent combinations
            var startSeriesId = Math.Max(targetSeriesId - lookbackWindow, 1);
            var recentCombinations = LoadRecentCombinations(startSeriesId, targetSeriesId - 1);
            
            var random = new Random(42); // Deterministic for consistency
            
            for (int attempt = 0; attempt < maxAttempts; attempt++)
            {
                // Generate random 14 numbers from 1-25
                var combination = new List<int>();
                while (combination.Count < 14)
                {
                    int number = random.Next(1, 26);
                    if (!combination.Contains(number))
                    {
                        combination.Add(number);
                    }
                }
                
                combination.Sort();
                var combinationStr = string.Join(",", combination);
                
                if (!recentCombinations.Contains(combinationStr))
                {
                    return combination;
                }
            }
            
            // If we can't find a unique combination after maxAttempts, return a random one
            // This should be extremely rare given the large combination space
            Console.WriteLine($"⚠️ Warning: Could not find unique combination after {maxAttempts} attempts");
            var fallback = new List<int>();
            var fallbackRandom = new Random(targetSeriesId);
            while (fallback.Count < 14)
            {
                int number = fallbackRandom.Next(1, 26);
                if (!fallback.Contains(number))
                {
                    fallback.Add(number);
                }
            }
            fallback.Sort();
            return fallback;
        }

        public UniquenessValidationResult ValidatePrediction(List<int> prediction, int targetSeriesId)
        {
            var result = new UniquenessValidationResult
            {
                IsUnique = IsUniqueCombination(prediction, targetSeriesId),
                TargetSeriesId = targetSeriesId,
                LookbackWindow = lookbackWindow
            };

            if (!result.IsUnique)
            {
                // Find which series this combination appeared in
                var startSeriesId = Math.Max(targetSeriesId - lookbackWindow, 1);
                var historicalData = dbConnection.LoadHistoricalDataBefore(targetSeriesId);
                
                var predictionStr = string.Join(",", prediction.OrderBy(x => x));
                
                foreach (var series in historicalData.Where(s => s.SeriesId >= startSeriesId))
                {
                    foreach (var combination in series.AllCombinations)
                    {
                        var combinationStr = string.Join(",", combination.OrderBy(x => x));
                        if (combinationStr == predictionStr)
                        {
                            result.ConflictingSeriesIds.Add(series.SeriesId);
                        }
                    }
                }
            }

            return result;
        }

        private HashSet<string> LoadRecentCombinations(int startSeriesId, int endSeriesId)
        {
            var recentCombinations = new HashSet<string>();
            var historicalData = dbConnection.LoadHistoricalDataBefore(endSeriesId + 1);
            
            foreach (var series in historicalData.Where(s => s.SeriesId >= startSeriesId && s.SeriesId <= endSeriesId))
            {
                foreach (var combination in series.AllCombinations)
                {
                    var combinationStr = string.Join(",", combination.OrderBy(x => x));
                    recentCombinations.Add(combinationStr);
                }
            }
            
            return recentCombinations;
        }

        public UniquenessStats GetUniquenessStats(int targetSeriesId)
        {
            var startSeriesId = Math.Max(targetSeriesId - lookbackWindow, 1);
            var recentCombinations = LoadRecentCombinations(startSeriesId, targetSeriesId - 1);
            var seriesCount = Math.Min(lookbackWindow, targetSeriesId - 1);
            
            return new UniquenessStats
            {
                TotalRecentCombinations = recentCombinations.Count,
                SeriesAnalyzed = seriesCount,
                TheoreticalMaxCombinations = 4457400, // C(25,14)
                PercentageUsed = (recentCombinations.Count / 4457400.0) * 100,
                RemainingUniqueCombinations = 4457400 - recentCombinations.Count
            };
        }
    }

    public class UniquenessValidationResult
    {
        public bool IsUnique { get; set; }
        public int TargetSeriesId { get; set; }
        public int LookbackWindow { get; set; }
        public List<int> ConflictingSeriesIds { get; set; } = new List<int>();
        
        public override string ToString()
        {
            if (IsUnique)
            {
                return $"✅ Combination is UNIQUE (no conflicts in last {LookbackWindow} series)";
            }
            else
            {
                return $"❌ Combination is NOT UNIQUE - conflicts with series: {string.Join(", ", ConflictingSeriesIds)}";
            }
        }
    }

    public class UniquenessStats
    {
        public int TotalRecentCombinations { get; set; }
        public int SeriesAnalyzed { get; set; }
        public int TheoreticalMaxCombinations { get; set; }
        public double PercentageUsed { get; set; }
        public int RemainingUniqueCombinations { get; set; }
        
        public override string ToString()
        {
            return $"""
                📊 UNIQUENESS STATISTICS:
                Series analyzed: {SeriesAnalyzed}
                Recent combinations: {TotalRecentCombinations:N0}
                Theoretical maximum: {TheoreticalMaxCombinations:N0}
                Percentage used: {PercentageUsed:F6}%
                Remaining unique: {RemainingUniqueCombinations:N0}
                """;
        }
    }
}
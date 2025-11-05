using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor
{
    // Enhanced pattern learning based on actual 3108 results analysis
    public static class EnhancedPatternLearning
    {
        // Learned insights from 3108 analysis
        public static Dictionary<string, object> GetLearnedPatterns()
        {
            return new Dictionary<string, object>
            {
                // Hot numbers that actually appeared frequently in 3108
                ["super_hot_numbers"] = new List<int> { 22, 3, 19, 1, 12, 13, 6, 23 },
                
                // Mathematical pattern preferences (actual 3108 data)
                ["prime_preference"] = 0.378,  // 37.8% primes in actual results
                ["fibonacci_preference"] = 0.286, // 28.6% fibonacci in actual results  
                ["perfect_square_preference"] = 0.184, // 18.4% perfect squares in actual results
                
                // Sum insights
                ["target_sum_mean"] = 178.9,
                ["sum_std_deviation"] = 12.0, // Estimated from range
                
                // Gap insights
                ["optimal_gap"] = 1.70,
                ["gap_tolerance"] = 0.1,
                
                // Range distribution (more balanced than my previous predictions)
                ["low_range_target"] = 0.316,  // 31.6% low numbers (1-8)
                ["mid_range_target"] = 0.357,  // 35.7% mid numbers (9-17) 
                ["high_range_target"] = 0.327, // 32.7% high numbers (18-25)
                
                // Learned combination strategies
                ["hot_number_inclusion_rate"] = 0.80, // Include 80% hot numbers
                ["mathematical_pattern_bonus"] = 1.5,  // Increased weight for math patterns
                ["sum_convergence_importance"] = 2.0,   // Sum targeting is critical
                ["gap_pattern_importance"] = 1.8       // Gap patterns are important
            };
        }

        public static double CalculateEnhancedScore(List<int> combination, Dictionary<string, object> patterns)
        {
            var learned = GetLearnedPatterns();
            double score = 0.0;

            // 1. Super Hot Numbers Score (20% - increased importance)
            var superHotNumbers = (List<int>)learned["super_hot_numbers"];
            var superHotCount = combination.Count(n => superHotNumbers.Contains(n));
            var superHotScore = (superHotCount / 8.0) * 100; // Target 8 out of 8 super hot
            score += superHotScore * 0.20;

            // 2. Enhanced Mathematical Patterns (18% - learned preferences)
            var mathScore = CalculateLearnedMathematicalScore(combination, learned);
            score += mathScore * 0.18;

            // 3. Precise Sum Targeting (15% - critical insight)
            var targetSum = (double)learned["target_sum_mean"];
            var sumDeviation = Math.Abs(combination.Sum() - targetSum);
            var sumScore = Math.Max(0, 100 - sumDeviation * 3); // Stricter penalty
            score += sumScore * 0.15;

            // 4. Optimized Gap Pattern (12%)
            var optimalGap = (double)learned["optimal_gap"];
            var gapScore = CalculateOptimizedGapScore(combination, optimalGap);
            score += gapScore * 0.12;

            // 5. Learned Range Distribution (12%)
            var rangeScore = CalculateLearnedRangeScore(combination, learned);
            score += rangeScore * 0.12;

            // 6. Global Frequency Score (10%)
            var globalFreqs = (Dictionary<int, int>)patterns["global_frequencies"];
            var globalScore = combination.Sum(n => globalFreqs.GetValueOrDefault(n, 0));
            globalScore = (globalScore / combination.Count) / ((int)patterns["total_draws"] / 25) * 100;
            score += Math.Min(100, globalScore) * 0.10;

            // 7. Frequency Stability (8%)
            if (patterns.ContainsKey("frequency_stability"))
            {
                var freqStability = (Dictionary<int, double>)patterns["frequency_stability"];
                var stabilityScore = combination.Average(n => freqStability.GetValueOrDefault(n, 0)) * 10;
                score += Math.Min(100, stabilityScore) * 0.08;
            }
            else
            {
                // Fallback stability calculation
                var fallbackStabilityScore = 50; // Neutral score
                score += fallbackStabilityScore * 0.08;
            }

            // 8. Cyclical Patterns (5%)
            var cyclicalScore = (double)patterns["strongest_correlation"] * 100;
            score += cyclicalScore * 0.05;

            return score;
        }

        private static double CalculateLearnedMathematicalScore(List<int> combination, Dictionary<string, object> learned)
        {
            double score = 0;
            
            // Use actual learned preferences from 3108
            var primePreference = (double)learned["prime_preference"];
            var fibonacciPreference = (double)learned["fibonacci_preference"];
            var squarePreference = (double)learned["perfect_square_preference"];
            
            var primes = new HashSet<int> { 2, 3, 5, 7, 11, 13, 17, 19, 23 };
            var fibonacci = new HashSet<int> { 1, 2, 3, 5, 8, 13, 21 };
            var squares = new HashSet<int> { 1, 4, 9, 16, 25 };

            var primeCount = combination.Count(n => primes.Contains(n));
            var fibCount = combination.Count(n => fibonacci.Contains(n));
            var squareCount = combination.Count(n => squares.Contains(n));

            // Score based on how close we are to learned preferences
            var primeRatio = primeCount / 14.0;
            var fibRatio = fibCount / 14.0;
            var squareRatio = squareCount / 14.0;

            score += (1.0 - Math.Abs(primeRatio - primePreference)) * 50;
            score += (1.0 - Math.Abs(fibRatio - fibonacciPreference)) * 30;
            score += (1.0 - Math.Abs(squareRatio - squarePreference)) * 20;

            return Math.Min(100, score);
        }

        private static double CalculateOptimizedGapScore(List<int> combination, double optimalGap)
        {
            if (combination.Count < 2) return 0;
            
            var sortedCombo = combination.OrderBy(x => x).ToList();
            var gaps = new List<double>();
            
            for (int i = 1; i < sortedCombo.Count; i++)
            {
                gaps.Add(sortedCombo[i] - sortedCombo[i-1]);
            }
            
            var averageGap = gaps.Average();
            var gapDeviation = Math.Abs(averageGap - optimalGap);
            
            return Math.Max(0, 100 - gapDeviation * 100); // Stricter gap penalty
        }

        private static double CalculateLearnedRangeScore(List<int> combination, Dictionary<string, object> learned)
        {
            var lowTarget = (double)learned["low_range_target"];
            var midTarget = (double)learned["mid_range_target"];
            var highTarget = (double)learned["high_range_target"];
            
            var lowCount = combination.Count(n => n <= 8) / 14.0;
            var midCount = combination.Count(n => n >= 9 && n <= 17) / 14.0;
            var highCount = combination.Count(n => n >= 18) / 14.0;
            
            var lowScore = (1.0 - Math.Abs(lowCount - lowTarget)) * 100;
            var midScore = (1.0 - Math.Abs(midCount - midTarget)) * 100;
            var highScore = (1.0 - Math.Abs(highCount - highTarget)) * 100;
            
            return (lowScore + midScore + highScore) / 3.0;
        }

        // Enhanced combination generation based on learned patterns
        public static List<int> GenerateLearnedPatternCombination(Dictionary<string, object> allPatterns, int variation)
        {
            var learned = GetLearnedPatterns();
            var random = new Random(variation + DateTime.Now.Millisecond + 5000);
            var combo = new List<int>();
            
            // Start with super hot numbers (8 out of 14)
            var superHotNumbers = (List<int>)learned["super_hot_numbers"];
            var selectedHot = superHotNumbers.OrderBy(x => random.Next()).Take(8).ToList();
            combo.AddRange(selectedHot);
            
            // Add numbers to achieve target mathematical pattern ratios
            var primePreference = (double)learned["prime_preference"];
            var fibonacciPreference = (double)learned["fibonacci_preference"];
            
            var targetPrimes = (int)(14 * primePreference);
            var targetFibs = (int)(14 * fibonacciPreference);
            
            var primes = new HashSet<int> { 2, 3, 5, 7, 11, 13, 17, 19, 23 };
            var fibonacci = new HashSet<int> { 1, 2, 3, 5, 8, 13, 21 };
            
            var currentPrimes = combo.Count(n => primes.Contains(n));
            var currentFibs = combo.Count(n => fibonacci.Contains(n));
            
            // Add more primes if needed
            while (currentPrimes < targetPrimes && combo.Count < 14)
            {
                var availablePrimes = primes.Where(p => !combo.Contains(p) && p <= 25).ToList();
                if (availablePrimes.Any())
                {
                    var selectedPrime = availablePrimes[random.Next(availablePrimes.Count)];
                    combo.Add(selectedPrime);
                    currentPrimes++;
                }
                else break;
            }
            
            // Add more fibonacci numbers if needed
            while (currentFibs < targetFibs && combo.Count < 14)
            {
                var availableFibs = fibonacci.Where(f => !combo.Contains(f) && f <= 25).ToList();
                if (availableFibs.Any())
                {
                    var selectedFib = availableFibs[random.Next(availableFibs.Count)];
                    combo.Add(selectedFib);
                    currentFibs++;
                }
                else break;
            }
            
            // Fill remaining slots with balanced range distribution
            var allCandidates = Enumerable.Range(1, 25).ToList();
            var remaining = allCandidates.Except(combo).ToList();
            
            while (combo.Count < 14 && remaining.Any())
            {
                // Check current range distribution
                var lowCount = combo.Count(n => n <= 8);
                var midCount = combo.Count(n => n >= 9 && n <= 17);
                var highCount = combo.Count(n => n >= 18);
                
                var lowTarget = (double)learned["low_range_target"] * 14;
                var midTarget = (double)learned["mid_range_target"] * 14;
                var highTarget = (double)learned["high_range_target"] * 14;
                
                List<int> preferredRange;
                if (lowCount < lowTarget)
                    preferredRange = remaining.Where(n => n <= 8).ToList();
                else if (midCount < midTarget)
                    preferredRange = remaining.Where(n => n >= 9 && n <= 17).ToList();
                else if (highCount < highTarget)
                    preferredRange = remaining.Where(n => n >= 18).ToList();
                else
                    preferredRange = remaining;
                
                if (preferredRange.Any())
                {
                    var selected = preferredRange[random.Next(preferredRange.Count)];
                    combo.Add(selected);
                    remaining.Remove(selected);
                }
                else break;
            }
            
            return combo.OrderBy(x => x).Take(14).ToList();
        }
    }
}
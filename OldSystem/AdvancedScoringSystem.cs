using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor
{
    // Advanced scoring system for the enhanced ML model
    public static class AdvancedScoringSystem
    {
        public static double CalculateAdvancedMLScore(
            List<int> combination,
            Dictionary<string, object> globalPatterns,
            Dictionary<string, object> cyclicalPatterns,
            Dictionary<string, object> frequencyPatterns,
            Dictionary<string, object> geometricPatterns,
            Dictionary<string, object> temporalPatterns,
            Dictionary<string, object> mathematicalPatterns,
            Dictionary<int, int> hotNumbers, 
            Dictionary<int, double> trendingNumbers, 
            double targetSum)
        {
            double score = 0.0;
            
            // 1. Global Frequency Score (15%)
            var globalFreqs = (Dictionary<int, int>)globalPatterns["global_frequencies"];
            var globalScore = combination.Sum(n => globalFreqs.GetValueOrDefault(n, 0));
            globalScore = (globalScore / combination.Count) / ((int)globalPatterns["total_draws"] / 25) * 100;
            score += Math.Min(100, globalScore) * 0.15;
            
            // 2. Hot Numbers Score (12%)
            var hotCount = combination.Count(n => hotNumbers.ContainsKey(n));
            var hotScore = (hotCount / 10.0) * 100;
            score += hotScore * 0.12;
            
            // 3. Trend Score (10%)
            var trendScore = combination.Sum(n => Math.Max(0, trendingNumbers.GetValueOrDefault(n, 0))) * 10;
            score += Math.Min(100, trendScore) * 0.10;
            
            // 4. Mathematical Pattern Score (15%)
            var mathScore = CalculateMathematicalPatternScore(combination, mathematicalPatterns);
            score += mathScore * 0.15;
            
            // 5. Geometric Pattern Score (12%)
            var geomScore = CalculateGeometricPatternScore(combination, geometricPatterns);
            score += geomScore * 0.12;
            
            // 6. Frequency Stability Score (10%)
            var freqStability = (Dictionary<int, double>)frequencyPatterns["frequency_stability"];
            var stabilityScore = combination.Average(n => freqStability.GetValueOrDefault(n, 0)) * 10;
            score += Math.Min(100, stabilityScore) * 0.10;
            
            // 7. Cyclical Pattern Score (8%)
            var cyclicalScore = (double)cyclicalPatterns["strongest_correlation"] * 100;
            score += cyclicalScore * 0.08;
            
            // 8. Sum Convergence Score (8%)
            var sumDeviation = Math.Abs(combination.Sum() - targetSum);
            var sumScore = Math.Max(0, 100 - sumDeviation * 2);
            score += sumScore * 0.08;
            
            // 9. Gap Pattern Score (5%)
            var gapScore = CalculateGapScore(combination);
            score += gapScore * 0.05;
            
            // 10. Position Distribution Score (5%)
            var positionScore = CalculatePositionScore(combination);
            score += positionScore * 0.05;
            
            return score;
        }
        
        public static double CalculateMathematicalPatternScore(List<int> combination, Dictionary<string, object> mathPatterns)
        {
            double score = 0;
            
            // Fibonacci bonus
            var fibNumbers = new HashSet<int> { 1, 2, 3, 5, 8, 13, 21 };
            var fibCount = combination.Count(n => fibNumbers.Contains(n));
            score += fibCount * 15;
            
            // Prime number analysis
            var primes = new HashSet<int> { 2, 3, 5, 7, 11, 13, 17, 19, 23 };
            var primeCount = combination.Count(n => primes.Contains(n));
            score += primeCount * 8;
            
            // Perfect squares bonus
            var squares = new HashSet<int> { 1, 4, 9, 16, 25 };
            var squareCount = combination.Count(n => squares.Contains(n));
            score += squareCount * 10;
            
            return Math.Min(100, score);
        }
        
        public static double CalculateGeometricPatternScore(List<int> combination, Dictionary<string, object> geomPatterns)
        {
            double score = 0;
            
            // Sum alignment with historical mean
            var sumMean = (double)geomPatterns["sum_mean"];
            var sumDeviation = Math.Abs(combination.Sum() - sumMean);
            score += Math.Max(0, 100 - sumDeviation);
            
            // Golden ratio alignment
            var goldenRatioScore = (double)geomPatterns["golden_ratio_score"];
            score += goldenRatioScore * 100;
            
            // Range analysis
            var range = combination.Max() - combination.Min();
            var rangeMean = (double)geomPatterns["range_mean"];
            var rangeDeviation = Math.Abs(range - rangeMean);
            score += Math.Max(0, 50 - rangeDeviation);
            
            return Math.Min(100, score / 2.5);
        }

        public static double CalculateGapScore(List<int> combination)
        {
            if (combination.Count < 2) return 0;
            
            var sortedCombo = combination.OrderBy(x => x).ToList();
            var gaps = new List<double>();
            
            for (int i = 1; i < sortedCombo.Count; i++)
            {
                gaps.Add(sortedCombo[i] - sortedCombo[i-1]);
            }
            
            var averageGap = gaps.Average();
            var targetGap = 1.74; // From historical analysis
            var gapDeviation = Math.Abs(averageGap - targetGap);
            
            return Math.Max(0, 100 - gapDeviation * 20);
        }

        public static double CalculatePositionScore(List<int> combination)
        {
            var early = combination.Count(n => n <= 8);
            var middle = combination.Count(n => n >= 9 && n <= 17);
            var late = combination.Count(n => n >= 18);
            
            // Target distribution: 4-6, 3-5, 4-6
            var earlyScore = early >= 4 && early <= 6 ? 100 : Math.Max(0, 100 - Math.Abs(early - 5) * 20);
            var middleScore = middle >= 3 && middle <= 5 ? 100 : Math.Max(0, 100 - Math.Abs(middle - 4) * 20);
            var lateScore = late >= 4 && late <= 6 ? 100 : Math.Max(0, 100 - Math.Abs(late - 5) * 20);
            
            return (earlyScore + middleScore + lateScore) / 3.0;
        }

        public static Dictionary<int, double> GenerateElementScoresFromML(List<int> combination, Dictionary<int, int> hotNumbers)
        {
            var scores = new Dictionary<int, double>();
            var random = new Random();
            
            foreach (var element in combination)
            {
                var baseScore = 0.75;
                if (hotNumbers.ContainsKey(element))
                {
                    baseScore = 0.85 + (hotNumbers[element] / 100.0) * 0.1; // Boost for hot numbers
                }
                scores[element] = Math.Min(0.99, baseScore + (random.NextDouble() * 0.1));
            }
            
            return scores;
        }

        public static double CalculateAverageGap(List<int> combination)
        {
            if (combination.Count < 2) return 0;
            
            var sorted = combination.OrderBy(x => x).ToList();
            var gaps = new List<double>();
            
            for (int i = 1; i < sorted.Count; i++)
            {
                gaps.Add(sorted[i] - sorted[i-1]);
            }
            
            return gaps.Average();
        }
    }
}
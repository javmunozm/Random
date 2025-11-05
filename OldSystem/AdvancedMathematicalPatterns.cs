using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor
{
    // Advanced Mathematical Pattern Analysis Methods
    public static class AdvancedMathematicalPatterns
    {
        // Cyclical Pattern Analysis
        public static Dictionary<string, object> AnalyzeCyclicalPatterns(List<SeriesData> allSeries, int elementRange)
        {
            var patterns = new Dictionary<string, object>();
            var cycleLengths = new List<int> { 3, 5, 7, 10, 12, 15, 20, 25, 30 };
            var bestCycles = new Dictionary<int, double>();
            
            foreach (var cycleLength in cycleLengths)
            {
                var correlation = CalculateCyclicalCorrelation(allSeries, cycleLength, elementRange);
                bestCycles[cycleLength] = correlation;
            }
            
            var strongestCycle = bestCycles.OrderByDescending(kvp => kvp.Value).First();
            
            patterns["cycle_correlations"] = bestCycles;
            patterns["strongest_cycle"] = strongestCycle.Key;
            patterns["strongest_correlation"] = strongestCycle.Value;
            patterns["score"] = strongestCycle.Value * 100;
            
            Console.WriteLine($"Cyclical Analysis: Strongest cycle = {strongestCycle.Key} series (r={strongestCycle.Value:F4})");
            
            return patterns;
        }

        // Advanced Frequency Pattern Analysis
        public static Dictionary<string, object> AnalyzeAdvancedFrequencyPatterns(List<SeriesData> allSeries, int elementRange)
        {
            var patterns = new Dictionary<string, object>();
            
            // Analyze frequency clusters
            var numberFreqs = new Dictionary<int, List<int>>();
            for (int num = 1; num <= elementRange; num++)
            {
                numberFreqs[num] = new List<int>();
            }
            
            // Track frequencies over time windows
            var windowSize = 20;
            for (int i = 0; i <= allSeries.Count - windowSize; i += windowSize / 4)
            {
                var window = allSeries.Skip(i).Take(windowSize).ToList();
                var windowFreqs = new Dictionary<int, int>();
                
                foreach (var series in window)
                {
                    foreach (var element in series.Elements)
                    {
                        windowFreqs[element] = windowFreqs.GetValueOrDefault(element, 0) + 1;
                    }
                }
                
                foreach (var kvp in windowFreqs)
                {
                    numberFreqs[kvp.Key].Add(kvp.Value);
                }
            }
            
            // Calculate frequency stability and patterns
            var frequencyStability = new Dictionary<int, double>();
            var frequencyTrends = new Dictionary<int, double>();
            
            foreach (var kvp in numberFreqs)
            {
                if (kvp.Value.Count > 1)
                {
                    var freqs = kvp.Value;
                    var mean = freqs.Average();
                    var stdDev = Math.Sqrt(freqs.Select(f => Math.Pow(f - mean, 2)).Average());
                    frequencyStability[kvp.Key] = mean / (stdDev + 0.001); // Higher = more stable
                    
                    // Linear trend in frequencies
                    frequencyTrends[kvp.Key] = CalculateLinearTrend(freqs.Select(f => (double)f).ToList());
                }
            }
            
            patterns["frequency_stability"] = frequencyStability;
            patterns["frequency_trends"] = frequencyTrends;
            patterns["most_stable_numbers"] = frequencyStability.OrderByDescending(kvp => kvp.Value).Take(10).ToDictionary(kvp => kvp.Key, kvp => kvp.Value);
            patterns["score"] = frequencyStability.Values.Average();
            
            Console.WriteLine($"Frequency Analysis: Avg stability = {frequencyStability.Values.Average():F3}");
            
            return patterns;
        }

        // Geometric Pattern Analysis
        public static Dictionary<string, object> AnalyzeGeometricPatterns(List<SeriesData> allSeries)
        {
            var patterns = new Dictionary<string, object>();
            
            // Analyze gaps between consecutive numbers
            var allGaps = new List<double>();
            var gapDistribution = new Dictionary<int, int>();
            
            foreach (var series in allSeries)
            {
                var sorted = series.Elements.OrderBy(x => x).ToList();
                for (int i = 1; i < sorted.Count; i++)
                {
                    var gap = sorted[i] - sorted[i - 1];
                    allGaps.Add(gap);
                    gapDistribution[gap] = gapDistribution.GetValueOrDefault(gap, 0) + 1;
                }
            }
            
            // Analyze sum patterns
            var allSums = allSeries.Select(s => s.Elements.Sum()).ToList();
            var sumMean = allSums.Average();
            var sumStdDev = Math.Sqrt(allSums.Select(s => Math.Pow(s - sumMean, 2)).Average());
            
            // Analyze range patterns
            var allRanges = allSeries.Select(s => s.Elements.Max() - s.Elements.Min()).ToList();
            var rangeMean = allRanges.Average();
            
            // Golden ratio analysis
            var goldenRatio = 1.618033988749;
            var goldenRatioScore = CalculateGoldenRatioAlignment(allSeries, goldenRatio);
            
            patterns["gap_distribution"] = gapDistribution;
            patterns["avg_gap"] = allGaps.Average();
            patterns["gap_std_dev"] = Math.Sqrt(allGaps.Select(g => Math.Pow(g - allGaps.Average(), 2)).Average());
            patterns["sum_mean"] = sumMean;
            patterns["sum_std_dev"] = sumStdDev;
            patterns["range_mean"] = rangeMean;
            patterns["golden_ratio_score"] = goldenRatioScore;
            patterns["score"] = (goldenRatioScore + (1.0 / (sumStdDev / sumMean))) * 50;
            
            Console.WriteLine($"Geometric Analysis: Sum μ={sumMean:F1}±{sumStdDev:F1}, Golden ratio score={goldenRatioScore:F4}");
            
            return patterns;
        }

        // Temporal Pattern Analysis
        public static Dictionary<string, object> AnalyzeTemporalPatterns(List<SeriesData> allSeries)
        {
            var patterns = new Dictionary<string, object>();
            
            // Analyze patterns based on series position in sequence
            var positionPatterns = new Dictionary<string, List<double>>();
            
            for (int i = 0; i < allSeries.Count; i++)
            {
                var series = allSeries[i];
                var position = i / (double)allSeries.Count; // 0 to 1
                
                // Track various metrics over time
                if (!positionPatterns.ContainsKey("sums")) positionPatterns["sums"] = new List<double>();
                if (!positionPatterns.ContainsKey("mins")) positionPatterns["mins"] = new List<double>();
                if (!positionPatterns.ContainsKey("maxs")) positionPatterns["maxs"] = new List<double>();
                if (!positionPatterns.ContainsKey("odds")) positionPatterns["odds"] = new List<double>();
                
                positionPatterns["sums"].Add(series.Elements.Sum());
                positionPatterns["mins"].Add(series.Elements.Min());
                positionPatterns["maxs"].Add(series.Elements.Max());
                positionPatterns["odds"].Add(series.Elements.Count(e => e % 2 == 1));
            }
            
            // Calculate temporal trends
            var temporalTrends = new Dictionary<string, double>();
            foreach (var kvp in positionPatterns)
            {
                temporalTrends[kvp.Key] = CalculateLinearTrend(kvp.Value);
            }
            
            patterns["temporal_trends"] = temporalTrends;
            patterns["trend_strength"] = temporalTrends.Values.Select(Math.Abs).Average();
            patterns["score"] = temporalTrends.Values.Select(Math.Abs).Average() * 10;
            
            Console.WriteLine($"Temporal Analysis: Trend strength = {temporalTrends.Values.Select(Math.Abs).Average():F4}");
            
            return patterns;
        }

        // Mathematical Pattern Analysis
        public static Dictionary<string, object> AnalyzeMathematicalPatterns(List<SeriesData> allSeries, int elementRange)
        {
            var patterns = new Dictionary<string, object>();
            
            // Prime number analysis
            var primes = new HashSet<int> { 2, 3, 5, 7, 11, 13, 17, 19, 23 };
            var primeFrequencies = new Dictionary<int, int>();
            var nonPrimeFrequencies = new Dictionary<int, int>();
            
            // Fibonacci analysis
            var fibonacciNumbers = new HashSet<int> { 1, 2, 3, 5, 8, 13, 21 };
            var fibonacciScore = 0.0;
            
            // Perfect squares analysis
            var perfectSquares = new HashSet<int> { 1, 4, 9, 16, 25 };
            var perfectSquareScore = 0.0;
            
            foreach (var series in allSeries)
            {
                var primeCount = series.Elements.Count(e => primes.Contains(e));
                var fibCount = series.Elements.Count(e => fibonacciNumbers.Contains(e));
                var squareCount = series.Elements.Count(e => perfectSquares.Contains(e));
                
                fibonacciScore += fibCount / (double)series.Elements.Count;
                perfectSquareScore += squareCount / (double)series.Elements.Count;
                
                foreach (var element in series.Elements)
                {
                    if (primes.Contains(element))
                        primeFrequencies[element] = primeFrequencies.GetValueOrDefault(element, 0) + 1;
                    else
                        nonPrimeFrequencies[element] = nonPrimeFrequencies.GetValueOrDefault(element, 0) + 1;
                }
            }
            
            fibonacciScore /= allSeries.Count;
            perfectSquareScore /= allSeries.Count;
            
            // Modular arithmetic patterns
            var modularPatterns = new Dictionary<int, Dictionary<int, int>>();
            var moduli = new List<int> { 3, 5, 7, 11 };
            
            foreach (var mod in moduli)
            {
                modularPatterns[mod] = new Dictionary<int, int>();
                foreach (var series in allSeries)
                {
                    foreach (var element in series.Elements)
                    {
                        var remainder = element % mod;
                        modularPatterns[mod][remainder] = modularPatterns[mod].GetValueOrDefault(remainder, 0) + 1;
                    }
                }
            }
            
            patterns["prime_frequencies"] = primeFrequencies;
            patterns["fibonacci_score"] = fibonacciScore;
            patterns["perfect_square_score"] = perfectSquareScore;
            patterns["modular_patterns"] = modularPatterns;
            patterns["score"] = (fibonacciScore + perfectSquareScore) * 100;
            
            Console.WriteLine($"Mathematical Analysis: Fibonacci score={fibonacciScore:F4}, Perfect square score={perfectSquareScore:F4}");
            
            return patterns;
        }

        // Helper Methods
        private static double CalculateGlobalPatternScore(Dictionary<int, int> frequencies, double mean, double stdDev, double entropy, int elementRange)
        {
            var normalizedEntropy = entropy / Math.Log(elementRange, 2); // Normalize to 0-1
            var coefficientOfVariation = stdDev / mean;
            return (normalizedEntropy * 0.6 + (1.0 / coefficientOfVariation) * 0.4) * 100;
        }

        private static double CalculateCyclicalCorrelation(List<SeriesData> allSeries, int cycleLength, int elementRange)
        {
            if (allSeries.Count < cycleLength * 2) return 0;
            
            var correlations = new List<double>();
            
            for (int num = 1; num <= elementRange; num++)
            {
                var sequence = new List<int>();
                foreach (var series in allSeries)
                {
                    sequence.Add(series.Elements.Contains(num) ? 1 : 0);
                }
                
                if (sequence.Count >= cycleLength * 2)
                {
                    var firstCycle = sequence.Take(cycleLength).ToList();
                    var correlation = 0.0;
                    var cycles = 0;
                    
                    for (int start = cycleLength; start <= sequence.Count - cycleLength; start += cycleLength)
                    {
                        var currentCycle = sequence.Skip(start).Take(cycleLength).ToList();
                        correlation += CalculateCorrelation(firstCycle, currentCycle);
                        cycles++;
                    }
                    
                    if (cycles > 0)
                        correlations.Add(correlation / cycles);
                }
            }
            
            return correlations.Count > 0 ? correlations.Average() : 0;
        }

        private static double CalculateCorrelation(List<int> x, List<int> y)
        {
            if (x.Count != y.Count || x.Count == 0) return 0;
            
            var meanX = x.Average();
            var meanY = y.Average();
            
            var numerator = x.Zip(y, (xi, yi) => (xi - meanX) * (yi - meanY)).Sum();
            var denomX = Math.Sqrt(x.Sum(xi => Math.Pow(xi - meanX, 2)));
            var denomY = Math.Sqrt(y.Sum(yi => Math.Pow(yi - meanY, 2)));
            
            return denomX * denomY == 0 ? 0 : numerator / (denomX * denomY);
        }

        private static double CalculateGoldenRatioAlignment(List<SeriesData> allSeries, double goldenRatio)
        {
            var alignmentScores = new List<double>();
            
            foreach (var series in allSeries)
            {
                var sorted = series.Elements.OrderBy(x => x).ToList();
                var ratios = new List<double>();
                
                for (int i = 1; i < sorted.Count; i++)
                {
                    if (sorted[i - 1] != 0)
                    {
                        ratios.Add(sorted[i] / (double)sorted[i - 1]);
                    }
                }
                
                if (ratios.Count > 0)
                {
                    var avgRatio = ratios.Average();
                    var alignment = 1.0 / (1.0 + Math.Abs(avgRatio - goldenRatio));
                    alignmentScores.Add(alignment);
                }
            }
            
            return alignmentScores.Count > 0 ? alignmentScores.Average() : 0;
        }

        private static double CalculateLinearTrend(List<double> values)
        {
            if (values == null || values.Count < 2) return 0;

            var n = values.Count;
            var xSum = (n * (n - 1)) / 2.0;
            var xSquaredSum = (n * (n - 1) * (2 * n - 1)) / 6.0;
            var ySum = values.Sum();
            var xySum = values.Select((value, index) => value * index).Sum();

            var denominator = n * xSquaredSum - xSum * xSum;
            if (Math.Abs(denominator) < 1e-10) return 0;

            var slope = (n * xySum - xSum * ySum) / denominator;
            return slope;
        }
    }
}
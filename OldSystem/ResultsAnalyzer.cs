using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor
{
    public static class ResultsAnalyzer
    {
        public static void AnalyzePredictionAccuracy()
        {
            // Actual 3108 results
            var actual3108 = new List<List<int>>
            {
                new List<int> { 01, 02, 04, 05, 08, 10, 12, 13, 14, 15, 17, 18, 21, 22 },
                new List<int> { 01, 03, 06, 07, 09, 10, 11, 13, 19, 20, 21, 22, 23, 24 },
                new List<int> { 03, 04, 05, 06, 09, 12, 13, 14, 16, 18, 19, 20, 22, 25 },
                new List<int> { 01, 03, 04, 06, 07, 09, 12, 15, 16, 18, 19, 21, 22, 23 },
                new List<int> { 02, 03, 06, 07, 12, 13, 14, 15, 16, 17, 19, 22, 23, 24 },
                new List<int> { 01, 03, 05, 06, 10, 11, 12, 15, 17, 19, 20, 21, 23, 24 },
                new List<int> { 01, 02, 03, 04, 05, 09, 10, 13, 14, 16, 18, 19, 22, 23 }
            };

            // My recent predictions (example from last run)
            var predicted3108 = new List<List<int>>
            {
                new List<int> { 01, 03, 06, 10, 11, 12, 13, 15, 16, 18, 19, 20, 22, 25 },
                new List<int> { 01, 02, 03, 09, 10, 11, 12, 16, 18, 19, 20, 22, 23, 25 },
                new List<int> { 01, 03, 05, 06, 09, 10, 11, 16, 19, 20, 21, 22, 23, 25 },
                new List<int> { 01, 02, 03, 06, 07, 08, 09, 10, 11, 15, 19, 20, 21, 24 },
                new List<int> { 01, 03, 04, 05, 07, 08, 09, 13, 16, 17, 19, 21, 22, 23 },
                new List<int> { 02, 03, 05, 06, 10, 13, 15, 16, 17, 19, 20, 21, 23, 25 },
                new List<int> { 02, 04, 05, 06, 09, 11, 14, 17, 18, 19, 20, 21, 23, 25 }
            };

            Console.WriteLine("=== SERIES 3108 PREDICTION ANALYSIS ===\n");

            // Calculate overall accuracy metrics
            var allActualNumbers = actual3108.SelectMany(x => x).ToHashSet();
            var allPredictedNumbers = predicted3108.SelectMany(x => x).ToHashSet();
            var commonNumbers = allActualNumbers.Intersect(allPredictedNumbers).ToList();

            Console.WriteLine($"Numbers appearing in actual results: {allActualNumbers.Count}");
            Console.WriteLine($"Numbers appearing in predictions: {allPredictedNumbers.Count}");
            Console.WriteLine($"Common numbers: {commonNumbers.Count}");
            Console.WriteLine($"Overall accuracy: {(double)commonNumbers.Count / allActualNumbers.Count:P2}");
            Console.WriteLine($"Common numbers: {string.Join(", ", commonNumbers.OrderBy(x => x).Select(x => x.ToString("D2")))}");
            Console.WriteLine();

            // Analyze what I missed
            var missedNumbers = allActualNumbers.Except(allPredictedNumbers).ToList();
            var wrongNumbers = allPredictedNumbers.Except(allActualNumbers).ToList();

            Console.WriteLine($"Numbers I MISSED: {string.Join(", ", missedNumbers.OrderBy(x => x).Select(x => x.ToString("D2")))}");
            Console.WriteLine($"Numbers I predicted WRONGLY: {string.Join(", ", wrongNumbers.OrderBy(x => x).Select(x => x.ToString("D2")))}");
            Console.WriteLine();

            // Individual combination analysis
            Console.WriteLine("=== COMBINATION-BY-COMBINATION ANALYSIS ===");
            for (int i = 0; i < actual3108.Count; i++)
            {
                var actual = actual3108[i];
                var predicted = predicted3108[i];
                var matches = actual.Intersect(predicted).Count();
                var accuracy = (double)matches / actual.Count;

                Console.WriteLine($"Combo {i + 1}: {matches}/14 matches ({accuracy:P1})");
                Console.WriteLine($"  Actual:    {string.Join(" ", actual.Select(x => x.ToString("D2")))}");
                Console.WriteLine($"  Predicted: {string.Join(" ", predicted.Select(x => x.ToString("D2")))}");
                Console.WriteLine($"  Matches:   {string.Join(" ", actual.Intersect(predicted).Select(x => x.ToString("D2")))}");
                Console.WriteLine();
            }

            AnalyzePatterns(actual3108);
        }

        private static void AnalyzePatterns(List<List<int>> actual3108)
        {
            Console.WriteLine("=== PATTERN ANALYSIS OF ACTUAL 3108 RESULTS ===");

            // Frequency analysis
            var frequencyMap = new Dictionary<int, int>();
            foreach (var combo in actual3108)
            {
                foreach (var num in combo)
                {
                    frequencyMap[num] = frequencyMap.GetValueOrDefault(num, 0) + 1;
                }
            }

            var hotNumbers = frequencyMap.Where(kvp => kvp.Value >= 3)
                .OrderByDescending(kvp => kvp.Value)
                .ToDictionary(kvp => kvp.Key, kvp => kvp.Value);

            Console.WriteLine("Hot numbers in actual 3108 (appearing 3+ times):");
            foreach (var kvp in hotNumbers)
            {
                Console.WriteLine($"  {kvp.Key:D2}: {kvp.Value} times");
            }
            Console.WriteLine();

            // Sum analysis
            var sums = actual3108.Select(combo => combo.Sum()).ToList();
            Console.WriteLine($"Sum analysis:");
            Console.WriteLine($"  Average sum: {sums.Average():F1}");
            Console.WriteLine($"  Min sum: {sums.Min()}");
            Console.WriteLine($"  Max sum: {sums.Max()}");
            Console.WriteLine($"  Sum range: {sums.Max() - sums.Min()}");
            Console.WriteLine($"  All sums: {string.Join(", ", sums)}");
            Console.WriteLine();

            // Gap analysis
            var allGaps = new List<double>();
            foreach (var combo in actual3108)
            {
                var sorted = combo.OrderBy(x => x).ToList();
                var gaps = new List<double>();
                for (int i = 1; i < sorted.Count; i++)
                {
                    gaps.Add(sorted[i] - sorted[i - 1]);
                }
                allGaps.AddRange(gaps);
                Console.WriteLine($"  Gaps for {string.Join(" ", sorted.Select(x => x.ToString("D2")))}: avg={gaps.Average():F2}");
            }
            Console.WriteLine($"Overall average gap: {allGaps.Average():F2}");
            Console.WriteLine();

            // Mathematical patterns
            var primes = new HashSet<int> { 2, 3, 5, 7, 11, 13, 17, 19, 23 };
            var fibonacci = new HashSet<int> { 1, 2, 3, 5, 8, 13, 21 };
            var squares = new HashSet<int> { 1, 4, 9, 16, 25 };

            var primeCount = actual3108.Sum(combo => combo.Count(n => primes.Contains(n)));
            var fibCount = actual3108.Sum(combo => combo.Count(n => fibonacci.Contains(n)));
            var squareCount = actual3108.Sum(combo => combo.Count(n => squares.Contains(n)));

            Console.WriteLine($"Mathematical patterns:");
            Console.WriteLine($"  Prime numbers: {primeCount} total ({primeCount / (double)(actual3108.Count * 14):P1})");
            Console.WriteLine($"  Fibonacci numbers: {fibCount} total ({fibCount / (double)(actual3108.Count * 14):P1})");
            Console.WriteLine($"  Perfect squares: {squareCount} total ({squareCount / (double)(actual3108.Count * 14):P1})");
            Console.WriteLine();

            // Range distribution
            var lowCount = actual3108.Sum(combo => combo.Count(n => n <= 8));
            var midCount = actual3108.Sum(combo => combo.Count(n => n >= 9 && n <= 17));
            var highCount = actual3108.Sum(combo => combo.Count(n => n >= 18));

            Console.WriteLine($"Range distribution:");
            Console.WriteLine($"  Low (1-8): {lowCount} ({lowCount / (double)(actual3108.Count * 14):P1})");
            Console.WriteLine($"  Mid (9-17): {midCount} ({midCount / (double)(actual3108.Count * 14):P1})");
            Console.WriteLine($"  High (18-25): {highCount} ({highCount / (double)(actual3108.Count * 14):P1})");
        }

        public static List<List<int>> GetActual3108Results()
        {
            return new List<List<int>>
            {
                new List<int> { 01, 02, 04, 05, 08, 10, 12, 13, 14, 15, 17, 18, 21, 22 },
                new List<int> { 01, 03, 06, 07, 09, 10, 11, 13, 19, 20, 21, 22, 23, 24 },
                new List<int> { 03, 04, 05, 06, 09, 12, 13, 14, 16, 18, 19, 20, 22, 25 },
                new List<int> { 01, 03, 04, 06, 07, 09, 12, 15, 16, 18, 19, 21, 22, 23 },
                new List<int> { 02, 03, 06, 07, 12, 13, 14, 15, 16, 17, 19, 22, 23, 24 },
                new List<int> { 01, 03, 05, 06, 10, 11, 12, 15, 17, 19, 20, 21, 23, 24 },
                new List<int> { 01, 02, 03, 04, 05, 09, 10, 13, 14, 16, 18, 19, 22, 23 }
            };
        }
    }
}
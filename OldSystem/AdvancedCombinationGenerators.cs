using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor
{
    // Advanced combination generation methods for the enhanced ML model
    public static class AdvancedCombinationGenerators
    {
        public static List<int> GenerateGlobalFrequencyOptimizedCombination(Dictionary<int, int> globalFreqs, List<int> allCandidates, int variation)
        {
            var random = new Random(variation + DateTime.Now.Millisecond);
            var combo = new List<int>();
            
            // Select top frequency numbers with some randomization
            var topFreqNumbers = globalFreqs.OrderByDescending(kvp => kvp.Value)
                .Take(20) // Top 20 most frequent
                .OrderBy(x => random.Next())
                .Take(10 + variation) // Select 10-12 of them
                .Select(kvp => kvp.Key)
                .ToList();
            
            combo.AddRange(topFreqNumbers);
            
            // Fill remaining slots with weighted random selection
            var remaining = allCandidates.Except(combo)
                .OrderBy(n => random.NextDouble() / Math.Max(1, globalFreqs.GetValueOrDefault(n, 1)))
                .Take(14 - combo.Count)
                .ToList();
            combo.AddRange(remaining);
            
            return combo.OrderBy(x => x).Take(14).ToList();
        }
        
        public static List<int> GenerateMathematicalPatternCombination(Dictionary<string, object> mathPatterns, List<int> allCandidates, int variation)
        {
            var random = new Random(variation + DateTime.Now.Millisecond + 500);
            var combo = new List<int>();
            
            // Include mathematical special numbers
            var fibNumbers = new List<int> { 1, 2, 3, 5, 8, 13, 21 }.Where(n => n <= 25).ToList();
            var primes = new List<int> { 2, 3, 5, 7, 11, 13, 17, 19, 23 }.Where(n => n <= 25).ToList();
            var squares = new List<int> { 1, 4, 9, 16, 25 }.Where(n => n <= 25).ToList();
            
            // Select some from each category
            combo.AddRange(fibNumbers.OrderBy(x => random.Next()).Take(2 + variation));
            combo.AddRange(primes.Except(combo).OrderBy(x => random.Next()).Take(3));
            combo.AddRange(squares.Except(combo).OrderBy(x => random.Next()).Take(2));
            
            // Fill remaining with regular numbers
            var remaining = allCandidates.Except(combo)
                .OrderBy(x => random.Next())
                .Take(14 - combo.Count)
                .ToList();
            combo.AddRange(remaining);
            
            return combo.OrderBy(x => x).Take(14).ToList();
        }
        
        public static List<int> GenerateStabilityBasedCombination(List<int> mostStable, List<int> hotNumbers, List<int> allCandidates, int variation)
        {
            var random = new Random(variation + DateTime.Now.Millisecond + 1000);
            var combo = new List<int>();
            
            // Select from most stable numbers
            var selectedStable = mostStable.OrderBy(x => random.Next()).Take(8).ToList();
            combo.AddRange(selectedStable);
            
            // Add some hot numbers
            var selectedHot = hotNumbers.Except(combo).OrderBy(x => random.Next()).Take(3).ToList();
            combo.AddRange(selectedHot);
            
            // Fill remaining
            var remaining = allCandidates.Except(combo)
                .OrderBy(x => random.Next())
                .Take(14 - combo.Count)
                .ToList();
            combo.AddRange(remaining);
            
            return combo.OrderBy(x => x).Take(14).ToList();
        }
        
        public static List<int> GenerateGeometricPatternCombination(Dictionary<string, object> geomPatterns, List<int> allCandidates)
        {
            var random = new Random(DateTime.Now.Millisecond + 1500);
            var combo = new List<int>();
            
            // Target sum from patterns
            var targetSum = (double)geomPatterns["sum_mean"];
            
            // Generate numbers that sum close to target
            var currentSum = 0;
            var used = new HashSet<int>();
            
            while (combo.Count < 14 && used.Count < 25)
            {
                var remaining = 14 - combo.Count;
                var neededSum = targetSum - currentSum;
                var avgNeeded = remaining > 0 ? neededSum / remaining : 0;
                
                // Find number close to avgNeeded
                var candidate = allCandidates
                    .Where(n => !used.Contains(n))
                    .OrderBy(n => Math.Abs(n - avgNeeded))
                    .FirstOrDefault();
                
                if (candidate > 0)
                {
                    combo.Add(candidate);
                    used.Add(candidate);
                    currentSum += candidate;
                }
                else
                {
                    // Fallback: random selection
                    var fallback = allCandidates.Where(n => !used.Contains(n)).OrderBy(x => random.Next()).FirstOrDefault();
                    if (fallback > 0)
                    {
                        combo.Add(fallback);
                        used.Add(fallback);
                        currentSum += fallback;
                    }
                    else break;
                }
            }
            
            return combo.OrderBy(x => x).ToList();
        }
        
        public static List<int> GenerateHybridPatternCombination(Dictionary<int, int> globalFreqs, List<int> mostStable, List<int> hotNumbers, List<int> trendingUp, List<int> allCandidates)
        {
            var random = new Random(DateTime.Now.Millisecond + 2000);
            var combo = new List<int>();
            
            // Weighted selection from all pattern sources
            var candidates = new Dictionary<int, double>();
            
            foreach (var num in allCandidates)
            {
                double weight = 1.0;
                
                // Global frequency weight
                if (globalFreqs.ContainsKey(num))
                    weight += globalFreqs[num] * 0.001;
                    
                // Stability weight
                if (mostStable.Contains(num))
                    weight += 0.5;
                    
                // Hot number weight
                if (hotNumbers.Contains(num))
                    weight += 0.3;
                    
                // Trending weight
                if (trendingUp.Contains(num))
                    weight += 0.2;
                    
                candidates[num] = weight;
            }
            
            // Select numbers based on weighted probabilities
            var totalWeight = candidates.Values.Sum();
            var selected = new HashSet<int>();
            
            while (combo.Count < 14 && selected.Count < 25)
            {
                var target = random.NextDouble() * totalWeight;
                var cumulative = 0.0;
                
                foreach (var kvp in candidates.OrderByDescending(c => c.Value))
                {
                    if (selected.Contains(kvp.Key)) continue;
                    
                    cumulative += kvp.Value;
                    if (cumulative >= target)
                    {
                        combo.Add(kvp.Key);
                        selected.Add(kvp.Key);
                        totalWeight -= kvp.Value; // Remove from pool
                        break;
                    }
                }
                
                // Safety check to prevent infinite loop
                if (combo.Count == 0 && selected.Count > 0) break;
            }
            
            // Fill any remaining slots
            while (combo.Count < 14)
            {
                var remaining = allCandidates.Except(combo).FirstOrDefault();
                if (remaining == 0) break;
                combo.Add(remaining);
            }
            
            return combo.OrderBy(x => x).Take(14).ToList();
        }
    }
}
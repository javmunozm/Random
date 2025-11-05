using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.IO;

namespace DataProcessor.Models
{
    public class ModelCheckpoint
    {
        public int Generation { get; set; }
        public DateTime Timestamp { get; set; }
        public Dictionary<int, double> NumberWeights { get; set; } = new();
        public Dictionary<string, double> PatternWeights { get; set; } = new();
        public double LearningRate { get; set; }
        public List<PerformanceMetric> PerformanceHistory { get; set; } = new();
        public int TotalSeriesTrained { get; set; }
    }

    public class PerformanceMetric
    {
        public int SeriesId { get; set; }
        public double BestAccuracy { get; set; }
        public double AverageAccuracy { get; set; }
        public List<int> CriticalNumbersMissed { get; set; } = new();
        public List<int> CriticalNumbersHit { get; set; } = new();
    }

    public class EvolutionaryModel
    {
        private LearningWeights weights;
        private readonly List<SeriesPattern> trainingData;
        private readonly Random random = new();
        private readonly UniquenessValidator uniquenessValidator;
        private readonly List<PerformanceMetric> performanceHistory;
        private int generation;
        private readonly string checkpointPath;

        public EvolutionaryModel(string checkpointPath = "Models/evolution_checkpoint.json")
        {
            this.checkpointPath = checkpointPath;
            trainingData = new List<SeriesPattern>();
            performanceHistory = new List<PerformanceMetric>();
            uniquenessValidator = new UniquenessValidator(151);

            // Try to load existing checkpoint
            if (File.Exists(checkpointPath))
            {
                LoadCheckpoint();
                Console.WriteLine($"✅ Loaded checkpoint: Generation {generation}, {trainingData.Count} series trained");
            }
            else
            {
                weights = new LearningWeights();
                generation = 0;
                InitializeWeights();
                Console.WriteLine("🆕 New model initialized - Generation 0");
            }
        }

        private void InitializeWeights()
        {
            for (int i = 1; i <= 25; i++)
            {
                weights.NumberFrequencyWeights[i] = 1.0;
                weights.PositionWeights[i] = 1.0;
            }

            weights.PatternWeights["consecutive"] = 0.3;
            weights.PatternWeights["sum_range"] = 0.3;
            weights.PatternWeights["distribution"] = 0.2;
            weights.PatternWeights["high_numbers"] = 0.2;
            weights.LearningRate = 0.1;
        }

        public void LoadCheckpoint()
        {
            try
            {
                var json = File.ReadAllText(checkpointPath);
                var checkpoint = JsonSerializer.Deserialize<ModelCheckpoint>(json);

                if (checkpoint != null)
                {
                    weights = new LearningWeights
                    {
                        NumberFrequencyWeights = checkpoint.NumberWeights,
                        PatternWeights = checkpoint.PatternWeights,
                        LearningRate = checkpoint.LearningRate
                    };

                    // Initialize PositionWeights (not saved in checkpoint)
                    for (int i = 1; i <= 25; i++)
                    {
                        weights.PositionWeights[i] = 1.0;
                    }

                    generation = checkpoint.Generation;
                    performanceHistory.AddRange(checkpoint.PerformanceHistory);

                    Console.WriteLine($"📊 Checkpoint loaded:");
                    Console.WriteLine($"   Generation: {generation}");
                    Console.WriteLine($"   Series trained: {checkpoint.TotalSeriesTrained}");
                    Console.WriteLine($"   Learning rate: {checkpoint.LearningRate}");

                    if (performanceHistory.Any())
                    {
                        var avgPerf = performanceHistory.Average(p => p.BestAccuracy);
                        Console.WriteLine($"   Historical avg accuracy: {avgPerf:P1}");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️  Error loading checkpoint: {ex.Message}");
                InitializeWeights();
            }
        }

        public void SaveCheckpoint()
        {
            try
            {
                var checkpoint = new ModelCheckpoint
                {
                    Generation = generation,
                    Timestamp = DateTime.Now,
                    NumberWeights = weights.NumberFrequencyWeights,
                    PatternWeights = weights.PatternWeights,
                    LearningRate = weights.LearningRate,
                    PerformanceHistory = performanceHistory,
                    TotalSeriesTrained = trainingData.Count
                };

                var options = new JsonSerializerOptions { WriteIndented = true };
                var json = JsonSerializer.Serialize(checkpoint, options);

                Directory.CreateDirectory(Path.GetDirectoryName(checkpointPath) ?? "Models");
                File.WriteAllText(checkpointPath, json);

                Console.WriteLine($"💾 Checkpoint saved: Generation {generation}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠️  Error saving checkpoint: {ex.Message}");
            }
        }

        public void Evolve(SeriesPattern pattern)
        {
            trainingData.Add(pattern);
            UpdateWeights(pattern);
            generation++;
        }

        private void UpdateWeights(SeriesPattern pattern)
        {
            // Multi-event frequency analysis
            var allNumbersInSeries = new Dictionary<int, int>();
            var eventCount = pattern.Combinations.Count;

            foreach (var combination in pattern.Combinations)
            {
                foreach (var number in combination)
                {
                    allNumbersInSeries[number] = allNumbersInSeries.GetValueOrDefault(number) + 1;
                }
            }

            // Adaptive learning based on frequency
            foreach (var kvp in allNumbersInSeries)
            {
                var frequency = kvp.Value / (double)eventCount;
                var boost = frequency >= 0.7 ? 2.0 : (frequency >= 0.5 ? 1.5 : 0.5);
                weights.NumberFrequencyWeights[kvp.Key] += weights.LearningRate * boost;
            }

            // Pattern learning
            foreach (var combination in pattern.Combinations)
            {
                for (int pos = 0; pos < combination.Count; pos++)
                {
                    weights.PositionWeights[combination[pos]] += weights.LearningRate * 0.5;
                }

                var consecutiveCount = CountConsecutive(combination);
                var sum = combination.Sum();
                var distribution = CalculateDistribution(combination);

                if (consecutiveCount > 1 && consecutiveCount <= 3)
                    weights.PatternWeights["consecutive"] += weights.LearningRate * 0.7;

                if (sum >= 160 && sum <= 240)
                    weights.PatternWeights["sum_range"] += weights.LearningRate;

                if (distribution > 0.6)
                    weights.PatternWeights["distribution"] += weights.LearningRate;
            }

            LearnPairAffinities(pattern.Combinations);
        }

        private void LearnPairAffinities(List<List<int>> combinations)
        {
            if (!weights.PatternWeights.ContainsKey("pair_affinity"))
                weights.PatternWeights["pair_affinity"] = 0.0;

            var pairCounts = new Dictionary<string, int>();

            foreach (var combo in combinations)
            {
                for (int i = 0; i < combo.Count; i++)
                {
                    for (int j = i + 1; j < combo.Count; j++)
                    {
                        var pair = $"{Math.Min(combo[i], combo[j])}-{Math.Max(combo[i], combo[j])}";
                        pairCounts[pair] = pairCounts.GetValueOrDefault(pair) + 1;
                    }
                }
            }

            var strongPairs = pairCounts.Where(p => p.Value >= combinations.Count * 0.5).Count();
            if (strongPairs > 0)
            {
                weights.PatternWeights["pair_affinity"] += weights.LearningRate * strongPairs * 0.1;
            }
        }

        public List<int> Predict(int targetSeriesId)
        {
            var candidates = GenerateCandidates(targetSeriesId);
            var scored = candidates.Select(c => new PredictionCandidate
            {
                Numbers = c,
                Score = CalculateScore(c)
            }).OrderByDescending(p => p.Score).ToList();

            return scored.First().Numbers;
        }

        private List<List<int>> GenerateCandidates(int targetSeriesId)
        {
            var candidates = new List<List<int>>();

            for (int attempt = 0; attempt < 2000; attempt++)
            {
                var candidate = GenerateWeightedCandidate();
                if (IsValidCombination(candidate) && uniquenessValidator.IsUniqueCombination(candidate, targetSeriesId))
                {
                    candidates.Add(candidate);
                }
            }

            return candidates.Take(100).ToList();
        }

        private List<int> GenerateWeightedCandidate()
        {
            var numbers = new List<int>();
            var used = new HashSet<int>();

            while (numbers.Count < 14)
            {
                var number = SelectWeightedNumber(used);
                if (!used.Contains(number))
                {
                    numbers.Add(number);
                    used.Add(number);
                }
            }

            numbers.Sort();
            return numbers;
        }

        private int SelectWeightedNumber(HashSet<int> used)
        {
            var totalWeight = 0.0;
            for (int i = 1; i <= 25; i++)
            {
                if (!used.Contains(i))
                    totalWeight += weights.NumberFrequencyWeights[i] * weights.PositionWeights[i];
            }

            var randomValue = random.NextDouble() * totalWeight;
            var currentWeight = 0.0;

            for (int i = 1; i <= 25; i++)
            {
                if (!used.Contains(i))
                {
                    currentWeight += weights.NumberFrequencyWeights[i] * weights.PositionWeights[i];
                    if (currentWeight >= randomValue)
                        return i;
                }
            }

            return Enumerable.Range(1, 25).Where(x => !used.Contains(x)).OrderBy(x => random.Next()).First();
        }

        private double CalculateScore(List<int> combination)
        {
            var score = 0.0;

            foreach (var number in combination)
            {
                score += weights.NumberFrequencyWeights[number];
            }

            var consecutiveCount = CountConsecutive(combination);
            var sum = combination.Sum();
            var distribution = CalculateDistribution(combination);

            score += consecutiveCount * weights.PatternWeights["consecutive"];

            if (sum >= 160 && sum <= 240)
                score += weights.PatternWeights["sum_range"];

            score += distribution * weights.PatternWeights["distribution"];

            return score;
        }

        public void ValidateAndEvolve(int seriesId, List<int> prediction, List<List<int>> actualResults)
        {
            var bestMatch = actualResults.OrderByDescending(actual => prediction.Intersect(actual).Count()).First();
            var accuracy = (double)prediction.Intersect(bestMatch).Count() / 14.0;

            // Analyze critical numbers
            var numberFrequencyInSeries = new Dictionary<int, int>();
            foreach (var actualEvent in actualResults)
            {
                foreach (var num in actualEvent)
                {
                    numberFrequencyInSeries[num] = numberFrequencyInSeries.GetValueOrDefault(num) + 1;
                }
            }

            var criticalNumbers = numberFrequencyInSeries.Where(kvp => kvp.Value >= 5).Select(kvp => kvp.Key).ToList();
            var criticalMissed = criticalNumbers.Where(n => !prediction.Contains(n)).ToList();
            var criticalHit = criticalNumbers.Where(n => prediction.Contains(n)).ToList();

            // Record performance
            var metric = new PerformanceMetric
            {
                SeriesId = seriesId,
                BestAccuracy = accuracy,
                AverageAccuracy = actualResults.Average(a => (double)prediction.Intersect(a).Count() / 14.0),
                CriticalNumbersMissed = criticalMissed,
                CriticalNumbersHit = criticalHit
            };
            performanceHistory.Add(metric);

            Console.WriteLine($"📊 Evolution Step {generation}: Series {seriesId}");
            Console.WriteLine($"   Accuracy: {accuracy:P1} ({prediction.Intersect(bestMatch).Count()}/14)");
            Console.WriteLine($"   Critical hit: {criticalHit.Count}/{criticalNumbers.Count}");

            // EVOLVE: Penalize mistakes heavily
            var correctionFactor = accuracy < 0.5 ? 0.2 : 0.1;

            foreach (var criticalNum in criticalMissed)
            {
                weights.NumberFrequencyWeights[criticalNum] *= (1.0 + correctionFactor * 4.0);
                Console.WriteLine($"   ⚠️  Boosting critical #{criticalNum:D2} (missed, freq: {numberFrequencyInSeries[criticalNum]}/7)");
            }

            foreach (var number in prediction.Except(bestMatch))
            {
                if (numberFrequencyInSeries.GetValueOrDefault(number) >= 3)
                {
                    weights.NumberFrequencyWeights[number] *= (1.0 - correctionFactor * 0.3);
                }
                else
                {
                    weights.NumberFrequencyWeights[number] *= (1.0 - correctionFactor);
                }
            }

            foreach (var number in bestMatch.Except(prediction))
            {
                var boost = numberFrequencyInSeries.GetValueOrDefault(number) >= 4 ? 3.0 : 1.5;
                weights.NumberFrequencyWeights[number] *= (1.0 + correctionFactor * boost);
            }

            foreach (var number in prediction.Intersect(bestMatch))
            {
                var boost = numberFrequencyInSeries.GetValueOrDefault(number) >= 4 ? 1.5 : 0.8;
                weights.NumberFrequencyWeights[number] *= (1.0 + correctionFactor * boost);
            }

            // Adapt learning rate based on performance
            if (performanceHistory.Count >= 5)
            {
                var recent5 = performanceHistory.TakeLast(5).Average(p => p.BestAccuracy);
                var previous5 = performanceHistory.Count >= 10
                    ? performanceHistory.Skip(performanceHistory.Count - 10).Take(5).Average(p => p.BestAccuracy)
                    : recent5;

                if (recent5 > previous5)
                {
                    weights.LearningRate = Math.Min(0.25, weights.LearningRate * 1.05);
                    Console.WriteLine($"   📈 Performance improving - LR increased to {weights.LearningRate:F3}");
                }
                else if (recent5 < previous5)
                {
                    weights.LearningRate = Math.Max(0.05, weights.LearningRate * 0.95);
                    Console.WriteLine($"   📉 Performance declining - LR decreased to {weights.LearningRate:F3}");
                }
            }

            // Learn from actual patterns
            var actualPattern = new SeriesPattern
            {
                SeriesId = seriesId,
                Combinations = actualResults
            };
            Evolve(actualPattern);

            Console.WriteLine($"   ✅ Model evolved to Generation {generation}");
        }

        private int CountConsecutive(List<int> numbers)
        {
            var consecutive = 0;
            for (int i = 1; i < numbers.Count; i++)
            {
                if (numbers[i] == numbers[i-1] + 1)
                    consecutive++;
            }
            return consecutive;
        }

        private double CalculateDistribution(List<int> numbers)
        {
            var ranges = new int[5];
            foreach (var num in numbers)
            {
                ranges[(num - 1) / 5]++;
            }

            var nonZeroRanges = ranges.Count(r => r > 0);
            return (double)nonZeroRanges / 5.0;
        }

        private bool IsValidCombination(List<int> combination)
        {
            return combination.Count == 14 &&
                   combination.All(n => n >= 1 && n <= 25) &&
                   combination.Distinct().Count() == 14;
        }

        public int GetGeneration() => generation;
        public List<PerformanceMetric> GetPerformanceHistory() => performanceHistory;
    }
}

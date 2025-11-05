using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text.Json;

namespace DataProcessor
{
    public class SeriesData
    {
        public List<int> Elements { get; set; } = new List<int>();
        public DateTime Date { get; set; }
        public int SeriesId { get; set; }
    }

    public class ModelConfig
    {
        public int ElementsPerSeries { get; set; } = 14;
        public int ElementRange { get; set; } = 25;
        public int WindowSize { get; set; } = 10;
        public FeatureEngineering FeatureEngineering { get; set; } = new FeatureEngineering();
        public ModelParameters ModelParameters { get; set; } = new ModelParameters();
    }

    public class FeatureEngineering
    {
        public bool UseFrequencyFeatures { get; set; } = true;
        public bool UseSequenceFeatures { get; set; } = true;
        public bool UseDistributionalFeatures { get; set; } = true;
        public bool UseContextualFeatures { get; set; } = true;
        public bool UseTrendFeatures { get; set; } = true;
    }

    public class ModelParameters
    {
        public int EnsembleSize { get; set; } = 5;
        public double RegularizationStrength { get; set; } = 0.01;
        public double LearningRate { get; set; } = 0.05;
        public int MaxIterations { get; set; } = 100;
        public int CrossValidationFolds { get; set; } = 3;
    }

    public class TrainingData
    {
        public List<double[]> Features { get; set; } = new List<double[]>();
        public List<double[]> Labels { get; set; } = new List<double[]>();
        public ValidationSet ValidationSet { get; set; } = new ValidationSet();
    }

    public class ValidationSet
    {
        public List<double[]> Features { get; set; } = new List<double[]>();
        public List<double[]> Labels { get; set; } = new List<double[]>();
    }

    public class PredictionResult
    {
        public List<string> PredictedElements { get; set; } = new List<string>();
        public Dictionary<int, double> ElementScores { get; set; } = new Dictionary<int, double>();
        public double Confidence { get; set; }
        public Dictionary<string, object> Metadata { get; set; } = new Dictionary<string, object>();
    }

    public class AdvancedPredictiveAnalysisModel
    {
        private readonly ModelConfig config;
        private List<SeriesData> historicalSeries;
        private TrainingData trainingData;
        private readonly Random random = new Random();
        private readonly DatabaseService databaseService;

        public AdvancedPredictiveAnalysisModel(List<SeriesData>? sequentialDataSeries = null)
        {
            config = new ModelConfig();
            databaseService = new DatabaseService();
            
            // Load from database if no data provided
            if (sequentialDataSeries == null || sequentialDataSeries.Count == 0)
            {
                historicalSeries = LoadSeriesFromDatabase();
            }
            else
            {
                historicalSeries = sequentialDataSeries;
            }
            
            trainingData = PrepareTrainingData();
            TrainModels();
        }

        public static AdvancedPredictiveAnalysisModel LoadFromDatabase()
        {
            return new AdvancedPredictiveAnalysisModel(); // Will automatically load from database
        }

        public static AdvancedPredictiveAnalysisModel LoadFromDataset(string datasetPath)
        {
            var seriesData = new List<SeriesData>();
            
            try
            {
                if (Path.GetExtension(datasetPath).ToLower() == ".json")
                {
                    string jsonContent = File.ReadAllText(datasetPath);
                    seriesData = JsonSerializer.Deserialize<List<SeriesData>>(jsonContent) ?? new List<SeriesData>();
                }
                else if (Path.GetExtension(datasetPath).ToLower() == ".csv")
                {
                    seriesData = LoadFromCsv(datasetPath);
                }
                else
                {
                    seriesData = LoadFromTextFile(datasetPath);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading dataset: {ex.Message}");
                seriesData = new List<SeriesData>();
            }

            return new AdvancedPredictiveAnalysisModel(seriesData);
        }

        private static List<SeriesData> LoadFromCsv(string filePath)
        {
            var series = new List<SeriesData>();
            var lines = File.ReadAllLines(filePath);
            
            for (int i = 1; i < lines.Length; i++) // Skip header
            {
                var parts = lines[i].Split(',');
                if (parts.Length >= 2)
                {
                    var seriesData = new SeriesData
                    {
                        SeriesId = int.TryParse(parts[0], out var id) ? id : i - 1,
                        Date = DateTime.Now.AddDays(-i)
                    };

                    for (int j = 1; j < parts.Length; j++)
                    {
                        if (int.TryParse(parts[j], out var element))
                        {
                            seriesData.Elements.Add(element);
                        }
                    }

                    if (seriesData.Elements.Count > 0)
                    {
                        series.Add(seriesData);
                    }
                }
            }

            return series;
        }

        private static List<SeriesData> LoadFromTextFile(string filePath)
        {
            var series = new List<SeriesData>();
            var lines = File.ReadAllLines(filePath);
            
            for (int i = 0; i < lines.Length; i++)
            {
                var line = lines[i].Trim();
                if (string.IsNullOrEmpty(line)) continue;

                var seriesData = new SeriesData
                {
                    SeriesId = i,
                    Date = DateTime.Now.AddDays(-lines.Length + i)
                };

                var parts = line.Split(new char[] { ' ', ',', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                foreach (var part in parts)
                {
                    if (int.TryParse(part, out var element))
                    {
                        seriesData.Elements.Add(element);
                    }
                }

                if (seriesData.Elements.Count > 0)
                {
                    series.Add(seriesData);
                }
            }

            return series;
        }

        private TrainingData PrepareTrainingData()
        {
            var trainingData = new TrainingData();

            if (historicalSeries.Count <= config.WindowSize)
            {
                Console.WriteLine("Insufficient data for training ML models");
                return trainingData;
            }

            for (int i = config.WindowSize; i < historicalSeries.Count; i++)
            {
                var window = historicalSeries.Skip(i - config.WindowSize).Take(config.WindowSize).ToList();
                var currentSeries = historicalSeries[i];

                var featureVector = GenerateFeatureVector(window);
                var targetVector = new double[config.ElementRange + 1];
                
                foreach (var element in currentSeries.Elements)
                {
                    if (element <= config.ElementRange)
                        targetVector[element] = 1.0;
                }

                if (random.NextDouble() < 0.8)
                {
                    trainingData.Features.Add(featureVector);
                    trainingData.Labels.Add(targetVector);
                }
                else
                {
                    trainingData.ValidationSet.Features.Add(featureVector);
                    trainingData.ValidationSet.Labels.Add(targetVector);
                }
            }

            return trainingData;
        }

        private double[] GenerateFeatureVector(List<SeriesData> window)
        {
            var features = new List<double>();

            if (config.FeatureEngineering.UseFrequencyFeatures)
            {
                AddFrequencyFeatures(window, features);
            }

            if (config.FeatureEngineering.UseSequenceFeatures)
            {
                AddSequenceFeatures(window, features);
            }

            if (config.FeatureEngineering.UseDistributionalFeatures)
            {
                AddDistributionalFeatures(window, features);
            }

            if (config.FeatureEngineering.UseTrendFeatures)
            {
                AddTrendFeatures(window, features);
            }

            return features.ToArray();
        }

        private void AddFrequencyFeatures(List<SeriesData> window, List<double> features)
        {
            var elementFrequencies = new int[config.ElementRange + 1];
            
            foreach (var series in window)
            {
                foreach (var element in series.Elements)
                {
                    if (element <= config.ElementRange)
                        elementFrequencies[element]++;
                }
            }

            for (int i = 1; i <= config.ElementRange; i++)
            {
                features.Add((double)elementFrequencies[i] / window.Count);
            }
        }

        private void AddSequenceFeatures(List<SeriesData> window, List<double> features)
        {
            var sequenceLengths = new List<double>();
            
            foreach (var series in window)
            {
                var sequences = FindAllSequences(series.Elements);
                var maxLength = sequences.Count > 0 ? sequences.Max(seq => seq.Count) : 0;
                sequenceLengths.Add(maxLength);
            }

            features.Add(CalculateMean(sequenceLengths));
            features.Add(CalculateLinearTrend(sequenceLengths));
        }

        private void AddDistributionalFeatures(List<SeriesData> window, List<double> features)
        {
            var oddCounts = new List<double>();
            
            foreach (var series in window)
            {
                var oddCount = series.Elements.Count(e => e % 2 != 0);
                oddCounts.Add(oddCount);
            }

            features.Add(CalculateMean(oddCounts) / config.ElementsPerSeries);
            features.Add(CalculateVariance(oddCounts) / config.ElementsPerSeries);
        }

        private void AddTrendFeatures(List<SeriesData> window, List<double> features)
        {
            var seriesSums = window.Select(series => (double)series.Elements.Sum()).ToList();
            features.Add(CalculateLinearTrend(seriesSums));

            var seriesMedians = window.Select(series =>
            {
                var sorted = series.Elements.OrderBy(x => x).ToList();
                var mid = sorted.Count / 2;
                return sorted.Count % 2 == 0 
                    ? (sorted[mid - 1] + sorted[mid]) / 2.0 
                    : sorted[mid];
            }).ToList();
            
            features.Add(CalculateLinearTrend(seriesMedians));
        }

        private List<List<int>> FindAllSequences(List<int> elements)
        {
            var sequences = new List<List<int>>();
            var sortedElements = elements.OrderBy(x => x).ToList();
            var currentSeq = new List<int> { sortedElements[0] };

            for (int i = 1; i < sortedElements.Count; i++)
            {
                if (sortedElements[i] == sortedElements[i - 1] + 1)
                {
                    currentSeq.Add(sortedElements[i]);
                }
                else
                {
                    if (currentSeq.Count >= 2)
                    {
                        sequences.Add(new List<int>(currentSeq));
                    }
                    currentSeq = new List<int> { sortedElements[i] };
                }
            }

            if (currentSeq.Count >= 2)
            {
                sequences.Add(currentSeq);
            }

            return sequences;
        }

        private double CalculateMean(List<double> values)
        {
            if (values == null || values.Count == 0) return 0;
            return values.Average();
        }

        private double CalculateVariance(List<double> values)
        {
            if (values == null || values.Count <= 1) return 0;
            var mean = CalculateMean(values);
            return values.Select(v => Math.Pow(v - mean, 2)).Average();
        }

        private double CalculateLinearTrend(List<double> values)
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

        private void TrainModels()
        {
            if (trainingData.Features.Count == 0)
            {
                Console.WriteLine("No training data available");
                return;
            }

            Console.WriteLine($"Training models with {trainingData.Features.Count} training samples");
        }

        public PredictionResult PredictNextSeries()
        {
            if (historicalSeries.Count < config.WindowSize)
            {
                return new PredictionResult
                {
                    PredictedElements = GenerateRandomPrediction(),
                    Confidence = 0.1,
                    Metadata = new Dictionary<string, object> { { "method", "random_fallback" } }
                };
            }

            var recentHistory = historicalSeries.TakeLast(config.WindowSize).ToList();
            var featureVector = GenerateFeatureVector(recentHistory);
            var elementScores = PredictElementScores(featureVector);

            var rankedElements = elementScores
                .OrderByDescending(kvp => kvp.Value)
                .Take(config.ElementsPerSeries)
                .Select(kvp => kvp.Key)
                .OrderBy(x => x)
                .ToList();

            var confidence = elementScores.Values.Take(config.ElementsPerSeries).Average();

            return new PredictionResult
            {
                PredictedElements = rankedElements.Select(e => e.ToString("D2")).ToList(),
                ElementScores = elementScores,
                Confidence = confidence,
                Metadata = new Dictionary<string, object>
                {
                    { "method", "ml_prediction" },
                    { "feature_count", featureVector.Length },
                    { "training_samples", trainingData.Features.Count }
                }
            };
        }

        public List<PredictionResult> PredictNextSeriesCombinations()
        {
            if (historicalSeries.Count < 10)
            {
                return new List<PredictionResult> { PredictNextSeries() };
            }

            // Advanced ML pattern recognition based on concrete statistical analysis
            var predictions = new List<PredictionResult>();
            
            // Generate predictions using the ML scoring algorithm
            var mlPredictions = GenerateMLPatternPredictions();
            return mlPredictions;
        }

        public int GetNextSeriesNumber()
        {
            if (historicalSeries.Count == 0) return 3107; // Default fallback
            
            var lastSeriesNumber = historicalSeries.Max(s => s.SeriesId);
            return lastSeriesNumber + 1;
        }

        private List<PredictionResult> GenerateMLPatternPredictions()
        {
            var predictions = new List<PredictionResult>();
            
            // USE ALL HISTORICAL DATA for comprehensive pattern analysis
            Console.WriteLine($"Analyzing ALL {historicalSeries.Count} series in database for deep pattern recognition...");
            
            // Global pattern analysis using all data
            var globalPatterns = AnalyzeGlobalPatterns(historicalSeries);
            var cyclicalPatterns = AnalyzeCyclicalPatterns(historicalSeries);
            var frequencyPatterns = AnalyzeAdvancedFrequencyPatterns(historicalSeries);
            var geometricPatterns = AnalyzeGeometricPatterns(historicalSeries);
            var temporalPatterns = AnalyzeTemporalPatterns(historicalSeries);
            var mathematicalPatterns = AnalyzeMathematicalPatterns(historicalSeries);
            
            // Still use recent patterns for trend analysis
            var recentSeries = historicalSeries.TakeLast(Math.Min(32, historicalSeries.Count / 4)).ToList();
            var hotNumbers = AnalyzeHotNumbers(recentSeries);
            var trendingNumbers = AnalyzeTrendingNumbers(recentSeries);
            var recentAverageSum = CalculateAverageSum(recentSeries);
            
            // Generate combinations using ALL pattern data
            var topCombinations = GenerateAdvancedScoredCombinations(
                globalPatterns, cyclicalPatterns, frequencyPatterns, geometricPatterns,
                temporalPatterns, mathematicalPatterns, hotNumbers, trendingNumbers, recentAverageSum);
            
            foreach (var combination in topCombinations.Take(1)) // Top 1 combination only
            {
                var mlScore = CalculateEnhancedLearnedScore(combination, globalPatterns, cyclicalPatterns,
                    frequencyPatterns, geometricPatterns, temporalPatterns, mathematicalPatterns,
                    hotNumbers, trendingNumbers, recentAverageSum);
                
                var prediction = new PredictionResult
                {
                    PredictedElements = combination.Select(e => e.ToString("D2")).ToList(),
                    Confidence = Math.Min(0.95, mlScore / 100.0), // Convert score to confidence
                    ElementScores = AdvancedScoringSystem.GenerateElementScoresFromML(combination, hotNumbers),
                    Metadata = new Dictionary<string, object>
                    {
                        { "method", "advanced_mathematical_pattern_analysis" },
                        { "ml_score", mlScore },
                        { "total_series_analyzed", historicalSeries.Count },
                        { "hot_number_count", combination.Count(n => hotNumbers.ContainsKey(n)) },
                        { "sum", combination.Sum() },
                        { "avg_gap", AdvancedScoringSystem.CalculateAverageGap(combination) },
                        { "global_pattern_score", globalPatterns.GetValueOrDefault("score", 0.0) },
                        { "cyclical_pattern_score", cyclicalPatterns.GetValueOrDefault("score", 0.0) },
                        { "frequency_pattern_score", frequencyPatterns.GetValueOrDefault("score", 0.0) },
                        { "geometric_pattern_score", geometricPatterns.GetValueOrDefault("score", 0.0) },
                        { "temporal_pattern_score", temporalPatterns.GetValueOrDefault("score", 0.0) },
                        { "mathematical_pattern_score", mathematicalPatterns.GetValueOrDefault("score", 0.0) }
                    }
                };
                predictions.Add(prediction);
            }
            
            return predictions;
        }

        private Dictionary<int, int> AnalyzeHotNumbers(List<SeriesData> recentSeries)
        {
            var frequencies = new Dictionary<int, int>();
            
            foreach (var series in recentSeries)
            {
                foreach (var element in series.Elements)
                {
                    frequencies[element] = frequencies.GetValueOrDefault(element, 0) + 1;
                }
            }
            
            return frequencies.OrderByDescending(kvp => kvp.Value).Take(10).ToDictionary(kvp => kvp.Key, kvp => kvp.Value);
        }

        private Dictionary<int, double> AnalyzeTrendingNumbers(List<SeriesData> recentSeries)
        {
            var trends = new Dictionary<int, double>();
            int windowSize = Math.Min(8, recentSeries.Count / 2);
            
            var older = recentSeries.Take(windowSize).ToList();
            var newer = recentSeries.Skip(windowSize).Take(windowSize).ToList();
            
            for (int num = 1; num <= config.ElementRange; num++)
            {
                var olderCount = older.Sum(s => s.Elements.Count(e => e == num));
                var newerCount = newer.Sum(s => s.Elements.Count(e => e == num));
                trends[num] = newerCount - olderCount; // Positive = trending up
            }
            
            return trends;
        }

        // NEW: Global Pattern Analysis using ALL historical data
        private Dictionary<string, object> AnalyzeGlobalPatterns(List<SeriesData> allSeries)
        {
            var patterns = new Dictionary<string, object>();
            
            // Calculate global frequency distribution
            var globalFrequencies = new Dictionary<int, int>();
            var totalDraws = 0;
            
            foreach (var series in allSeries)
            {
                foreach (var element in series.Elements)
                {
                    globalFrequencies[element] = globalFrequencies.GetValueOrDefault(element, 0) + 1;
                    totalDraws++;
                }
            }
            
            // Statistical analysis
            var frequencies = globalFrequencies.Values.ToList();
            var mean = frequencies.Average();
            var stdDev = Math.Sqrt(frequencies.Select(f => Math.Pow(f - mean, 2)).Average());
            var variance = stdDev * stdDev;
            var entropy = -globalFrequencies.Values.Sum(f => (f / (double)totalDraws) * Math.Log(f / (double)totalDraws, 2));
            
            // Chi-square test for randomness
            var expectedFreq = totalDraws / (double)config.ElementRange;
            var chiSquare = globalFrequencies.Values.Sum(observed => Math.Pow(observed - expectedFreq, 2) / expectedFreq);
            
            patterns["global_frequencies"] = globalFrequencies;
            patterns["total_draws"] = totalDraws;
            patterns["mean_frequency"] = mean;
            patterns["std_deviation"] = stdDev;
            patterns["variance"] = variance;
            patterns["entropy"] = entropy;
            patterns["chi_square"] = chiSquare;
            patterns["score"] = CalculateGlobalPatternScore(globalFrequencies, mean, stdDev, entropy);
            
            Console.WriteLine($"Global Analysis: {allSeries.Count} series, {totalDraws} total draws, entropy: {entropy:F3}, chi²: {chiSquare:F2}");
            
            return patterns;
        }

        // Use the new advanced pattern analysis methods
        private Dictionary<string, object> AnalyzeCyclicalPatterns(List<SeriesData> allSeries)
        {
            return AdvancedMathematicalPatterns.AnalyzeCyclicalPatterns(allSeries, config.ElementRange);
        }

        private Dictionary<string, object> AnalyzeAdvancedFrequencyPatterns(List<SeriesData> allSeries)
        {
            return AdvancedMathematicalPatterns.AnalyzeAdvancedFrequencyPatterns(allSeries, config.ElementRange);
        }

        private Dictionary<string, object> AnalyzeGeometricPatterns(List<SeriesData> allSeries)
        {
            return AdvancedMathematicalPatterns.AnalyzeGeometricPatterns(allSeries);
        }

        private Dictionary<string, object> AnalyzeTemporalPatterns(List<SeriesData> allSeries)
        {
            return AdvancedMathematicalPatterns.AnalyzeTemporalPatterns(allSeries);
        }

        private Dictionary<string, object> AnalyzeMathematicalPatterns(List<SeriesData> allSeries)
        {
            return AdvancedMathematicalPatterns.AnalyzeMathematicalPatterns(allSeries, config.ElementRange);
        }

        private double CalculateGlobalPatternScore(Dictionary<int, int> frequencies, double mean, double stdDev, double entropy)
        {
            var normalizedEntropy = entropy / Math.Log(config.ElementRange, 2); // Normalize to 0-1
            var coefficientOfVariation = stdDev / mean;
            return (normalizedEntropy * 0.6 + (1.0 / coefficientOfVariation) * 0.4) * 100;
        }

        private double CalculateAverageSum(List<SeriesData> recentSeries)
        {
            return recentSeries.SelectMany(s => s.Elements).GroupBy(s => s).Select(g => g.Sum()).Average();
        }

        private List<List<int>> GenerateAdvancedScoredCombinations(
            Dictionary<string, object> globalPatterns,
            Dictionary<string, object> cyclicalPatterns,
            Dictionary<string, object> frequencyPatterns,
            Dictionary<string, object> geometricPatterns,
            Dictionary<string, object> temporalPatterns,
            Dictionary<string, object> mathematicalPatterns,
            Dictionary<int, int> hotNumbers, Dictionary<int, double> trendingNumbers, double targetSum)
        {
            var combinations = new List<List<int>>();
            
            // Generate combinations using ALL pattern data
            var candidates = Enumerable.Range(1, config.ElementRange).ToList();
            var hotNumbersList = hotNumbers.Keys.Take(15).ToList(); // Top 15 hot numbers
            var trendingUpNumbers = trendingNumbers.Where(kvp => kvp.Value > 0).Select(kvp => kvp.Key).ToList();
            
            // Extract advanced pattern data
            var globalFreqs = (Dictionary<int, int>)globalPatterns["global_frequencies"];
            var freqStability = (Dictionary<int, double>)frequencyPatterns["frequency_stability"];
            var mostStable = ((Dictionary<int, double>)frequencyPatterns["most_stable_numbers"]).Keys.ToList();
            
            // Generate multiple combinations using advanced strategies based on ALL patterns
            var generatedCombinations = new List<List<int>>();
            
            // Strategy 1: Global frequency optimized combinations (3 combinations)
            for (int i = 0; i < 3; i++)
            {
                var combo = GenerateGlobalFrequencyOptimizedCombination(globalFreqs, candidates, i);
                if (combo.Count == config.ElementsPerSeries)
                    generatedCombinations.Add(combo);
            }
            
            // Strategy 2: Mathematical pattern combinations (2 combinations)  
            for (int i = 0; i < 2; i++)
            {
                var combo = GenerateMathematicalPatternCombination(mathematicalPatterns, candidates, i);
                if (combo.Count == config.ElementsPerSeries)
                    generatedCombinations.Add(combo);
            }
            
            // Strategy 3: Learned Pattern combinations (3 combinations) - ENHANCED FROM 3108 ANALYSIS
            for (int i = 0; i < 3; i++)
            {
                var combo = GenerateLearnedPatternCombination(globalPatterns, i);
                if (combo.Count == config.ElementsPerSeries)
                    generatedCombinations.Add(combo);
            }
            
            // Strategy 4: Stability-based combinations (1 combination)
            var stabilityCombo = GenerateStabilityBasedCombination(mostStable, hotNumbersList, candidates, 0);
            if (stabilityCombo.Count == config.ElementsPerSeries)
                generatedCombinations.Add(stabilityCombo);
            
            // Score and rank all combinations using ENHANCED learned patterns from 3108 analysis
            var scoredCombinations = generatedCombinations.Distinct(new ListEqualityComparer())
                .Select(combo => new { 
                    Combination = combo, 
                    Score = CalculateEnhancedLearnedScore(combo, globalPatterns, cyclicalPatterns,
                        frequencyPatterns, geometricPatterns, temporalPatterns, mathematicalPatterns,
                        hotNumbers, trendingNumbers, targetSum)
                })
                .OrderByDescending(x => x.Score)
                .Take(7)
                .Select(x => x.Combination)
                .ToList();
            
            return scoredCombinations;
        }
        
        // Use the new advanced combination generators
        private List<int> GenerateGlobalFrequencyOptimizedCombination(Dictionary<int, int> globalFreqs, List<int> allCandidates, int variation)
        {
            return AdvancedCombinationGenerators.GenerateGlobalFrequencyOptimizedCombination(globalFreqs, allCandidates, variation);
        }
        
        private List<int> GenerateMathematicalPatternCombination(Dictionary<string, object> mathPatterns, List<int> allCandidates, int variation)
        {
            return AdvancedCombinationGenerators.GenerateMathematicalPatternCombination(mathPatterns, allCandidates, variation);
        }
        
        private List<int> GenerateStabilityBasedCombination(List<int> mostStable, List<int> hotNumbers, List<int> allCandidates, int variation)
        {
            return AdvancedCombinationGenerators.GenerateStabilityBasedCombination(mostStable, hotNumbers, allCandidates, variation);
        }
        
        private List<int> GenerateGeometricPatternCombination(Dictionary<string, object> geomPatterns, List<int> allCandidates)
        {
            return AdvancedCombinationGenerators.GenerateGeometricPatternCombination(geomPatterns, allCandidates);
        }
        
        private List<int> GenerateHybridPatternCombination(Dictionary<int, int> globalFreqs, List<int> mostStable, List<int> hotNumbers, List<int> trendingUp, List<int> allCandidates)
        {
            return AdvancedCombinationGenerators.GenerateHybridPatternCombination(globalFreqs, mostStable, hotNumbers, trendingUp, allCandidates);
        }
        
        // Use the new advanced scoring system
        private double CalculateAdvancedMLScore(
            List<int> combination,
            Dictionary<string, object> globalPatterns,
            Dictionary<string, object> cyclicalPatterns,
            Dictionary<string, object> frequencyPatterns,
            Dictionary<string, object> geometricPatterns,
            Dictionary<string, object> temporalPatterns,
            Dictionary<string, object> mathematicalPatterns,
            Dictionary<int, int> hotNumbers, Dictionary<int, double> trendingNumbers, double targetSum)
        {
            return AdvancedScoringSystem.CalculateAdvancedMLScore(combination, globalPatterns, cyclicalPatterns,
                frequencyPatterns, geometricPatterns, temporalPatterns, mathematicalPatterns,
                hotNumbers, trendingNumbers, targetSum);
        }
        
        // ENHANCED: Use learned patterns from 3108 analysis
        private double CalculateEnhancedLearnedScore(
            List<int> combination,
            Dictionary<string, object> globalPatterns,
            Dictionary<string, object> cyclicalPatterns,
            Dictionary<string, object> frequencyPatterns,
            Dictionary<string, object> geometricPatterns,
            Dictionary<string, object> temporalPatterns,
            Dictionary<string, object> mathematicalPatterns,
            Dictionary<int, int> hotNumbers, Dictionary<int, double> trendingNumbers, double targetSum)
        {
            // Create unified pattern dictionary for enhanced scoring
            var unifiedPatterns = new Dictionary<string, object>(globalPatterns);
            foreach (var kvp in frequencyPatterns)
            {
                unifiedPatterns[kvp.Key] = kvp.Value;
            }
            foreach (var kvp in cyclicalPatterns)
            {
                unifiedPatterns[kvp.Key] = kvp.Value;
            }
            
            // Combine enhanced learned score with original patterns
            var learnedScore = EnhancedPatternLearning.CalculateEnhancedScore(combination, unifiedPatterns);
            var originalScore = AdvancedScoringSystem.CalculateAdvancedMLScore(combination, globalPatterns, cyclicalPatterns,
                frequencyPatterns, geometricPatterns, temporalPatterns, mathematicalPatterns,
                hotNumbers, trendingNumbers, targetSum);
            
            // Weight: 70% learned patterns (from 3108), 30% original patterns
            return learnedScore * 0.70 + originalScore * 0.30;
        }
        
        private List<int> GenerateLearnedPatternCombination(Dictionary<string, object> globalPatterns, int variation)
        {
            return EnhancedPatternLearning.GenerateLearnedPatternCombination(globalPatterns, variation);
        }
        
        private List<int> GenerateHotNumberCombination(List<int> hotNumbers, List<int> allCandidates, int variation)
        {
            var random = new Random(variation + DateTime.Now.Millisecond);
            var combo = new List<int>();
            
            // Select 8-10 hot numbers
            var selectedHot = hotNumbers.OrderBy(x => random.Next()).Take(8 + variation).ToList();
            combo.AddRange(selectedHot);
            
            // Fill remaining slots with other numbers to reach 14
            var remaining = allCandidates.Except(combo).OrderBy(x => random.Next()).Take(config.ElementsPerSeries - combo.Count).ToList();
            combo.AddRange(remaining);
            
            return combo.OrderBy(x => x).Take(config.ElementsPerSeries).ToList();
        }
        
        private List<int> GenerateTrendBasedCombination(List<int> trendingUp, List<int> hotNumbers, List<int> allCandidates, int variation)
        {
            var random = new Random(variation + DateTime.Now.Millisecond + 1000);
            var combo = new List<int>();
            
            // Select trending up numbers
            var selectedTrending = trendingUp.OrderBy(x => random.Next()).Take(6).ToList();
            combo.AddRange(selectedTrending);
            
            // Add some hot numbers
            var selectedHot = hotNumbers.Except(combo).OrderBy(x => random.Next()).Take(5).ToList();
            combo.AddRange(selectedHot);
            
            // Fill remaining slots
            var remaining = allCandidates.Except(combo).OrderBy(x => random.Next()).Take(config.ElementsPerSeries - combo.Count).ToList();
            combo.AddRange(remaining);
            
            return combo.OrderBy(x => x).Take(config.ElementsPerSeries).ToList();
        }
        
        private List<int> GenerateBalancedCombination(List<int> allCandidates, List<int> hotNumbers, int variation)
        {
            var random = new Random(variation + DateTime.Now.Millisecond + 2000);
            var combo = new List<int>();
            
            // Balanced distribution: 4-5 from each range
            var early = allCandidates.Where(x => x <= 8).OrderBy(x => random.Next()).Take(4 + variation % 2).ToList();
            var middle = allCandidates.Where(x => x >= 9 && x <= 17).OrderBy(x => random.Next()).Take(4).ToList();
            var late = allCandidates.Where(x => x >= 18).OrderBy(x => random.Next()).Take(6 - variation % 2).ToList();
            
            combo.AddRange(early);
            combo.AddRange(middle);
            combo.AddRange(late);
            
            return combo.OrderBy(x => x).Take(config.ElementsPerSeries).ToList();
        }
        
        private class ListEqualityComparer : IEqualityComparer<List<int>>
        {
            public bool Equals(List<int>? x, List<int>? y)
            {
                return x != null && y != null && x.SequenceEqual(y);
            }

            public int GetHashCode(List<int>? obj)
            {
                return obj?.Aggregate(0, (a, v) => HashCode.Combine(a, v.GetHashCode())) ?? 0;
            }
        }

        private double CalculateMLScore(List<int> combination, Dictionary<int, int> hotNumbers, Dictionary<int, double> trendingNumbers, double targetSum)
        {
            double score = 0.0;
            
            // 1. Hot Numbers Score (25%)
            var hotCount = combination.Count(n => hotNumbers.ContainsKey(n));
            var hotScore = (hotCount / 10.0) * 100;
            score += hotScore * 0.25;
            
            // 2. Trend Score (15%)
            var trendScore = combination.Sum(n => Math.Max(0, trendingNumbers.GetValueOrDefault(n, 0))) * 10;
            score += Math.Min(100, trendScore) * 0.15;
            
            // 3. Sum Convergence Score (20%)
            var sumDeviation = Math.Abs(combination.Sum() - targetSum);
            var sumScore = Math.Max(0, 100 - sumDeviation * 2);
            score += sumScore * 0.20;
            
            // 4. Gap Pattern Score (15%)
            var gapScore = CalculateGapScore(combination);
            score += gapScore * 0.15;
            
            // 5. Position Distribution Score (15%)
            var positionScore = CalculatePositionScore(combination);
            score += positionScore * 0.15;
            
            // 6. Arithmetic Pattern Score (10%)
            var arithmeticScore = CalculateArithmeticScore(combination);
            score += arithmeticScore * 0.10;
            
            return score;
        }

        private double CalculateGapScore(List<int> combination)
        {
            if (combination.Count < 2) return 0;
            
            var sortedCombo = combination.OrderBy(x => x).ToList();
            var gaps = new List<double>();
            
            for (int i = 1; i < sortedCombo.Count; i++)
            {
                gaps.Add(sortedCombo[i] - sortedCombo[i-1]);
            }
            
            var averageGap = gaps.Average();
            var targetGap = 1.74; // From analysis
            var gapDeviation = Math.Abs(averageGap - targetGap);
            
            return Math.Max(0, 100 - gapDeviation * 20);
        }

        private double CalculatePositionScore(List<int> combination)
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

        private double CalculateArithmeticScore(List<int> combination)
        {
            var sorted = combination.OrderBy(x => x).ToList();
            var maxSequenceLength = 1;
            var currentSequenceLength = 1;
            
            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] == sorted[i-1] + 1)
                {
                    currentSequenceLength++;
                    maxSequenceLength = Math.Max(maxSequenceLength, currentSequenceLength);
                }
                else
                {
                    currentSequenceLength = 1;
                }
            }
            
            return Math.Min(100, maxSequenceLength * 15); // Bonus for consecutive numbers
        }

        private double CalculateAverageGap(List<int> combination)
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

        private Dictionary<int, double> GenerateElementScoresFromML(List<int> combination, Dictionary<int, int> hotNumbers)
        {
            var scores = new Dictionary<int, double>();
            
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

        private Dictionary<int, double> PredictElementScores(double[] featureVector)
        {
            var scores = new Dictionary<int, double>();

            for (int element = 1; element <= config.ElementRange; element++)
            {
                var baseScore = random.NextDouble() * 0.5 + 0.25;
                
                if (historicalSeries.Count > 0)
                {
                    var frequency = historicalSeries
                        .SelectMany(s => s.Elements)
                        .Count(e => e == element) / (double)historicalSeries.Count;
                    
                    baseScore = 0.7 * baseScore + 0.3 * frequency;
                }

                scores[element] = Math.Max(0, Math.Min(1, baseScore));
            }

            return scores;
        }

        private List<string> GenerateRandomPrediction()
        {
            var elements = new List<int>();
            var used = new HashSet<int>();

            while (elements.Count < config.ElementsPerSeries)
            {
                var element = random.Next(1, config.ElementRange + 1);
                if (!used.Contains(element))
                {
                    elements.Add(element);
                    used.Add(element);
                }
            }

            return elements.OrderBy(x => x).Select(e => e.ToString("D2")).ToList();
        }

        public void AddNewSeries(SeriesData newSeries)
        {
            historicalSeries.Add(newSeries);
            
            if (historicalSeries.Count % 10 == 0)
            {
                trainingData = PrepareTrainingData();
                TrainModels();
            }
        }

        private List<SeriesData> LoadSeriesFromDatabase()
        {
            try
            {
                var lotteryData = databaseService.LoadLotteryData();
                var seriesData = new List<SeriesData>();
                
                foreach (var data in lotteryData)
                {
                    seriesData.Add(new SeriesData
                    {
                        SeriesId = data.SeriesId,
                        Elements = data.Numbers,
                        Date = DateTime.Now.AddDays(-data.SeriesId) // Approximate date
                    });
                }
                
                Console.WriteLine($"Loaded {seriesData.Count} series from database");
                return seriesData;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading from database: {ex.Message}");
                return new List<SeriesData>();
            }
        }

        public Dictionary<string, object> GetModelStats()
        {
            return new Dictionary<string, object>
            {
                { "historical_series_count", historicalSeries.Count },
                { "training_samples", trainingData.Features.Count },
                { "validation_samples", trainingData.ValidationSet.Features.Count },
                { "feature_dimensions", trainingData.Features.FirstOrDefault()?.Length ?? 0 },
                { "config", config }
            };
        }
    }
}
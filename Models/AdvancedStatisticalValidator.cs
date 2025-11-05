using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using System.Text.Json;

namespace DataProcessor.Models
{
    public class AdvancedStatisticalValidator
    {
        private readonly List<ValidationResult> validationHistory;
        private readonly Dictionary<string, AccuracyTracker> modelTrackers;
        private readonly StatisticalBaseline baseline;
        private readonly Random random;

        public AdvancedStatisticalValidator()
        {
            validationHistory = new List<ValidationResult>();
            modelTrackers = new Dictionary<string, AccuracyTracker>();
            baseline = new StatisticalBaseline();
            random = new Random(42);
        }

        public ValidationResult ValidatePrediction(string modelName, int seriesId, List<int> prediction,
                                                  List<int> actual = null, Dictionary<string, object> metadata = null)
        {
            var result = new ValidationResult
            {
                ModelName = modelName,
                SeriesId = seriesId,
                Prediction = prediction,
                Actual = actual,
                Metadata = metadata ?? new Dictionary<string, object>(),
                Timestamp = DateTime.UtcNow
            };

            // Perform comprehensive validation
            PerformStatisticalValidation(result);
            PerformPatternValidation(result);
            PerformDistributionValidation(result);
            PerformUniquenessValidation(result);

            if (actual != null)
            {
                PerformAccuracyValidation(result);
                UpdateAccuracyTracking(result);
            }

            // Calculate overall validation score
            result.OverallScore = CalculateOverallValidationScore(result);

            validationHistory.Add(result);

            Console.WriteLine($"🔍 Validation for {modelName} Series {seriesId}: Score {result.OverallScore:F3}");

            return result;
        }

        private void PerformStatisticalValidation(ValidationResult result)
        {
            var stats = new StatisticalValidation();
            var prediction = result.Prediction;

            // Basic statistics
            stats.Mean = prediction.Average();
            stats.Median = CalculateMedian(prediction);
            stats.StandardDeviation = CalculateStandardDeviation(prediction);
            stats.Variance = Math.Pow(stats.StandardDeviation, 2);
            stats.Range = prediction.Max() - prediction.Min();
            stats.Sum = prediction.Sum();

            // Advanced statistics
            stats.Skewness = CalculateSkewness(prediction);
            stats.Kurtosis = CalculateKurtosis(prediction);
            stats.Entropy = CalculateEntropy(prediction);
            stats.GiniCoefficient = CalculateGiniCoefficient(prediction);

            // Validate against expected ranges
            stats.MeanValid = stats.Mean >= 10 && stats.Mean <= 16; // Expected mean range
            stats.SumValid = stats.Sum >= 160 && stats.Sum <= 240; // Expected sum range
            stats.VarianceValid = stats.Variance >= 25 && stats.Variance <= 80; // Expected variance range

            // Statistical outlier detection
            stats.HasOutliers = DetectStatisticalOutliers(prediction);
            stats.OutlierCount = CountOutliers(prediction);

            // Distribution normality test
            stats.NormalityScore = TestNormality(prediction);

            result.StatisticalValidation = stats;
        }

        private void PerformPatternValidation(ValidationResult result)
        {
            var patterns = new PatternValidation();
            var prediction = result.Prediction;

            // Consecutive patterns
            patterns.ConsecutivePairs = CountConsecutivePairs(prediction);
            patterns.ConsecutiveGroups = FindConsecutiveGroups(prediction);
            patterns.MaxConsecutiveLength = patterns.ConsecutiveGroups.Any() ?
                patterns.ConsecutiveGroups.Max(g => g.Count) : 0;

            // Gap analysis
            patterns.Gaps = CalculateGaps(prediction);
            patterns.AverageGap = patterns.Gaps.Average();
            patterns.GapVariance = CalculateVariance(patterns.Gaps.Select(g => (double)g).ToList());
            patterns.MaxGap = patterns.Gaps.Max();
            patterns.MinGap = patterns.Gaps.Min();

            // Arithmetic sequences
            patterns.ArithmeticSequences = FindArithmeticSequences(prediction);
            patterns.HasArithmeticPattern = patterns.ArithmeticSequences.Any();

            // Clustering analysis
            patterns.ClusterAnalysis = AnalyzeClusters(prediction);
            patterns.IsolatedNumbers = FindIsolatedNumbers(prediction);

            // Pattern regularity
            patterns.RegularityScore = CalculatePatternRegularity(prediction);

            // Fibonacci-like sequences
            patterns.FibonacciLikeSequences = FindFibonacciLikeSequences(prediction);

            result.PatternValidation = patterns;
        }

        private void PerformDistributionValidation(ValidationResult result)
        {
            var distribution = new DistributionValidation();
            var prediction = result.Prediction;

            // Range distribution (1-8, 9-17, 18-25)
            distribution.LowRange = prediction.Count(n => n <= 8);
            distribution.MidRange = prediction.Count(n => n >= 9 && n <= 17);
            distribution.HighRange = prediction.Count(n => n >= 18);

            // Balance scores
            distribution.RangeBalance = CalculateRangeBalance(distribution.LowRange,
                distribution.MidRange, distribution.HighRange);

            // Quintile distribution (5 groups of 5 numbers each)
            distribution.QuintileDistribution = CalculateQuintileDistribution(prediction);
            distribution.QuintileBalance = CalculateQuintileBalance(distribution.QuintileDistribution);

            // Coordinate system validation (if applicable)
            distribution.ColumnDistribution = CalculateColumnDistribution(prediction);
            distribution.ColumnBalance = CalculateColumnBalance(distribution.ColumnDistribution);

            // Even/odd distribution
            distribution.EvenCount = prediction.Count(n => n % 2 == 0);
            distribution.OddCount = prediction.Count(n => n % 2 == 1);
            distribution.EvenOddBalance = Math.Abs(distribution.EvenCount - distribution.OddCount) <= 2;

            // Prime number distribution
            distribution.PrimeCount = prediction.Count(IsPrime);
            distribution.CompositeCount = prediction.Count(n => !IsPrime(n) && n > 1);

            // Density analysis
            distribution.DensityMap = CalculateDensityMap(prediction);
            distribution.UniformityScore = CalculateUniformityScore(distribution.DensityMap);

            result.DistributionValidation = distribution;
        }

        private void PerformUniquenessValidation(ValidationResult result)
        {
            var uniqueness = new UniquenessValidation();
            var prediction = result.Prediction;

            // Basic uniqueness
            uniqueness.HasDuplicates = prediction.Count != prediction.Distinct().Count();
            uniqueness.UniqueCount = prediction.Distinct().Count();

            // Historical uniqueness (compare against past predictions)
            uniqueness.IsHistoricallyUnique = IsHistoricallyUnique(prediction);
            uniqueness.SimilarityToHistory = CalculateHistoricalSimilarity(prediction);

            // Uniqueness within ensemble (if multiple predictions exist)
            if (result.Metadata.ContainsKey("EnsemblePredictions"))
            {
                var ensemblePredictions = (List<List<int>>)result.Metadata["EnsemblePredictions"];
                uniqueness.EnsembleUniqueness = CalculateEnsembleUniqueness(prediction, ensemblePredictions);
            }

            // Theoretical uniqueness probability
            uniqueness.TheoreticalProbability = CalculateTheoreticalProbability();

            result.UniquenessValidation = uniqueness;
        }

        private void PerformAccuracyValidation(ValidationResult result)
        {
            var accuracy = new AccuracyValidation();
            var prediction = result.Prediction;
            var actual = result.Actual;

            // Basic accuracy metrics
            accuracy.ExactMatches = prediction.Intersect(actual).Count();
            accuracy.AccuracyPercentage = (double)accuracy.ExactMatches / prediction.Count * 100.0;

            // Position-based accuracy
            accuracy.PositionAccuracy = CalculatePositionAccuracy(prediction, actual);

            // Partial match analysis
            accuracy.NearMisses = CountNearMisses(prediction, actual);
            accuracy.CloseMatches = CountCloseMatches(prediction, actual, tolerance: 2);

            // Distribution accuracy
            accuracy.DistributionSimilarity = CalculateDistributionSimilarity(prediction, actual);

            // Pattern accuracy
            accuracy.PatternSimilarity = CalculatePatternSimilarity(prediction, actual);

            // Statistical accuracy
            accuracy.StatisticalSimilarity = CalculateStatisticalSimilarity(prediction, actual);

            // Confidence intervals
            accuracy.ConfidenceInterval = CalculateAccuracyConfidenceInterval(accuracy.AccuracyPercentage);

            // Significance testing
            accuracy.IsStatisticallySignificant = TestStatisticalSignificance(prediction, actual);

            result.AccuracyValidation = accuracy;
        }

        private void UpdateAccuracyTracking(ValidationResult result)
        {
            var modelName = result.ModelName;

            if (!modelTrackers.ContainsKey(modelName))
            {
                modelTrackers[modelName] = new AccuracyTracker { ModelName = modelName };
            }

            var tracker = modelTrackers[modelName];
            tracker.AddResult(result);

            // Update rolling statistics
            tracker.UpdateStatistics();

            // Check for improvement/degradation trends
            tracker.TrendAnalysis = AnalyzeTrend(tracker.AccuracyHistory);

            // Calculate model confidence
            tracker.ModelConfidence = CalculateModelConfidence(tracker);
        }

        private double CalculateOverallValidationScore(ValidationResult result)
        {
            double score = 0;
            int components = 0;

            // Statistical validation (25% weight)
            if (result.StatisticalValidation != null)
            {
                var statScore = CalculateStatisticalScore(result.StatisticalValidation);
                score += statScore * 0.25;
                components++;
            }

            // Pattern validation (25% weight)
            if (result.PatternValidation != null)
            {
                var patternScore = CalculatePatternScore(result.PatternValidation);
                score += patternScore * 0.25;
                components++;
            }

            // Distribution validation (25% weight)
            if (result.DistributionValidation != null)
            {
                var distScore = CalculateDistributionScore(result.DistributionValidation);
                score += distScore * 0.25;
                components++;
            }

            // Accuracy validation (25% weight) - only if actual results available
            if (result.AccuracyValidation != null)
            {
                var accScore = result.AccuracyValidation.AccuracyPercentage / 100.0;
                score += accScore * 0.25;
                components++;
            }
            else
            {
                // If no accuracy data, redistribute weight
                score = score / (components * 0.25) * 0.75; // Normalize to 75% and redistribute
            }

            return Math.Max(0, Math.Min(1, score));
        }

        private double CalculateStatisticalScore(StatisticalValidation stats)
        {
            double score = 0;

            // Basic validity checks
            if (stats.MeanValid) score += 0.2;
            if (stats.SumValid) score += 0.2;
            if (stats.VarianceValid) score += 0.2;

            // Normality and distribution quality
            score += stats.NormalityScore * 0.2;

            // Outlier penalty
            if (!stats.HasOutliers) score += 0.1;

            // Entropy (information content)
            var normalizedEntropy = Math.Min(1.0, stats.Entropy / 3.0); // Max entropy ≈ 3 for 5 ranges
            score += normalizedEntropy * 0.1;

            return Math.Max(0, Math.Min(1, score));
        }

        private double CalculatePatternScore(PatternValidation patterns)
        {
            double score = 0;

            // Consecutive patterns (moderate is good)
            var consecutiveScore = patterns.ConsecutivePairs >= 2 && patterns.ConsecutivePairs <= 5 ? 0.3 : 0.1;
            score += consecutiveScore;

            // Gap regularity
            var gapRegularity = 1.0 / (1.0 + patterns.GapVariance);
            score += gapRegularity * 0.2;

            // Pattern regularity
            score += patterns.RegularityScore * 0.2;

            // Clustering (avoid too much clustering)
            var clusterScore = patterns.ClusterAnalysis.Count <= 3 ? 0.2 : 0.1;
            score += clusterScore;

            // Isolated numbers (some isolation is good for diversity)
            var isolationScore = patterns.IsolatedNumbers.Count >= 2 && patterns.IsolatedNumbers.Count <= 6 ? 0.1 : 0.05;
            score += isolationScore;

            return Math.Max(0, Math.Min(1, score));
        }

        private double CalculateDistributionScore(DistributionValidation dist)
        {
            double score = 0;

            // Range balance
            score += dist.RangeBalance * 0.3;

            // Quintile balance
            score += dist.QuintileBalance * 0.2;

            // Column balance (coordinate system)
            score += dist.ColumnBalance * 0.2;

            // Even/odd balance
            if (dist.EvenOddBalance) score += 0.1;

            // Uniformity
            score += dist.UniformityScore * 0.2;

            return Math.Max(0, Math.Min(1, score));
        }

        public ValidationReport GenerateValidationReport(int days = 30)
        {
            var cutoffDate = DateTime.UtcNow.AddDays(-days);
            var recentValidations = validationHistory.Where(v => v.Timestamp >= cutoffDate).ToList();

            var report = new ValidationReport
            {
                ReportPeriod = days,
                TotalValidations = recentValidations.Count,
                ModelsEvaluated = recentValidations.Select(v => v.ModelName).Distinct().Count(),
                GeneratedAt = DateTime.UtcNow
            };

            // Model performance summary
            report.ModelPerformance = modelTrackers.Values
                .Where(t => t.LastUpdated >= cutoffDate)
                .OrderByDescending(t => t.AverageAccuracy)
                .ToList();

            // Best performing predictions
            report.BestPredictions = recentValidations
                .Where(v => v.AccuracyValidation != null)
                .OrderByDescending(v => v.AccuracyValidation.AccuracyPercentage)
                .Take(10)
                .ToList();

            // Statistical insights
            report.StatisticalInsights = GenerateStatisticalInsights(recentValidations);

            // Trend analysis
            report.TrendAnalysis = GenerateOverallTrendAnalysis(recentValidations);

            // Recommendations
            report.Recommendations = GenerateRecommendations(recentValidations);

            return report;
        }

        private StatisticalInsights GenerateStatisticalInsights(List<ValidationResult> validations)
        {
            var insights = new StatisticalInsights();

            var validAccuracies = validations
                .Where(v => v.AccuracyValidation != null)
                .Select(v => v.AccuracyValidation.AccuracyPercentage)
                .ToList();

            if (validAccuracies.Any())
            {
                insights.AverageAccuracy = validAccuracies.Average();
                insights.MedianAccuracy = CalculateMedian(validAccuracies.Select(a => (int)a).ToList());
                insights.AccuracyStandardDeviation = CalculateStandardDeviation(validAccuracies.Select(a => (int)a).ToList());
                insights.BestAccuracy = validAccuracies.Max();
                insights.WorstAccuracy = validAccuracies.Min();
            }

            // Statistical validation patterns
            var statValidations = validations.Where(v => v.StatisticalValidation != null).ToList();
            if (statValidations.Any())
            {
                insights.AverageEntropy = statValidations.Average(v => v.StatisticalValidation.Entropy);
                insights.AverageVariance = statValidations.Average(v => v.StatisticalValidation.Variance);
                insights.NormalityScoreAverage = statValidations.Average(v => v.StatisticalValidation.NormalityScore);
            }

            // Pattern insights
            var patternValidations = validations.Where(v => v.PatternValidation != null).ToList();
            if (patternValidations.Any())
            {
                insights.AverageConsecutivePairs = patternValidations.Average(v => v.PatternValidation.ConsecutivePairs);
                insights.AverageGapVariance = patternValidations.Average(v => v.PatternValidation.GapVariance);
                insights.AverageRegularityScore = patternValidations.Average(v => v.PatternValidation.RegularityScore);
            }

            return insights;
        }

        private TrendAnalysis GenerateOverallTrendAnalysis(List<ValidationResult> validations)
        {
            var trend = new TrendAnalysis();

            var accuracyValidations = validations
                .Where(v => v.AccuracyValidation != null)
                .OrderBy(v => v.Timestamp)
                .ToList();

            if (accuracyValidations.Count >= 5)
            {
                var accuracies = accuracyValidations.Select(v => v.AccuracyValidation.AccuracyPercentage).ToList();
                trend.AccuracyTrend = CalculateLinearTrend(accuracies);
                trend.IsImproving = trend.AccuracyTrend > 0.5;
                trend.TrendStrength = Math.Abs(trend.AccuracyTrend);
            }

            var overallScores = validations.OrderBy(v => v.Timestamp).Select(v => v.OverallScore).ToList();
            if (overallScores.Count >= 5)
            {
                trend.QualityTrend = CalculateLinearTrend(overallScores);
                trend.QualityImproving = trend.QualityTrend > 0.1;
            }

            return trend;
        }

        private List<string> GenerateRecommendations(List<ValidationResult> validations)
        {
            var recommendations = new List<string>();

            // Accuracy-based recommendations
            var avgAccuracy = validations
                .Where(v => v.AccuracyValidation != null)
                .Average(v => v.AccuracyValidation?.AccuracyPercentage ?? 0);

            if (avgAccuracy < 60)
            {
                recommendations.Add("Consider increasing model complexity or ensemble size - accuracy below 60%");
            }
            else if (avgAccuracy > 80)
            {
                recommendations.Add("Excellent accuracy achieved - monitor for overfitting");
            }

            // Pattern-based recommendations
            var avgConsecutive = validations
                .Where(v => v.PatternValidation != null)
                .Average(v => v.PatternValidation?.ConsecutivePairs ?? 0);

            if (avgConsecutive > 7)
            {
                recommendations.Add("High consecutive patterns detected - consider reducing consecutive bias");
            }
            else if (avgConsecutive < 2)
            {
                recommendations.Add("Low consecutive patterns - consider adding pattern recognition");
            }

            // Distribution recommendations
            var balanceIssues = validations.Count(v =>
                v.DistributionValidation?.RangeBalance < 0.7);

            if (balanceIssues > validations.Count * 0.5)
            {
                recommendations.Add("Distribution balance issues detected - improve range balancing");
            }

            // Model-specific recommendations
            var modelPerformances = validations
                .Where(v => v.AccuracyValidation != null)
                .GroupBy(v => v.ModelName)
                .Where(g => g.Count() >= 3)
                .Select(g => new { Model = g.Key, Accuracy = g.Average(v => v.AccuracyValidation.AccuracyPercentage) })
                .OrderBy(m => m.Accuracy)
                .ToList();

            if (modelPerformances.Any())
            {
                var worst = modelPerformances.First();
                var best = modelPerformances.Last();

                if (best.Accuracy - worst.Accuracy > 15)
                {
                    recommendations.Add($"Large performance gap detected: {best.Model} ({best.Accuracy:F1}%) vs {worst.Model} ({worst.Accuracy:F1}%)");
                    recommendations.Add($"Consider reducing weight of {worst.Model} or improving its parameters");
                }
            }

            return recommendations;
        }

        private void SaveValidationReport(ValidationReport report, string filePath = null)
        {
            filePath ??= $"Results/validation_report_{DateTime.Now:yyyyMMdd_HHmmss}.json";

            Directory.CreateDirectory("Results");
            var json = JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(filePath, json);

            Console.WriteLine($"📊 Validation report saved to: {filePath}");
        }

        // Helper methods for statistical calculations
        private double CalculateMedian(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            int mid = sorted.Count / 2;
            return sorted.Count % 2 == 0 ? (sorted[mid - 1] + sorted[mid]) / 2.0 : sorted[mid];
        }

        private double CalculateStandardDeviation(List<int> numbers)
        {
            var mean = numbers.Average();
            var variance = numbers.Sum(n => Math.Pow(n - mean, 2)) / numbers.Count;
            return Math.Sqrt(variance);
        }

        private double CalculateVariance(List<double> numbers)
        {
            var mean = numbers.Average();
            return numbers.Sum(n => Math.Pow(n - mean, 2)) / numbers.Count;
        }

        private double CalculateSkewness(List<int> numbers)
        {
            var mean = numbers.Average();
            var stdDev = CalculateStandardDeviation(numbers);
            if (stdDev == 0) return 0;
            return numbers.Sum(n => Math.Pow((n - mean) / stdDev, 3)) / numbers.Count;
        }

        private double CalculateKurtosis(List<int> numbers)
        {
            var mean = numbers.Average();
            var stdDev = CalculateStandardDeviation(numbers);
            if (stdDev == 0) return 0;
            return numbers.Sum(n => Math.Pow((n - mean) / stdDev, 4)) / numbers.Count - 3;
        }

        private double CalculateEntropy(List<int> numbers)
        {
            var ranges = new int[5];
            foreach (var num in numbers)
            {
                ranges[(num - 1) / 5]++;
            }

            double entropy = 0;
            foreach (var count in ranges)
            {
                if (count > 0)
                {
                    double p = (double)count / numbers.Count;
                    entropy -= p * Math.Log2(p);
                }
            }
            return entropy;
        }

        private double CalculateGiniCoefficient(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var n = sorted.Count;
            var sum = sorted.Sum();

            if (sum == 0) return 0;

            double gini = 0;
            for (int i = 0; i < n; i++)
            {
                gini += (2 * (i + 1) - n - 1) * sorted[i];
            }

            return gini / (n * sum);
        }

        private bool DetectStatisticalOutliers(List<int> numbers)
        {
            var q1 = CalculatePercentile(numbers, 25);
            var q3 = CalculatePercentile(numbers, 75);
            var iqr = q3 - q1;
            var lowerBound = q1 - 1.5 * iqr;
            var upperBound = q3 + 1.5 * iqr;

            return numbers.Any(n => n < lowerBound || n > upperBound);
        }

        private int CountOutliers(List<int> numbers)
        {
            var q1 = CalculatePercentile(numbers, 25);
            var q3 = CalculatePercentile(numbers, 75);
            var iqr = q3 - q1;
            var lowerBound = q1 - 1.5 * iqr;
            var upperBound = q3 + 1.5 * iqr;

            return numbers.Count(n => n < lowerBound || n > upperBound);
        }

        private double CalculatePercentile(List<int> numbers, double percentile)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var index = (percentile / 100.0) * (sorted.Count - 1);
            var lower = (int)Math.Floor(index);
            var upper = (int)Math.Ceiling(index);

            if (lower == upper) return sorted[lower];

            var weight = index - lower;
            return sorted[lower] * (1 - weight) + sorted[upper] * weight;
        }

        private double TestNormality(List<int> numbers)
        {
            // Simplified normality test based on skewness and kurtosis
            var skewness = Math.Abs(CalculateSkewness(numbers));
            var kurtosis = Math.Abs(CalculateKurtosis(numbers));

            // Good normality if skewness near 0 and kurtosis near 0
            var normalityScore = Math.Max(0, 1 - (skewness / 2.0) - (kurtosis / 4.0));
            return Math.Min(1, normalityScore);
        }

        private int CountConsecutivePairs(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            int count = 0;
            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] == sorted[i - 1] + 1) count++;
            }
            return count;
        }

        private List<List<int>> FindConsecutiveGroups(List<int> numbers)
        {
            var groups = new List<List<int>>();
            var sorted = numbers.OrderBy(x => x).ToList();
            var currentGroup = new List<int> { sorted[0] };

            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] == sorted[i - 1] + 1)
                {
                    currentGroup.Add(sorted[i]);
                }
                else
                {
                    if (currentGroup.Count >= 2)
                        groups.Add(currentGroup);
                    currentGroup = new List<int> { sorted[i] };
                }
            }

            if (currentGroup.Count >= 2)
                groups.Add(currentGroup);

            return groups;
        }

        private List<int> CalculateGaps(List<int> numbers)
        {
            var sorted = numbers.OrderBy(x => x).ToList();
            var gaps = new List<int>();

            for (int i = 1; i < sorted.Count; i++)
            {
                gaps.Add(sorted[i] - sorted[i - 1]);
            }

            return gaps;
        }

        private List<List<int>> FindArithmeticSequences(List<int> numbers, int minLength = 3)
        {
            var sequences = new List<List<int>>();
            var sorted = numbers.OrderBy(x => x).ToList();

            for (int i = 0; i < sorted.Count - minLength + 1; i++)
            {
                for (int j = i + 1; j < sorted.Count - minLength + 2; j++)
                {
                    var diff = sorted[j] - sorted[i];
                    var sequence = new List<int> { sorted[i], sorted[j] };

                    int next = sorted[j] + diff;
                    while (sorted.Contains(next))
                    {
                        sequence.Add(next);
                        next += diff;
                    }

                    if (sequence.Count >= minLength)
                    {
                        sequences.Add(sequence);
                    }
                }
            }

            return sequences.Distinct().ToList();
        }

        private List<List<int>> AnalyzeClusters(List<int> numbers, int maxGap = 3)
        {
            var clusters = new List<List<int>>();
            var sorted = numbers.OrderBy(x => x).ToList();
            var currentCluster = new List<int> { sorted[0] };

            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] - sorted[i - 1] <= maxGap)
                {
                    currentCluster.Add(sorted[i]);
                }
                else
                {
                    if (currentCluster.Count >= 2)
                        clusters.Add(currentCluster);
                    currentCluster = new List<int> { sorted[i] };
                }
            }

            if (currentCluster.Count >= 2)
                clusters.Add(currentCluster);

            return clusters;
        }

        private List<int> FindIsolatedNumbers(List<int> numbers, int minGap = 5)
        {
            var isolated = new List<int>();
            var sorted = numbers.OrderBy(x => x).ToList();

            for (int i = 0; i < sorted.Count; i++)
            {
                bool isIsolated = true;

                // Check previous number
                if (i > 0 && sorted[i] - sorted[i - 1] < minGap)
                    isIsolated = false;

                // Check next number
                if (i < sorted.Count - 1 && sorted[i + 1] - sorted[i] < minGap)
                    isIsolated = false;

                if (isIsolated)
                    isolated.Add(sorted[i]);
            }

            return isolated;
        }

        private double CalculatePatternRegularity(List<int> numbers)
        {
            var gaps = CalculateGaps(numbers);
            if (!gaps.Any()) return 0;

            var avgGap = gaps.Average();
            var gapVariance = CalculateVariance(gaps.Select(g => (double)g).ToList());

            return 1.0 / (1.0 + Math.Sqrt(gapVariance));
        }

        private List<List<int>> FindFibonacciLikeSequences(List<int> numbers)
        {
            var sequences = new List<List<int>>();
            var sorted = numbers.OrderBy(x => x).ToList();

            for (int i = 0; i < sorted.Count - 2; i++)
            {
                for (int j = i + 1; j < sorted.Count - 1; j++)
                {
                    var sequence = new List<int> { sorted[i], sorted[j] };
                    var next = sorted[i] + sorted[j];

                    while (sorted.Contains(next))
                    {
                        sequence.Add(next);
                        var temp = sequence[sequence.Count - 2];
                        next = sequence[sequence.Count - 1] + temp;
                    }

                    if (sequence.Count >= 3)
                    {
                        sequences.Add(sequence);
                    }
                }
            }

            return sequences;
        }

        private double CalculateRangeBalance(int low, int mid, int high)
        {
            // Expected distribution: roughly 5, 5, 4 for balanced
            var expected = new[] { 5.0, 5.0, 4.0 };
            var actual = new[] { (double)low, (double)mid, (double)high };

            var variance = 0.0;
            for (int i = 0; i < 3; i++)
            {
                variance += Math.Pow(actual[i] - expected[i], 2);
            }

            return Math.Max(0, 1 - (variance / 20.0)); // Normalize
        }

        private int[] CalculateQuintileDistribution(List<int> numbers)
        {
            var quintiles = new int[5];
            foreach (var num in numbers)
            {
                quintiles[(num - 1) / 5]++;
            }
            return quintiles;
        }

        private double CalculateQuintileBalance(int[] quintiles)
        {
            var expected = 14.0 / 5; // ~2.8 per quintile
            var variance = quintiles.Sum(q => Math.Pow(q - expected, 2)) / 5;
            return Math.Max(0, 1 - (variance / 10.0));
        }

        private int[] CalculateColumnDistribution(List<int> numbers)
        {
            var columns = new int[3];
            foreach (var num in numbers)
            {
                if (num >= 1 && num <= 9) columns[0]++;
                else if (num >= 10 && num <= 19) columns[1]++;
                else if (num >= 20 && num <= 25) columns[2]++;
            }
            return columns;
        }

        private double CalculateColumnBalance(int[] columns)
        {
            // Expected: ~5, ~6, ~3 based on available numbers per column
            var expected = new[] { 5.04, 5.6, 3.36 };
            var variance = 0.0;
            for (int i = 0; i < 3; i++)
            {
                variance += Math.Pow(columns[i] - expected[i], 2);
            }
            return Math.Max(0, 1 - (variance / 15.0));
        }

        private bool IsPrime(int number)
        {
            if (number < 2) return false;
            for (int i = 2; i <= Math.Sqrt(number); i++)
            {
                if (number % i == 0) return false;
            }
            return true;
        }

        private int[] CalculateDensityMap(List<int> numbers)
        {
            var density = new int[5]; // 5 regions
            foreach (var num in numbers)
            {
                density[(num - 1) / 5]++;
            }
            return density;
        }

        private double CalculateUniformityScore(int[] densityMap)
        {
            var expected = 14.0 / 5; // ~2.8 per region
            var variance = densityMap.Sum(d => Math.Pow(d - expected, 2)) / 5;
            return Math.Max(0, 1 - (variance / 10.0));
        }

        private bool IsHistoricallyUnique(List<int> prediction)
        {
            return !validationHistory.Any(v =>
                v.Prediction.SequenceEqual(prediction));
        }

        private double CalculateHistoricalSimilarity(List<int> prediction)
        {
            if (!validationHistory.Any()) return 0;

            var maxSimilarity = validationHistory.Max(v =>
                v.Prediction.Intersect(prediction).Count() / 14.0);

            return maxSimilarity;
        }

        private double CalculateEnsembleUniqueness(List<int> prediction, List<List<int>> ensemblePredictions)
        {
            if (!ensemblePredictions.Any()) return 1.0;

            var similarities = ensemblePredictions.Select(p =>
                p.Intersect(prediction).Count() / 14.0);

            return 1.0 - similarities.Average();
        }

        private double CalculateTheoreticalProbability()
        {
            // C(25,14) = 4,457,400
            return 1.0 / 4457400.0;
        }

        private double CalculatePositionAccuracy(List<int> prediction, List<int> actual)
        {
            var predSorted = prediction.OrderBy(x => x).ToList();
            var actSorted = actual.OrderBy(x => x).ToList();

            int matches = 0;
            for (int i = 0; i < Math.Min(predSorted.Count, actSorted.Count); i++)
            {
                if (predSorted[i] == actSorted[i]) matches++;
            }

            return (double)matches / prediction.Count * 100.0;
        }

        private int CountNearMisses(List<int> prediction, List<int> actual, int tolerance = 1)
        {
            int nearMisses = 0;
            foreach (var pred in prediction)
            {
                for (int i = -tolerance; i <= tolerance; i++)
                {
                    if (i != 0 && actual.Contains(pred + i))
                    {
                        nearMisses++;
                        break;
                    }
                }
            }
            return nearMisses;
        }

        private int CountCloseMatches(List<int> prediction, List<int> actual, int tolerance = 2)
        {
            int closeMatches = 0;
            foreach (var pred in prediction)
            {
                for (int i = -tolerance; i <= tolerance; i++)
                {
                    if (actual.Contains(pred + i))
                    {
                        closeMatches++;
                        break;
                    }
                }
            }
            return closeMatches;
        }

        private double CalculateDistributionSimilarity(List<int> prediction, List<int> actual)
        {
            var predDist = CalculateQuintileDistribution(prediction);
            var actDist = CalculateQuintileDistribution(actual);

            double similarity = 0;
            for (int i = 0; i < 5; i++)
            {
                similarity += 1.0 - Math.Abs(predDist[i] - actDist[i]) / 14.0;
            }

            return similarity / 5.0;
        }

        private double CalculatePatternSimilarity(List<int> prediction, List<int> actual)
        {
            var predConsecutive = CountConsecutivePairs(prediction);
            var actConsecutive = CountConsecutivePairs(actual);

            var consecutiveSim = 1.0 - Math.Abs(predConsecutive - actConsecutive) / 13.0;

            var predGaps = CalculateGaps(prediction);
            var actGaps = CalculateGaps(actual);

            var avgPredGap = predGaps.Average();
            var avgActGap = actGaps.Average();

            var gapSim = 1.0 - Math.Abs(avgPredGap - avgActGap) / 25.0;

            return (consecutiveSim + gapSim) / 2.0;
        }

        private double CalculateStatisticalSimilarity(List<int> prediction, List<int> actual)
        {
            var predMean = prediction.Average();
            var actMean = actual.Average();
            var meanSim = 1.0 - Math.Abs(predMean - actMean) / 25.0;

            var predVar = CalculateVariance(prediction.Select(p => (double)p).ToList());
            var actVar = CalculateVariance(actual.Select(a => (double)a).ToList());
            var varSim = 1.0 - Math.Abs(predVar - actVar) / 100.0;

            return (meanSim + varSim) / 2.0;
        }

        private (double lower, double upper) CalculateAccuracyConfidenceInterval(double accuracy, double confidence = 0.95)
        {
            var z = 1.96; // 95% confidence
            var n = 14; // sample size
            var p = accuracy / 100.0;
            var margin = z * Math.Sqrt(p * (1 - p) / n);

            return (Math.Max(0, p - margin) * 100, Math.Min(1, p + margin) * 100);
        }

        private bool TestStatisticalSignificance(List<int> prediction, List<int> actual, double alpha = 0.05)
        {
            // Chi-square test for independence
            var matches = prediction.Intersect(actual).Count();
            var expected = (prediction.Count * actual.Count) / 25.0; // Expected by chance
            var chiSquare = Math.Pow(matches - expected, 2) / expected;

            // Critical value for df=1 at α=0.05 is 3.841
            return chiSquare > 3.841;
        }

        private TrendDirection AnalyzeTrend(List<double> values)
        {
            if (values.Count < 3) return new TrendDirection { Direction = "Insufficient Data" };

            var trend = CalculateLinearTrend(values);

            return new TrendDirection
            {
                Direction = trend > 0.5 ? "Improving" : trend < -0.5 ? "Declining" : "Stable",
                Slope = trend,
                Strength = Math.Abs(trend)
            };
        }

        private double CalculateLinearTrend(List<double> values)
        {
            var n = values.Count;
            var sumX = 0.0;
            var sumY = values.Sum();
            var sumXY = 0.0;
            var sumX2 = 0.0;

            for (int i = 0; i < n; i++)
            {
                sumX += i;
                sumXY += i * values[i];
                sumX2 += i * i;
            }

            var slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
            return slope;
        }

        private double CalculateModelConfidence(AccuracyTracker tracker)
        {
            if (tracker.AccuracyHistory.Count < 3) return 0.5;

            var recentAccuracy = tracker.AccuracyHistory.TakeLast(5).Average();
            var consistency = 1.0 - (tracker.AccuracyStandardDeviation / 100.0);
            var trend = tracker.TrendAnalysis?.Strength ?? 0;

            return (recentAccuracy / 100.0 * 0.6) + (consistency * 0.3) + (Math.Max(0, trend) * 0.1);
        }

        public List<ValidationResult> GetValidationHistory() => validationHistory;
        public Dictionary<string, AccuracyTracker> GetModelTrackers() => modelTrackers;
        public ValidationReport GetLastReport() => GenerateValidationReport(30);
    }

    // Data classes for validation results
    public class ValidationResult
    {
        public string ModelName { get; set; }
        public int SeriesId { get; set; }
        public List<int> Prediction { get; set; }
        public List<int> Actual { get; set; }
        public DateTime Timestamp { get; set; }
        public Dictionary<string, object> Metadata { get; set; }

        public StatisticalValidation StatisticalValidation { get; set; }
        public PatternValidation PatternValidation { get; set; }
        public DistributionValidation DistributionValidation { get; set; }
        public UniquenessValidation UniquenessValidation { get; set; }
        public AccuracyValidation AccuracyValidation { get; set; }

        public double OverallScore { get; set; }
    }

    public class StatisticalValidation
    {
        public double Mean { get; set; }
        public double Median { get; set; }
        public double StandardDeviation { get; set; }
        public double Variance { get; set; }
        public double Range { get; set; }
        public double Sum { get; set; }
        public double Skewness { get; set; }
        public double Kurtosis { get; set; }
        public double Entropy { get; set; }
        public double GiniCoefficient { get; set; }

        public bool MeanValid { get; set; }
        public bool SumValid { get; set; }
        public bool VarianceValid { get; set; }
        public bool HasOutliers { get; set; }
        public int OutlierCount { get; set; }
        public double NormalityScore { get; set; }
    }

    public class PatternValidation
    {
        public int ConsecutivePairs { get; set; }
        public List<List<int>> ConsecutiveGroups { get; set; }
        public int MaxConsecutiveLength { get; set; }
        public List<int> Gaps { get; set; }
        public double AverageGap { get; set; }
        public double GapVariance { get; set; }
        public int MaxGap { get; set; }
        public int MinGap { get; set; }
        public List<List<int>> ArithmeticSequences { get; set; }
        public bool HasArithmeticPattern { get; set; }
        public List<List<int>> ClusterAnalysis { get; set; }
        public List<int> IsolatedNumbers { get; set; }
        public double RegularityScore { get; set; }
        public List<List<int>> FibonacciLikeSequences { get; set; }
    }

    public class DistributionValidation
    {
        public int LowRange { get; set; }
        public int MidRange { get; set; }
        public int HighRange { get; set; }
        public double RangeBalance { get; set; }
        public int[] QuintileDistribution { get; set; }
        public double QuintileBalance { get; set; }
        public int[] ColumnDistribution { get; set; }
        public double ColumnBalance { get; set; }
        public int EvenCount { get; set; }
        public int OddCount { get; set; }
        public bool EvenOddBalance { get; set; }
        public int PrimeCount { get; set; }
        public int CompositeCount { get; set; }
        public int[] DensityMap { get; set; }
        public double UniformityScore { get; set; }
    }

    public class UniquenessValidation
    {
        public bool HasDuplicates { get; set; }
        public int UniqueCount { get; set; }
        public bool IsHistoricallyUnique { get; set; }
        public double SimilarityToHistory { get; set; }
        public double EnsembleUniqueness { get; set; }
        public double TheoreticalProbability { get; set; }
    }

    public class AccuracyValidation
    {
        public int ExactMatches { get; set; }
        public double AccuracyPercentage { get; set; }
        public double PositionAccuracy { get; set; }
        public int NearMisses { get; set; }
        public int CloseMatches { get; set; }
        public double DistributionSimilarity { get; set; }
        public double PatternSimilarity { get; set; }
        public double StatisticalSimilarity { get; set; }
        public (double lower, double upper) ConfidenceInterval { get; set; }
        public bool IsStatisticallySignificant { get; set; }
    }

    public class AccuracyTracker
    {
        public string ModelName { get; set; }
        public List<double> AccuracyHistory { get; set; } = new();
        public List<double> OverallScoreHistory { get; set; } = new();
        public double AverageAccuracy { get; set; }
        public double BestAccuracy { get; set; }
        public double WorstAccuracy { get; set; }
        public double AccuracyStandardDeviation { get; set; }
        public double ModelConfidence { get; set; }
        public TrendDirection TrendAnalysis { get; set; }
        public DateTime LastUpdated { get; set; }

        public void AddResult(ValidationResult result)
        {
            if (result.AccuracyValidation != null)
            {
                AccuracyHistory.Add(result.AccuracyValidation.AccuracyPercentage);
            }
            OverallScoreHistory.Add(result.OverallScore);
            LastUpdated = result.Timestamp;
        }

        public void UpdateStatistics()
        {
            if (AccuracyHistory.Any())
            {
                AverageAccuracy = AccuracyHistory.Average();
                BestAccuracy = AccuracyHistory.Max();
                WorstAccuracy = AccuracyHistory.Min();

                if (AccuracyHistory.Count > 1)
                {
                    var mean = AccuracyHistory.Average();
                    var variance = AccuracyHistory.Sum(a => Math.Pow(a - mean, 2)) / AccuracyHistory.Count;
                    AccuracyStandardDeviation = Math.Sqrt(variance);
                }
            }
        }
    }

    public class ValidationReport
    {
        public int ReportPeriod { get; set; }
        public int TotalValidations { get; set; }
        public int ModelsEvaluated { get; set; }
        public DateTime GeneratedAt { get; set; }
        public List<AccuracyTracker> ModelPerformance { get; set; }
        public List<ValidationResult> BestPredictions { get; set; }
        public StatisticalInsights StatisticalInsights { get; set; }
        public TrendAnalysis TrendAnalysis { get; set; }
        public List<string> Recommendations { get; set; }
    }

    public class StatisticalInsights
    {
        public double AverageAccuracy { get; set; }
        public double MedianAccuracy { get; set; }
        public double AccuracyStandardDeviation { get; set; }
        public double BestAccuracy { get; set; }
        public double WorstAccuracy { get; set; }
        public double AverageEntropy { get; set; }
        public double AverageVariance { get; set; }
        public double NormalityScoreAverage { get; set; }
        public double AverageConsecutivePairs { get; set; }
        public double AverageGapVariance { get; set; }
        public double AverageRegularityScore { get; set; }
    }

    public class TrendAnalysis
    {
        public double AccuracyTrend { get; set; }
        public bool IsImproving { get; set; }
        public double TrendStrength { get; set; }
        public double QualityTrend { get; set; }
        public bool QualityImproving { get; set; }
    }

    public class TrendDirection
    {
        public string Direction { get; set; }
        public double Slope { get; set; }
        public double Strength { get; set; }
    }

    public class StatisticalBaseline
    {
        public double RandomAccuracy { get; set; } = 56.0; // C(25,14) baseline
        public double ExpectedMean { get; set; } = 13.0;
        public double ExpectedSum { get; set; } = 182.0;
        public double ExpectedVariance { get; set; } = 52.0;
    }
}
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using DataProcessor.Connections;

namespace DataProcessor.Models
{
    public class DynamicLearningModel
    {
        private readonly DatabaseConnection dbConnection;
        private Dictionary<int, double> numberWeights;
        private Dictionary<int, double> gradients;
        private Dictionary<int, double> numberFrequencies;
        private Dictionary<int, double> learningRates;
        private readonly Random random;
        private double baseLearningRate = 0.01;
        private int trainingEpochs;
        private int totalTrainingSamples;

        public DynamicLearningModel(string modelPath = null)
        {
            dbConnection = new DatabaseConnection();
            numberWeights = new Dictionary<int, double>();
            gradients = new Dictionary<int, double>();
            numberFrequencies = new Dictionary<int, double>();
            learningRates = new Dictionary<int, double>();
            random = new Random(42);
            trainingEpochs = 0;
            totalTrainingSamples = 0;

            if (!string.IsNullOrEmpty(modelPath) && File.Exists(modelPath))
            {
                LoadModel(modelPath);
                Console.WriteLine($"🔄 Loaded pre-trained model from: {modelPath}");
            }
            else
            {
                InitializeWeights();
            }
        }

        private void InitializeWeights()
        {
            // Initialize all weights to neutral values (no hard-coding)
            for (int i = 1; i <= 25; i++)
            {
                numberWeights[i] = 1.0; // Neutral starting point
                gradients[i] = 0.0;
                numberFrequencies[i] = 0;
                learningRates[i] = baseLearningRate;
            }
        }

        private void ResetWeights()
        {
            // Reset weights to prevent saturation
            for (int i = 1; i <= 25; i++)
            {
                if (numberWeights[i] >= 9999.0) // Near saturation
                {
                    numberWeights[i] = random.NextDouble() * 2.0 + 0.5; // Random 0.5-2.5
                    Console.WriteLine($"   🔄 Reset saturated weight for number {i:D2}");
                }
            }
        }

        public void TrainWithHistoricalData(int minimumEvents = 100, int maxHours = 0)
        {
            Console.WriteLine($"🤖 Starting dynamic training with minimum {minimumEvents} events...");
            if (maxHours > 0)
            {
                Console.WriteLine($"⏱️  Training will run for maximum {maxHours} hours");
            }

            // Load all available historical data
            var allHistoricalData = dbConnection.LoadHistoricalDataBefore(3127);

            if (allHistoricalData.Count < minimumEvents)
            {
                Console.WriteLine($"⚠️  Warning: Only {allHistoricalData.Count} events available, minimum {minimumEvents} requested");
            }

            var trainingData = allHistoricalData.TakeLast(Math.Max(minimumEvents, allHistoricalData.Count)).ToList();
            Console.WriteLine($"📊 Training with {trainingData.Count} historical events");

            // Reset training state
            totalTrainingSamples = 0;
            trainingEpochs = 0;

            var startTime = DateTime.Now;
            var maxTrainingTime = maxHours > 0 ? TimeSpan.FromHours(maxHours) : TimeSpan.MaxValue;

            // Extended training with time limit
            int maxEpochs = maxHours > 0 ? int.MaxValue : 10; // Unlimited epochs if time-based training
            double bestLoss = double.MaxValue;
            int epochsWithoutImprovement = 0;
            const int earlyStoppingPatience = 20; // Stop if no improvement for 20 epochs

            for (int epoch = 0; epoch < maxEpochs; epoch++)
            {
                // Check time limit
                if (DateTime.Now - startTime > maxTrainingTime)
                {
                    Console.WriteLine($"⏱️  Time limit reached ({maxHours} hours). Stopping training.");
                    break;
                }

                trainingEpochs++;
                Console.WriteLine($"🔄 Training Epoch {epoch + 1} - Elapsed: {(DateTime.Now - startTime).TotalMinutes:F1} min");

                double epochLoss = 0.0;
                int epochSamples = 0;

                // Train on each series multiple times for extended training
                int repetitions = maxHours > 0 ? 3 : 1; // More repetitions for extended training
                for (int rep = 0; rep < repetitions; rep++)
                {
                    // Shuffle training data for better learning
                    var shuffledData = trainingData.OrderBy(x => random.Next()).ToList();

                    foreach (var series in shuffledData)
                    {
                        foreach (var combination in series.AllCombinations)
                        {
                            // Generate prediction with current weights
                            var prediction = GeneratePrediction(series.SeriesId, 14);

                            // Calculate loss and update weights
                            double sampleLoss = CalculateLossAndUpdateWeights(prediction, combination);
                            epochLoss += sampleLoss;
                            epochSamples++;
                            totalTrainingSamples++;
                        }
                    }
                }

                double avgEpochLoss = epochLoss / epochSamples;
                Console.WriteLine($"   Epoch {epoch + 1} Loss: {avgEpochLoss:F4} (Best: {bestLoss:F4})");

                // Track best loss and early stopping
                if (avgEpochLoss < bestLoss)
                {
                    bestLoss = avgEpochLoss;
                    epochsWithoutImprovement = 0;
                    Console.WriteLine($"   🎯 New best loss achieved!");
                }
                else
                {
                    epochsWithoutImprovement++;
                }

                // Improved learning rate management
                if (epoch > 0 && avgEpochLoss > previousEpochLoss)
                {
                    // Reduce learning rate if loss increased
                    baseLearningRate *= 0.95;
                    for (int i = 1; i <= 25; i++)
                    {
                        learningRates[i] = baseLearningRate;
                    }
                    Console.WriteLine($"   📉 Learning rate reduced to: {baseLearningRate:F6}");
                }

                // Reset saturated weights every 50 epochs to enable continued learning
                if ((epoch + 1) % 50 == 0)
                {
                    ResetWeights();
                }

                // Prevent learning rate from becoming too small
                if (baseLearningRate < 0.000001)
                {
                    baseLearningRate = 0.001; // Reset to meaningful value
                    Console.WriteLine($"   🔄 Learning rate reset to: {baseLearningRate:F6}");
                }

                previousEpochLoss = avgEpochLoss;

                // Early stopping for extended training (only if time-based) - DISABLED for full hour training
                // Commenting out early stopping to ensure full hour training
                /*
                if (maxHours > 0 && epochsWithoutImprovement >= earlyStoppingPatience)
                {
                    Console.WriteLine($"   🛑 Early stopping: No improvement for {earlyStoppingPatience} epochs");
                    break;
                }
                */

                // Progress report every 10 epochs for extended training
                if (maxHours > 0 && (epoch + 1) % 10 == 0)
                {
                    Console.WriteLine($"   📊 Progress: {trainingEpochs} epochs, {totalTrainingSamples:N0} samples, {(DateTime.Now - startTime).TotalMinutes:F1} min elapsed");
                    PrintTopWeights(5); // Show top 5 weights during training
                }

                // Small pause to prevent overheating during extended training
                if (maxHours > 0 && epoch % 20 == 0)
                {
                    System.Threading.Thread.Sleep(50);
                }
            }

            var totalTrainingTime = DateTime.Now - startTime;
            Console.WriteLine($"✅ Dynamic training completed:");
            Console.WriteLine($"   - Training Time: {totalTrainingTime.TotalMinutes:F1} minutes");
            Console.WriteLine($"   - Epochs: {trainingEpochs}");
            Console.WriteLine($"   - Samples: {totalTrainingSamples:N0}");
            Console.WriteLine($"   - Final Learning Rate: {baseLearningRate:F6}");
            Console.WriteLine($"   - Best Loss Achieved: {bestLoss:F4}");

            PrintTopWeights();
        }

        private double previousEpochLoss = double.MaxValue;

        private double CalculateLossAndUpdateWeights(List<int> prediction, List<int> actualCombination)
        {
            // Calculate prediction accuracy as loss metric
            var predictedSet = new HashSet<int>(prediction);
            var actualSet = new HashSet<int>(actualCombination);

            int correctPredictions = predictedSet.Intersect(actualSet).Count();
            int totalPredictions = 14;

            // Loss = 1 - accuracy (0 = perfect, 1 = worst)
            double accuracy = (double)correctPredictions / totalPredictions;
            double loss = 1.0 - accuracy;

            // Update weights based on prediction performance
            UpdateWeightsFromPrediction(prediction, actualCombination, loss);

            return loss;
        }

        private void UpdateWeightsFromPrediction(List<int> prediction, List<int> actualCombination, double loss)
        {
            var predictedSet = new HashSet<int>(prediction);
            var actualSet = new HashSet<int>(actualCombination);

            // Calculate gradients for each number
            for (int number = 1; number <= 25; number++)
            {
                bool wasPredicted = predictedSet.Contains(number);
                bool wasActual = actualSet.Contains(number);

                double gradient = 0.0;

                if (wasActual && !wasPredicted)
                {
                    // Number should have been predicted but wasn't - increase weight
                    gradient = loss * 2.0; // Positive gradient to increase weight
                }
                else if (!wasActual && wasPredicted)
                {
                    // Number was predicted but shouldn't have been - decrease weight
                    gradient = -loss * 1.0; // Negative gradient to decrease weight
                }
                else if (wasActual && wasPredicted)
                {
                    // Correct prediction - small positive reinforcement
                    gradient = loss * 0.1;
                }
                // If neither predicted nor actual, no gradient update needed

                // Apply gradient with learning rate
                double weightUpdate = learningRates[number] * gradient;
                numberWeights[number] += weightUpdate;

                // Ensure weights stay in reasonable bounds
                numberWeights[number] = Math.Max(0.1, Math.Min(10.0, numberWeights[number]));

                // Adaptive learning rate per number
                if (Math.Abs(gradient) > 0.001)
                {
                    learningRates[number] *= 0.999; // Slight decay for active numbers
                }
            }
        }

        public List<int> GeneratePrediction(int targetSeriesId, int count = 14)
        {
            // Use current learned weights to generate prediction
            var weightedNumbers = new List<(int number, double score)>();

            for (int number = 1; number <= 25; number++)
            {
                // Base score from learned weight
                double score = numberWeights[number];

                // Add some randomness for exploration
                double randomFactor = (random.NextDouble() - 0.5) * 0.1;
                score += randomFactor;

                weightedNumbers.Add((number, score));
            }

            // Select top weighted numbers
            var selectedNumbers = weightedNumbers
                .OrderByDescending(x => x.score)
                .Take(count)
                .Select(x => x.number)
                .OrderBy(x => x)
                .ToList();

            return selectedNumbers;
        }

        public List<int> PredictBestCombination(int targetSeriesId)
        {
            return GeneratePrediction(targetSeriesId, 14);
        }

        private void PrintTopWeights(int count = 15)
        {
            var topWeights = numberWeights.OrderByDescending(x => x.Value).Take(count);
            Console.WriteLine($"\n🎯 Top {count} Learned Weights:");
            foreach (var weight in topWeights)
            {
                Console.WriteLine($"   Number {weight.Key:D2}: {weight.Value:F3}");
            }
        }

        public Dictionary<string, object> GetModelAnalysis()
        {
            var topWeights = numberWeights.OrderByDescending(x => x.Value).Take(15).ToDictionary(x => x.Key, x => x.Value);
            var bottomWeights = numberWeights.OrderBy(x => x.Value).Take(10).ToDictionary(x => x.Key, x => x.Value);

            return new Dictionary<string, object>
            {
                ["ModelType"] = "Dynamic Learning Model (No Hard-coding)",
                ["TrainingEpochs"] = trainingEpochs,
                ["TotalSamples"] = totalTrainingSamples,
                ["FinalLearningRate"] = baseLearningRate,
                ["TopWeights"] = topWeights,
                ["BottomWeights"] = bottomWeights,
                ["WeightRange"] = $"{numberWeights.Values.Min():F3} - {numberWeights.Values.Max():F3}"
            };
        }

        private void LoadModel(string filePath)
        {
            try
            {
                string jsonContent = File.ReadAllText(filePath);
                using JsonDocument document = JsonDocument.Parse(jsonContent);
                var root = document.RootElement;

                if (root.TryGetProperty("Weights", out var weightsProperty))
                {
                    foreach (var weight in weightsProperty.EnumerateObject())
                    {
                        if (int.TryParse(weight.Name, out int number) && number >= 1 && number <= 25)
                        {
                            numberWeights[number] = weight.Value.GetDouble();
                        }
                    }
                }

                if (root.TryGetProperty("LearningRates", out var learningRatesProperty))
                {
                    foreach (var rate in learningRatesProperty.EnumerateObject())
                    {
                        if (int.TryParse(rate.Name, out int number) && number >= 1 && number <= 25)
                        {
                            learningRates[number] = rate.Value.GetDouble();
                        }
                    }
                }

                if (root.TryGetProperty("BaseLearningRate", out var baseLrProperty))
                {
                    baseLearningRate = baseLrProperty.GetDouble();
                }

                if (root.TryGetProperty("TrainingEpochs", out var epochsProperty))
                {
                    trainingEpochs = epochsProperty.GetInt32();
                }

                if (root.TryGetProperty("TotalSamples", out var samplesProperty))
                {
                    totalTrainingSamples = samplesProperty.GetInt32();
                }

                Console.WriteLine($"✅ Model loaded: {trainingEpochs} epochs, {totalTrainingSamples:N0} samples");
                Console.WriteLine($"   📊 Weight range: {numberWeights.Values.Min():F3} - {numberWeights.Values.Max():F3}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Failed to load model: {ex.Message}");
                Console.WriteLine("🔄 Falling back to neutral weights initialization");
                InitializeWeights();
            }
        }

        public void SaveModel(string filePath)
        {
            var modelData = new
            {
                Timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                ModelType = "Dynamic Learning Model",
                TrainingEpochs = trainingEpochs,
                TotalSamples = totalTrainingSamples,
                Weights = numberWeights,
                LearningRates = learningRates,
                BaseLearningRate = baseLearningRate,
                Analysis = GetModelAnalysis()
            };

            string json = System.Text.Json.JsonSerializer.Serialize(modelData, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
            System.IO.File.WriteAllText(filePath, json);
            Console.WriteLine($"💾 Model saved to: {filePath}");
        }
    }
}
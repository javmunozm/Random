using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor.Models
{
    // A point in N-dimensional space, representing a number's embedding
    public class NonEuclideanPoint
    {
        public double[] Coordinates { get; set; }
        public int Dimension => Coordinates.Length;

        public NonEuclideanPoint(int dimension) { Coordinates = new double[dimension]; }
        public NonEuclideanPoint(double[] coordinates) { Coordinates = coordinates; }

        public double HyperbolicDistance(NonEuclideanPoint other)
        {
            double squaredNorm = Coordinates.Sum(x => x * x);
            double otherSquaredNorm = other.Coordinates.Sum(x => x * x);
            double squaredEuclideanDist = Coordinates.Zip(other.Coordinates, (a, b) => (a - b) * (a - b)).Sum();
            
            double numerator = 2 * squaredEuclideanDist;
            double denominator = (1 - squaredNorm) * (1 - otherSquaredNorm);

            if (Math.Abs(denominator) < 1e-10) return double.PositiveInfinity;
            return Math.Acosh(1 + numerator / denominator);
        }
    }

    // The geometric space where numbers live
    public class NonEuclideanManifold
    {
        public int Dimension { get; }
        public string GeometryType { get; }
        public Dictionary<int, NonEuclideanPoint> NumberEmbeddings { get; set; } = new();

        public NonEuclideanManifold(int dimension, string geometryType)
        {
            Dimension = dimension;
            GeometryType = geometryType;
            InitializeNumberEmbeddings();
        }

        private void InitializeNumberEmbeddings()
        {
            var random = new Random(42);
            for (int number = 1; number <= 25; number++)
            {
                var coords = new double[Dimension];
                for (int d = 0; d < Dimension; d++)
                {
                    coords[d] = (random.NextDouble() * 2 - 1) * 0.5; // Start near the origin
                }
                NumberEmbeddings[number] = new NonEuclideanPoint(coords);
            }
        }

        public double Geodesic(int num1, int num2)
        {
            // For now, we focus on hyperbolic as it's often best for hierarchical data
            return NumberEmbeddings[num1].HyperbolicDistance(NumberEmbeddings[num2]);
        }
    }

    public class NonEuclideanGenerativeModel
    {
        private readonly List<NonEuclideanManifold> manifolds = new();
        private readonly List<List<int>> historicalCombinations = new();
        private readonly Random random = new(42);
        private const double LearningRate = 0.01;
        private const int TrainingEpochs = 10;

        public NonEuclideanGenerativeModel()
        {
            // Create manifolds with different dimensionalities to capture different relationships
            manifolds.Add(new NonEuclideanManifold(5, "hyperbolic"));
            manifolds.Add(new NonEuclideanManifold(8, "hyperbolic"));
            manifolds.Add(new NonEuclideanManifold(12, "hyperbolic"));
        }

        public void LearnFromSeries(List<List<int>> combinations)
        {
            historicalCombinations.AddRange(combinations);
            Console.WriteLine($"🧠 Optimizing non-Euclidean embeddings with {combinations.Count} new combinations...");
            
            // Train each manifold on the new data
            foreach (var manifold in manifolds)
            {
                OptimizeManifoldEmbeddings(manifold, combinations);
            }
        }

        // The core learning algorithm
        private void OptimizeManifoldEmbeddings(NonEuclideanManifold manifold, List<List<int>> newCombinations)
        {
            for (int epoch = 0; epoch < TrainingEpochs; epoch++)
            {
                foreach (var combination in newCombinations)
                {
                    // For each number in the combination, pull it closer to the others
                    foreach (int num_i in combination)
                    {
                        var point_i = manifold.NumberEmbeddings[num_i];
                        var gradient = new double[manifold.Dimension];

                        // Calculate gradient: sum of vectors pointing towards other points in the combo
                        foreach (int num_j in combination)
                        {
                            if (num_i == num_j) continue;
                            var point_j = manifold.NumberEmbeddings[num_j];
                            
                            for (int d = 0; d < manifold.Dimension; d++)
                            {
                                // The gradient is the direction that reduces the distance
                                gradient[d] += (point_i.Coordinates[d] - point_j.Coordinates[d]);
                            }
                        }

                        // Update coordinates using gradient descent
                        for (int d = 0; d < manifold.Dimension; d++)
                        {
                            point_i.Coordinates[d] -= LearningRate * gradient[d] / combination.Count;
                        }

                        // Project back into the Poincaré disk to maintain hyperbolic geometry
                        double norm = Math.Sqrt(point_i.Coordinates.Sum(x => x * x));
                        if (norm >= 1.0)
                        {
                            for (int d = 0; d < manifold.Dimension; d++)
                            {
                                point_i.Coordinates[d] /= (norm + 1e-5);
                            }
                        }
                    }
                }
            }
        }

        private NonEuclideanManifold SelectOptimalManifold()
        {
            if (historicalCombinations.Count < 10) return manifolds[0]; // Default if not enough history

            Console.WriteLine("🔍 Selecting optimal manifold based on recent data compactness...");
            double bestScore = double.PositiveInfinity;
            NonEuclideanManifold bestManifold = null;

            var recentHistory = historicalCombinations.TakeLast(10).ToList();

            foreach (var manifold in manifolds)
            {
                double totalDistance = 0;
                foreach (var combo in recentHistory)
                {
                    // Calculate the average intra-combination distance (a measure of compactness)
                    double comboDist = 0;
                    for(int i = 0; i < combo.Count; i++)
                    {
                        for(int j = i + 1; j < combo.Count; j++)
                        {
                            comboDist += manifold.Geodesic(combo[i], combo[j]);
                        }
                    }
                    totalDistance += comboDist / (combo.Count * (combo.Count - 1) / 2);
                }
                
                double avgScore = totalDistance / recentHistory.Count;
                Console.WriteLine($"   Manifold (Dim {manifold.Dimension}) compactness score: {avgScore:F4}");
                if (avgScore < bestScore)
                {
                    bestScore = avgScore;
                    bestManifold = manifold;
                }
            }
            
            Console.WriteLine($"   -> Selected manifold with dimension {bestManifold.Dimension}");
            return bestManifold;
        }

        public List<int> GenerateForSeries(int seriesId)
        {
            var manifold = SelectOptimalManifold();
            Console.WriteLine($"🧭 Generating combination using geometric walk in {manifold.Dimension}D hyperbolic space...");

            var numbers = new List<int>();
            var availableNumbers = Enumerable.Range(1, 25).ToList();
            
            // Start the walk from a "hot" number (one that appeared recently)
            int startNumber = historicalCombinations.LastOrDefault()?.First() ?? random.Next(1, 26);
            numbers.Add(startNumber);
            availableNumbers.Remove(startNumber);

            int currentNumber = startNumber;

            while (numbers.Count < 14)
            {
                // Calculate distances from the current number to all available numbers
                var distances = availableNumbers
                    .Select(n => new { Number = n, Dist = manifold.Geodesic(currentNumber, n) })
                    .ToList();

                // Convert distances to probabilities using softmax (smaller distance = higher probability)
                double maxDist = distances.Max(d => d.Dist); // For numerical stability
                var scores = distances.Select(d => Math.Exp(-d.Dist / (maxDist + 1e-5))).ToList();
                double sumScores = scores.Sum();
                var probabilities = scores.Select(s => s / sumScores).ToList();

                // Probabilistically select the next number
                double roll = random.NextDouble();
                double cumulative = 0;
                int nextNumber = availableNumbers.Last(); // Fallback
                for (int i = 0; i < availableNumbers.Count; i++)
                {
                    cumulative += probabilities[i];
                    if (roll < cumulative)
                    {
                        nextNumber = availableNumbers[i];
                        break;
                    }
                }
                
                numbers.Add(nextNumber);
                availableNumbers.Remove(nextNumber);
                currentNumber = nextNumber;
            }

            return numbers.OrderBy(n => n).ToList();
        }
    }
}
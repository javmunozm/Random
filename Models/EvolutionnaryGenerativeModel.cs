using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor.Models
{
    // Represents a single "gene" or coefficient in our function
    public class EvolutionaryCoefficient
    {
        public double Value { get; set; }
        public int Power { get; set; }
        public double Weight { get; set; } = 1.0;
    }

    // Represents a single "individual" in our population
    public class EvolutionaryFunction
    {
        public List<EvolutionaryCoefficient> Coefficients { get; set; } = new();
        public double Bias { get; set; } = 0.0;
        public double Fitness { get; set; } = 0.0; // Fitness is the new "Accuracy"

        // Evaluates the function to get a score for a given number and series context
        public double Evaluate(int number, int seriesId)
        {
            double result = Bias;
            foreach (var coef in Coefficients)
            {
                // Incorporate seriesId to allow for time-varying patterns
                double timeFactor = Math.Sin(seriesId * 0.01 * coef.Power + coef.Power);
                result += coef.Weight * coef.Value * Math.Pow(number, coef.Power) * (1 + timeFactor * 0.1);
            }
            return result;
        }

        // Generates a combination by scoring all numbers and picking the best
        public List<int> GenerateCombination(int seriesId)
        {
            return Enumerable.Range(1, 25)
                .Select(n => new { Number = n, Score = Evaluate(n, seriesId) })
                .OrderByDescending(x => x.Score)
                .Take(14)
                .Select(x => x.Number)
                .OrderBy(n => n)
                .ToList();
        }
    }

    public class EvolutionaryGenerativeModel
    {
        private List<EvolutionaryFunction> ensemble = new();
        private readonly Random random = new(42);

        // --- Genetic Algorithm Parameters ---
        private const int PopulationSize = 100;
        private const int Generations = 50;
        private const double MutationRate = 0.1;
        private const double ElitismRate = 0.1; // Keep the top 10% of the population

        public void LearnFromSeries(int seriesId, List<List<int>> combinations)
        {
            Console.WriteLine($"🧬 Evolving generative functions for series {seriesId}...");
            
            // 1. Initialize Population
            var population = InitializePopulation(5); // Max order of 5

            // 2. Run Evolutionary Process
            for (int gen = 0; gen < Generations; gen++)
            {
                // Calculate fitness for each individual
                foreach (var individual in population)
                {
                    individual.Fitness = CalculateFitness(individual, seriesId, combinations);
                }

                // Sort population by fitness
                population = population.OrderByDescending(p => p.Fitness).ToList();

                // Create the next generation
                var nextGeneration = new List<EvolutionaryFunction>();

                // Elitism: carry over the best individuals
                int eliteCount = (int)(PopulationSize * ElitismRate);
                nextGeneration.AddRange(population.Take(eliteCount));

                // Crossover and Mutation
                while (nextGeneration.Count < PopulationSize)
                {
                    var parent1 = SelectParent(population);
                    var parent2 = SelectParent(population);
                    var child = Crossover(parent1, parent2);
                    Mutate(child);
                    nextGeneration.Add(child);
                }
                population = nextGeneration;
                
                if (gen % 10 == 0)
                {
                    Console.WriteLine($"   Generation {gen}: Best Fitness = {population[0].Fitness:P2}");
                }
            }

            // 3. Update the ensemble with the best functions found
            ensemble = population.OrderByDescending(p => p.Fitness).Take(10).ToList(); // Keep top 10 as our ensemble
            Console.WriteLine($"✅ Evolution complete. Best function fitness: {ensemble[0].Fitness:P2}. Ensemble size: {ensemble.Count}");
        }

        private List<EvolutionaryFunction> InitializePopulation(int maxOrder)
        {
            var population = new List<EvolutionaryFunction>();
            for (int i = 0; i < PopulationSize; i++)
            {
                var function = new EvolutionaryFunction { Bias = random.NextDouble() * 10 - 5 };
                int order = random.Next(1, maxOrder + 1);
                for (int p = 0; p <= order; p++)
                {
                    function.Coefficients.Add(new EvolutionaryCoefficient
                    {
                        Value = random.NextDouble() * 10 - 5,
                        Power = p,
                        Weight = random.NextDouble() * 2 - 1
                    });
                }
                population.Add(function);
            }
            return population;
        }

        private double CalculateFitness(EvolutionaryFunction function, int seriesId, List<List<int>> actualCombinations)
        {
            var generated = function.GenerateCombination(seriesId);
            double maxMatches = actualCombinations.Max(actual => (double)generated.Intersect(actual).Count());
            return maxMatches / 14.0;
        }

        private EvolutionaryFunction SelectParent(List<EvolutionaryFunction> population)
        {
            // Tournament selection
            int tournamentSize = 5;
            var tournament = population.OrderBy(x => random.Next()).Take(tournamentSize).ToList();
            return tournament.OrderByDescending(p => p.Fitness).First();
        }

        private EvolutionaryFunction Crossover(EvolutionaryFunction parent1, EvolutionaryFunction parent2)
        {
            var child = new EvolutionaryFunction { Bias = (parent1.Bias + parent2.Bias) / 2.0 };
            var allPowers = parent1.Coefficients.Select(c => c.Power)
                .Union(parent2.Coefficients.Select(c => c.Power)).Distinct();

            foreach (var power in allPowers)
            {
                var coef1 = parent1.Coefficients.FirstOrDefault(c => c.Power == power);
                var coef2 = parent2.Coefficients.FirstOrDefault(c => c.Power == power);
                
                if (coef1 != null && coef2 != null)
                {
                    child.Coefficients.Add(new EvolutionaryCoefficient
                    {
                        Power = power,
                        Value = (coef1.Value + coef2.Value) / 2.0,
                        Weight = (coef1.Weight + coef2.Weight) / 2.0
                    });
                }
                else
                {
                    child.Coefficients.Add(coef1 ?? coef2);
                }
            }
            return child;
        }

        private void Mutate(EvolutionaryFunction function)
        {
            if (random.NextDouble() < MutationRate)
            {
                function.Bias += (random.NextDouble() - 0.5) * 0.5;
            }
            foreach (var coef in function.Coefficients)
            {
                if (random.NextDouble() < MutationRate)
                {
                    coef.Value += (random.NextDouble() - 0.5) * 0.5;
                }
                if (random.NextDouble() < MutationRate)
                {
                    coef.Weight += (random.NextDouble() - 0.5) * 0.2;
                }
            }
        }

        public List<int> GenerateForSeries(int seriesId)
        {
            if (!ensemble.Any())
            {
                throw new InvalidOperationException("Model has not been trained. Call LearnFromSeries first.");
            }

            Console.WriteLine($"🗳️ Generating prediction for series {seriesId} using an ensemble of {ensemble.Count} functions...");

            // Ensemble Voting: Get predictions from all functions and count number occurrences
            var numberVotes = new Dictionary<int, int>();
            foreach (var function in ensemble)
            {
                var combination = function.GenerateCombination(seriesId);
                foreach (var number in combination)
                {
                    if (!numberVotes.ContainsKey(number)) numberVotes[number] = 0;
                    numberVotes[number]++;
                }
            }

            // Select the 14 numbers that received the most votes
            return numberVotes.OrderByDescending(kvp => kvp.Value)
                .ThenBy(kvp => kvp.Key) // Stable sort
                .Take(14)
                .Select(kvp => kvp.Key)
                .OrderBy(n => n)
                .ToList();
        }
    }
}
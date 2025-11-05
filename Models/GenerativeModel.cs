using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor.Models
{
    // Representa un coeficiente en una función generativa
    public class GenerativeCoefficient
    {
        public double Value { get; set; }
        public int Power { get; set; }
        public string Variable { get; set; } = "n"; // n = posición/índice
        public double Weight { get; set; } = 1.0;
    }

    // Función generativa de orden N
    public class GenerativeFunction
    {
        public List<GenerativeCoefficient> Coefficients { get; set; } = new();
        public int Order { get; set; }
        public double Bias { get; set; } = 0.0;
        public double Accuracy { get; set; } = 0.0;
        
        // Evalúa la función para un valor dado
        public double Evaluate(double n)
        {
            double result = Bias;
            foreach (var coef in Coefficients)
            {
                result += coef.Weight * coef.Value * Math.Pow(n, coef.Power);
            }
            return result;
        }
        
        // Genera una combinación usando la función
        public List<int> GenerateCombination(int seriesId)
        {
            var numbers = new List<int>();
            var used = new HashSet<int>();
            
            // Usar el seriesId como semilla inicial
            for (int pos = 1; pos <= 14; pos++)
            {
                // Aplicar la función generativa
                double rawValue = Evaluate(pos * seriesId + pos);
                
                // Transformar a número válido (1-25)
                int number = TransformToValidNumber(rawValue, used);
                
                if (number > 0 && !used.Contains(number))
                {
                    numbers.Add(number);
                    used.Add(number);
                }
            }
            
            // Completar hasta 14 números si falta
            while (numbers.Count < 14)
            {
                for (int n = 1; n <= 25 && numbers.Count < 14; n++)
                {
                    if (!used.Contains(n))
                    {
                        numbers.Add(n);
                        used.Add(n);
                    }
                }
            }
            
            return numbers.OrderBy(x => x).Take(14).ToList();
        }
        
        private int TransformToValidNumber(double value, HashSet<int> used)
        {
            // Aplicar funciones modulares para mapear a rango 1-25
            int candidate = ((int)Math.Abs(value) % 25) + 1;
            
            // Si está usado, aplicar transformaciones
            int attempts = 0;
            while (used.Contains(candidate) && attempts < 25)
            {
                candidate = (candidate % 25) + 1;
                attempts++;
            }
            
            return candidate;
        }
    }

    public class GenerativeModel
    {
        private List<GenerativeFunction> functions = new();
        private readonly Dictionary<int, List<List<int>>> actualResults = new();
        private readonly Random random = new(42);

        public void LearnFromSeries(int seriesId, List<List<int>> combinations)
        {
            // Almacenar resultados reales
            actualResults[seriesId] = combinations;
            
            // Intentar encontrar funciones que reproduzcan estos resultados
            var bestFunction = FindBestFunction(seriesId, combinations);
            
            if (bestFunction != null && bestFunction.Accuracy > 0.3) // Threshold mínimo
            {
                functions.Add(bestFunction);
                Console.WriteLine($"📊 Found generative function for series {seriesId} with {bestFunction.Accuracy:P2} accuracy");
                Console.WriteLine($"   Order: {bestFunction.Order}, Coefficients: {bestFunction.Coefficients.Count}");
            }
        }

        private GenerativeFunction FindBestFunction(int seriesId, List<List<int>> actualCombinations)
        {
            GenerativeFunction bestFunction = null;
            double bestAccuracy = 0.0;

            // Probar diferentes órdenes de función (1 a 5)
            for (int order = 1; order <= 5; order++)
            {
                var function = CreateFunctionForOrder(order, seriesId, actualCombinations);
                
                if (function.Accuracy > bestAccuracy)
                {
                    bestAccuracy = function.Accuracy;
                    bestFunction = function;
                }
            }

            return bestFunction;
        }

        private GenerativeFunction CreateFunctionForOrder(int order, int seriesId, List<List<int>> actualCombinations)
        {
            var function = new GenerativeFunction { Order = order };
            
            // Crear coeficientes para cada potencia hasta el orden
            for (int power = 0; power <= order; power++)
            {
                function.Coefficients.Add(new GenerativeCoefficient
                {
                    Value = random.NextDouble() * 10 - 5, // Valor entre -5 y 5
                    Power = power,
                    Weight = random.NextDouble() * 2
                });
            }
            
            // Bias inicial
            function.Bias = random.NextDouble() * 25;
            
            // Optimizar coeficientes usando gradiente descendente simple
            OptimizeFunction(function, seriesId, actualCombinations);
            
            // Calcular precisión final
            function.Accuracy = CalculateAccuracy(function, seriesId, actualCombinations);
            
            return function;
        }

        private void OptimizeFunction(GenerativeFunction function, int seriesId, List<List<int>> actualCombinations)
        {
            double learningRate = 0.01;
            int epochs = 100;
            
            for (int epoch = 0; epoch < epochs; epoch++)
            {
                // Generar combinación con función actual
                var generated = function.GenerateCombination(seriesId);
                
                // Encontrar la mejor coincidencia en los resultados reales
                var bestMatch = actualCombinations
                    .OrderByDescending(actual => generated.Intersect(actual).Count())
                    .First();
                
                // Calcular error y ajustar coeficientes
                double error = CalculateError(generated, bestMatch);
                
                // Ajuste simple de coeficientes
                foreach (var coef in function.Coefficients)
                {
                    coef.Value += (random.NextDouble() - 0.5) * learningRate * error;
                    coef.Weight += (random.NextDouble() - 0.5) * learningRate * error * 0.1;
                }
                
                function.Bias += (random.NextDouble() - 0.5) * learningRate * error * 0.1;
            }
        }

        private double CalculateError(List<int> generated, List<int> actual)
        {
            double matches = generated.Intersect(actual).Count();
            return (14.0 - matches) / 14.0; // Error normalizado
        }

        private double CalculateAccuracy(GenerativeFunction function, int seriesId, List<List<int>> actualCombinations)
        {
            var generated = function.GenerateCombination(seriesId);
            
            double maxMatches = 0;
            foreach (var actual in actualCombinations)
            {
                double matches = generated.Intersect(actual).Count();
                maxMatches = Math.Max(maxMatches, matches);
            }
            
            return maxMatches / 14.0;
        }

        public List<int> GenerateForSeries(int seriesId)
        {
            if (!functions.Any())
            {
                Console.WriteLine("⚠️  No generative functions available. Using fallback.");
                return GenerateFallback(seriesId);
            }

            // Usar la función con mejor precisión
            var bestFunction = functions.OrderByDescending(f => f.Accuracy).First();
            
            Console.WriteLine($"🔧 Using generative function (Order {bestFunction.Order}, Accuracy: {bestFunction.Accuracy:P2})");
            
            return bestFunction.GenerateCombination(seriesId);
        }

        public List<List<int>> GenerateMultipleForSeries(int seriesId, int count = 7)
        {
            var results = new List<List<int>>();
            
            // Generar usando diferentes funciones si están disponibles
            var availableFunctions = functions.OrderByDescending(f => f.Accuracy).Take(count).ToList();
            
            foreach (var function in availableFunctions)
            {
                results.Add(function.GenerateCombination(seriesId));
            }
            
            // Completar con variaciones si no hay suficientes funciones
            while (results.Count < count)
            {
                results.Add(GenerateVariation(seriesId, results.Count));
            }
            
            return results.Take(count).ToList();
        }

        private List<int> GenerateVariation(int seriesId, int variation)
        {
            if (functions.Any())
            {
                var baseFunction = functions.OrderByDescending(f => f.Accuracy).First();
                
                // Crear variación modificando coeficientes ligeramente
                var variedFunction = new GenerativeFunction
                {
                    Order = baseFunction.Order,
                    Bias = baseFunction.Bias + (random.NextDouble() - 0.5) * 2,
                    Coefficients = baseFunction.Coefficients.Select(c => new GenerativeCoefficient
                    {
                        Value = c.Value + (random.NextDouble() - 0.5) * 0.5,
                        Power = c.Power,
                        Weight = c.Weight + (random.NextDouble() - 0.5) * 0.1,
                        Variable = c.Variable
                    }).ToList()
                };
                
                return variedFunction.GenerateCombination(seriesId + variation);
            }
            
            return GenerateFallback(seriesId + variation);
        }

        private List<int> GenerateFallback(int seriesId)
        {
            // Función generativa simple como fallback
            var numbers = new List<int>();
            var used = new HashSet<int>();
            
            for (int i = 1; i <= 14; i++)
            {
                // Función polinómica simple: f(n) = a*n^2 + b*n + c
                double a = 0.1 + (seriesId % 10) * 0.01;
                double b = 1.2 + (seriesId % 7) * 0.1;
                double c = seriesId % 25;
                
                double value = a * i * i + b * i + c;
                int number = ((int)Math.Abs(value) % 25) + 1;
                
                while (used.Contains(number))
                {
                    number = (number % 25) + 1;
                }
                
                numbers.Add(number);
                used.Add(number);
            }
            
            return numbers.OrderBy(x => x).ToList();
        }

        public void PrintFunctionDetails()
        {
            Console.WriteLine($"\n📊 Generative Functions Discovered: {functions.Count}");
            
            foreach (var func in functions.OrderByDescending(f => f.Accuracy))
            {
                Console.WriteLine($"   Order {func.Order}: Accuracy {func.Accuracy:P2}, Coefficients: {func.Coefficients.Count}");
                Console.WriteLine($"   Bias: {func.Bias:F3}");
                
                for (int i = 0; i < func.Coefficients.Count; i++)
                {
                    var coef = func.Coefficients[i];
                    Console.WriteLine($"     C{i}: {coef.Value:F3} * n^{coef.Power} (weight: {coef.Weight:F3})");
                }
                Console.WriteLine();
            }
        }

        public int GetFunctionCount() => functions.Count;
        public double GetBestAccuracy() => functions.Any() ? functions.Max(f => f.Accuracy) : 0.0;
    }
}
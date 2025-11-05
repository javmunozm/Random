using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using DataProcessor.Models;
using DataProcessor.Connections;

namespace DataProcessor.Methods
{
    public class GenerativeEngine
    {
        private readonly DatabaseConnection dbConnection;
        private readonly GenerativeModel model;

        public GenerativeEngine()
        {
            dbConnection = new DatabaseConnection();
            model = new GenerativeModel();
            
            // Cargar y aprender de todos los datos existentes
            LearnFromExistingData();
        }

        private void LearnFromExistingData()
        {
            Console.WriteLine("🔬 Learning generative functions from existing data...");
            
            // Cargar todas las series históricas
            var allSeries = dbConnection.LoadHistoricalDataBefore(3113); // Todas hasta 3112
            
            Console.WriteLine($"📚 Learning from {allSeries.Count} historical series");
            
            // Agrupar por seriesId y aprender funciones específicas
            var seriesGroups = allSeries.GroupBy(s => s.SeriesId);
            
            foreach (var group in seriesGroups.OrderBy(g => g.Key))
            {
                var seriesId = group.Key;
                var combinations = group.SelectMany(s => s.AllCombinations).ToList();
                
                if (combinations.Count >= 7) // Suficientes datos para aprender
                {
                    model.LearnFromSeries(seriesId, combinations);
                }
            }
            
            Console.WriteLine($"✅ Generative learning complete. Functions discovered: {model.GetFunctionCount()}");
            Console.WriteLine($"   Best accuracy achieved: {model.GetBestAccuracy():P2}");
            
            // Mostrar detalles de las funciones
            model.PrintFunctionDetails();
        }

        public void LearnFromNewSeries(int seriesId, List<List<int>> combinations)
        {
            Console.WriteLine($"🔄 Learning generative function from new series {seriesId}...");
            
            model.LearnFromSeries(seriesId, combinations);
            
            Console.WriteLine($"📈 Updated model. Total functions: {model.GetFunctionCount()}");
            Console.WriteLine($"   Current best accuracy: {model.GetBestAccuracy():P2}");
        }

        public List<int> PredictSeries(int targetSeriesId)
        {
            Console.WriteLine($"\n🎯 Generating series {targetSeriesId} using generative functions");
            
            var prediction = model.GenerateForSeries(targetSeriesId);
            
            Console.WriteLine($"Generated: {string.Join(" ", prediction.Select(n => n.ToString("D2")))}");
            
            // Guardar predicción individual
            SaveGenerativePrediction(targetSeriesId, prediction);
            
            return prediction;
        }

        public List<List<int>> PredictMultipleSeries(int targetSeriesId, int count = 7)
        {
            Console.WriteLine($"\n🎯 Generating {count} combinations for series {targetSeriesId}");
            
            var predictions = model.GenerateMultipleForSeries(targetSeriesId, count);
            
            Console.WriteLine($"Generated {predictions.Count} combinations:");
            for (int i = 0; i < predictions.Count; i++)
            {
                Console.WriteLine($"{i + 1}. {string.Join(" ", predictions[i].Select(n => n.ToString("D2")))}");
            }
            
            // Guardar predicciones múltiples
            SaveMultipleGenerativePredictions(targetSeriesId, predictions);
            
            return predictions;
        }

        public void ValidateAndLearn(int seriesId, List<int> prediction, List<List<int>> actualResults)
        {
            Console.WriteLine($"🔍 Validating prediction for series {seriesId}");
            
            var bestMatch = actualResults
                .OrderByDescending(actual => prediction.Intersect(actual).Count())
                .First();
            
            var matches = prediction.Intersect(bestMatch).Count();
            var accuracy = (double)matches / 14.0;
            
            Console.WriteLine($"   Matches: {matches}/14 ({accuracy:P2})");
            Console.WriteLine($"   Best match: {string.Join(" ", bestMatch.Select(n => n.ToString("D2")))}");
            
            // Aprender de los resultados reales para mejorar las funciones
            model.LearnFromSeries(seriesId, actualResults);
        }

        private void SaveGenerativePrediction(int seriesId, List<int> prediction)
        {
            try
            {
                System.IO.Directory.CreateDirectory("Results");
                var fileName = $"Results/generated_func_{seriesId}.json";
                
                var predictionData = new
                {
                    series_id = seriesId,
                    generation_timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                    model_type = "GenerativeFunctionModel",
                    functions_count = model.GetFunctionCount(),
                    best_accuracy = model.GetBestAccuracy(),
                    predicted_combination = prediction,
                    formatted_prediction = string.Join(" ", prediction.Select(n => n.ToString("D2"))),
                    methodology = new
                    {
                        approach = "Mathematical generative functions of order N",
                        description = "Uses polynomial equations to generate exact number sequences",
                        learning_type = "Function coefficient optimization with gradient descent",
                        deterministic = "Functions are derived from historical data patterns"
                    },
                    function_details = new
                    {
                        total_functions = model.GetFunctionCount(),
                        max_accuracy = model.GetBestAccuracy(),
                        learning_source = "Historical series data with coefficient optimization"
                    }
                };

                var jsonOptions = new JsonSerializerOptions { WriteIndented = true };
                var json = JsonSerializer.Serialize(predictionData, jsonOptions);
                System.IO.File.WriteAllText(fileName, json);
                
                Console.WriteLine($"💾 Generative prediction saved to: {fileName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error saving prediction: {ex.Message}");
            }
        }

        private void SaveMultipleGenerativePredictions(int seriesId, List<List<int>> predictions)
        {
            try
            {
                System.IO.Directory.CreateDirectory("Results");
                var fileName = $"Results/generated_func_multi_{seriesId}.json";
                
                var predictionData = new
                {
                    series_id = seriesId,
                    generation_timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                    model_type = "GenerativeFunctionModel_Multiple",
                    functions_count = model.GetFunctionCount(),
                    best_accuracy = model.GetBestAccuracy(),
                    total_predictions = predictions.Count,
                    predicted_combinations = predictions.Select((p, index) => new
                    {
                        rank = index + 1,
                        combination = p,
                        formatted = string.Join(" ", p.Select(n => n.ToString("D2"))),
                        sum = p.Sum(),
                        variance = CalculateVariance(p),
                        consecutive_count = CountConsecutive(p)
                    }).ToArray(),
                    generative_approach = new
                    {
                        method = "Mathematical function generation",
                        function_types = "Polynomial equations of varying orders (1-5)",
                        optimization = "Gradient descent on historical data",
                        refinement = "Coefficient adjustment per new data insert"
                    },
                    learning_summary = new
                    {
                        discovered_functions = model.GetFunctionCount(),
                        peak_accuracy = model.GetBestAccuracy(),
                        data_driven = "Each function optimized for specific historical patterns"
                    }
                };

                var jsonOptions = new JsonSerializerOptions { WriteIndented = true };
                var json = JsonSerializer.Serialize(predictionData, jsonOptions);
                System.IO.File.WriteAllText(fileName, json);
                
                Console.WriteLine($"💾 Multiple generative predictions saved to: {fileName}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error saving predictions: {ex.Message}");
            }
        }

        private double CalculateVariance(List<int> numbers)
        {
            double mean = numbers.Average();
            return numbers.Select(n => Math.Pow(n - mean, 2)).Average();
        }

        private int CountConsecutive(List<int> numbers)
        {
            int consecutive = 0;
            var sorted = numbers.OrderBy(x => x).ToList();
            
            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i] == sorted[i - 1] + 1)
                    consecutive++;
            }
            
            return consecutive;
        }

        public void TestReproduction()
        {
            Console.WriteLine("\n🧪 Testing function reproduction capability...");
            
            // Probar con las últimas 3 series conocidas
            var testSeries = new[] { 3110, 3111, 3112 };
            
            foreach (var seriesId in testSeries)
            {
                Console.WriteLine($"\n--- Testing Series {seriesId} ---");
                
                var actualResults = dbConnection.GetActualResultsForSeries(seriesId);
                if (actualResults.Any())
                {
                    var generated = model.GenerateForSeries(seriesId);
                    
                    var bestMatch = actualResults
                        .OrderByDescending(actual => generated.Intersect(actual).Count())
                        .First();
                    
                    var matches = generated.Intersect(bestMatch).Count();
                    var accuracy = (double)matches / 14.0;
                    
                    Console.WriteLine($"Generated:  {string.Join(" ", generated.Select(n => n.ToString("D2")))}");
                    Console.WriteLine($"Best match: {string.Join(" ", bestMatch.Select(n => n.ToString("D2")))}");
                    Console.WriteLine($"Accuracy: {matches}/14 ({accuracy:P2})");
                }
                else
                {
                    Console.WriteLine($"No actual data found for series {seriesId}");
                }
            }
        }

        public void InsertAndLearn(int seriesId, List<List<int>> actualResults)
        {
            Console.WriteLine($"\n📥 Inserting and learning from series {seriesId}");
            
            // Insertar en base de datos usando CRUD
            if (!dbConnection.SeriesExists(seriesId))
            {
                if (dbConnection.InsertSeriesData(seriesId, actualResults))
                {
                    Console.WriteLine($"✅ Series {seriesId} inserted successfully");
                }
                else
                {
                    Console.WriteLine($"❌ Failed to insert series {seriesId}");
                    return;
                }
            }
            else
            {
                Console.WriteLine($"ℹ️  Series {seriesId} already exists in database");
            }
            
            // Aprender función generativa específica de esta serie
            LearnFromNewSeries(seriesId, actualResults);
        }
    }
}
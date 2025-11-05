using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using DataProcessor.Models;
using DataProcessor.Connections;

namespace DataProcessor.Methods
{
    public class SpatialPredictionEngine
    {
        private readonly SpatialEventModel model;
        private readonly SpatialDatabaseConnection dbConnection;

        public SpatialPredictionEngine()
        {
            model = new SpatialEventModel();
            dbConnection = new SpatialDatabaseConnection();
        }

        public void PredictSpatialEvent(int eventId)
        {
            Console.WriteLine($"\n=== Spatial Event Prediction for Event {eventId} ===");
            
            // Determine event day
            var eventDay = model.GetNextEventDay(eventId);
            var eventDateTime = dbConnection.CalculateEventDateTime(eventId);
            
            Console.WriteLine($"Event Day: {eventDay}");
            Console.WriteLine($"Event Time: {eventDateTime:yyyy-MM-dd HH:mm:ss} Chilean Time");
            
            // Load historical data for training
            var historicalData = dbConnection.LoadHistoricalSpatialDataBefore(eventId);
            Console.WriteLine($"Training with {historicalData.Count} historical spatial events before {eventId}");
            
            // Train the model
            foreach (var pattern in historicalData)
            {
                model.LearnFromEvent(pattern);
            }
            
            // Generate prediction as coordinates first
            var predictedCoordinates = model.PredictNextLocations(eventId, eventDay);
            
            // Convert coordinates to numbers for output format
            var predictedNumbers = CoordinateNumberSystem.CoordinatesToNumbers(predictedCoordinates);
            
            // Display prediction in number format (01-25)
            Console.WriteLine($"\n🎯 Spatial Prediction for Event {eventId}:");
            Console.WriteLine($"Numbers: {CoordinateNumberSystem.FormatNumbers(predictedNumbers)}");
            
            // Also show coordinates for reference
            Console.WriteLine($"Coordinates: {string.Join(" ", predictedCoordinates.Select(c => c.ToString()))}");
            
            // Validate event format
            var validation = CoordinateNumberSystem.ValidateEvent(predictedNumbers);
            if (!validation.isValid)
            {
                Console.WriteLine($"⚠️ Validation errors: {string.Join(", ", validation.errors)}");
            }
            else
            {
                Console.WriteLine("✅ Event format validated");
            }
            
            // Save prediction
            SaveSpatialPrediction(eventId, eventDay, eventDateTime, predictedCoordinates, historicalData.Count);
            
            // Validate if actual results exist
            var actualCoordinates = dbConnection.GetActualCoordinatesForEvent(eventId);
            if (actualCoordinates.Any())
            {
                var accuracy = CalculateSpatialAccuracy(predictedCoordinates, actualCoordinates);
                Console.WriteLine($"\n📊 Spatial Accuracy: {accuracy:F1}% ({GetMatchCount(predictedCoordinates, actualCoordinates)}/{predictedCoordinates.Count} coordinates within tolerance)");
                
                // Learn from the actual results
                var actualPattern = new SpatialEventPattern
                {
                    EventId = eventId,
                    EventDay = eventDay,
                    EventTime = eventDateTime,
                    Coordinates = actualCoordinates
                };
                model.LearnFromEvent(actualPattern);
                Console.WriteLine("✅ Model learned from actual results");
            }
            else
            {
                Console.WriteLine("No actual results found for validation");
            }
        }

        public void RunSequentialSpatialPredictions(int startEventId, int endEventId = 0)
        {
            if (endEventId == 0) endEventId = startEventId + 50; // Default to 50 predictions
            
            Console.WriteLine($"\n=== Sequential Spatial Predictions ({startEventId} to {endEventId}) ===");
            
            var results = new List<SpatialPredictionResult>();
            
            for (int eventId = startEventId; eventId <= endEventId; eventId++)
            {
                Console.WriteLine($"\n--- Predicting Event {eventId} ---");
                
                var eventDay = model.GetNextEventDay(eventId);
                var historicalData = dbConnection.LoadHistoricalSpatialDataBefore(eventId);
                
                // Train model
                foreach (var pattern in historicalData)
                {
                    model.LearnFromEvent(pattern);
                }
                
                // Predict
                var prediction = model.PredictNextLocations(eventId, eventDay);
                
                // Validate
                var actualCoords = dbConnection.GetActualCoordinatesForEvent(eventId);
                var accuracy = actualCoords.Any() ? CalculateSpatialAccuracy(prediction, actualCoords) : 0;
                
                var result = new SpatialPredictionResult
                {
                    EventId = eventId,
                    EventDay = eventDay,
                    PredictedCoordinates = prediction,
                    ActualCoordinates = actualCoords,
                    Accuracy = accuracy,
                    TrainingDataSize = historicalData.Count
                };
                
                results.Add(result);
                
                if (actualCoords.Any())
                {
                    Console.WriteLine($"Event {eventId}: {accuracy:F1}% accuracy");
                    
                    // Learn from actual results
                    var actualPattern = new SpatialEventPattern
                    {
                        EventId = eventId,
                        EventDay = eventDay,
                        EventTime = dbConnection.CalculateEventDateTime(eventId),
                        Coordinates = actualCoords
                    };
                    model.LearnFromEvent(actualPattern);
                }
                else
                {
                    Console.WriteLine($"Event {eventId}: No actual data for validation");
                }
            }
            
            // Summary
            var validResults = results.Where(r => r.ActualCoordinates.Any()).ToList();
            if (validResults.Any())
            {
                var averageAccuracy = validResults.Average(r => r.Accuracy);
                Console.WriteLine($"\n=== SPATIAL PREDICTION SUMMARY ===");
                Console.WriteLine($"Total predictions: {results.Count}");
                Console.WriteLine($"Validated predictions: {validResults.Count}");
                Console.WriteLine($"Average accuracy: {averageAccuracy:F1}%");
                Console.WriteLine($"Best accuracy: {validResults.Max(r => r.Accuracy):F1}%");
                Console.WriteLine($"Worst accuracy: {validResults.Min(r => r.Accuracy):F1}%");
                
                // Day-specific performance
                var dayPerformance = validResults.GroupBy(r => r.EventDay)
                    .ToDictionary(g => g.Key, g => g.Average(r => r.Accuracy));
                
                Console.WriteLine("\n=== PERFORMANCE BY DAY ===");
                foreach (var day in dayPerformance)
                {
                    Console.WriteLine($"{day.Key}: {day.Value:F1}% average accuracy");
                }
            }
            
            // Save comprehensive results
            SaveSequentialResults(results);
        }

        public void AnalyzeSpatialPatterns()
        {
            Console.WriteLine("\n=== Spatial Pattern Analysis ===");
            
            var allEvents = dbConnection.LoadAllSpatialEvents();
            Console.WriteLine($"Total events in database: {allEvents.Count}");
            
            // Day distribution
            var dayDistribution = allEvents.GroupBy(e => e.EventDay)
                .ToDictionary(g => g.Key, g => g.Count());
            
            Console.WriteLine("\n=== EVENT DISTRIBUTION BY DAY ===");
            foreach (var day in dayDistribution)
            {
                Console.WriteLine($"{day.Key}: {day.Value} events ({day.Value * 100.0 / allEvents.Count:F1}%)");
            }
            
            // Coordinate bounds
            var bounds = dbConnection.GetCoordinateBounds();
            Console.WriteLine($"\n=== COORDINATE BOUNDS ===");
            Console.WriteLine($"X: {bounds.minX:F2} to {bounds.maxX:F2} (range: {bounds.maxX - bounds.minX:F2})");
            Console.WriteLine($"Y: {bounds.minY:F2} to {bounds.maxY:F2} (range: {bounds.maxY - bounds.minY:F2})");
            
            // Density analysis
            var density = dbConnection.GetDensityDistribution();
            var topDensityAreas = density.OrderByDescending(d => d.Value).Take(10);
            
            Console.WriteLine($"\n=== TOP 10 HIGH-DENSITY AREAS ===");
            foreach (var area in topDensityAreas)
            {
                Console.WriteLine($"Grid {area.Key}: {area.Value} coordinates");
            }
            
            // Train model for cluster analysis
            foreach (var eventPattern in allEvents)
            {
                model.LearnFromEvent(eventPattern);
            }
            
            // Hot zones by day
            Console.WriteLine($"\n=== HOT ZONES BY DAY ===");
            var eventDays = new[] { DayOfWeek.Wednesday, DayOfWeek.Friday, DayOfWeek.Sunday };
            foreach (var day in eventDays)
            {
                var hotZones = model.GetHotZonesForDay(day).Take(5);
                Console.WriteLine($"\n{day} Hot Zones:");
                foreach (var zone in hotZones)
                {
                    Console.WriteLine($"  Center: {zone.Center}, Weight: {zone.Weight:F2}, Points: {zone.Points.Count}");
                }
            }
        }

        public void InsertSpatialEventData(int eventId, List<Coordinate> coordinates)
        {
            Console.WriteLine($"\n=== Inserting Spatial Event {eventId} ===");
            
            if (dbConnection.SpatialEventExists(eventId))
            {
                Console.WriteLine($"❌ Event {eventId} already exists in database");
                return;
            }
            
            if (!dbConnection.ValidateSpatialEventData(eventId, coordinates))
            {
                Console.WriteLine($"❌ Invalid spatial event data for event {eventId}");
                return;
            }
            
            var eventDay = dbConnection.CalculateEventDay(eventId);
            var eventDateTime = dbConnection.CalculateEventDateTime(eventId);
            
            if (dbConnection.InsertSpatialEventData(eventId, eventDay, eventDateTime, coordinates))
            {
                Console.WriteLine($"✅ Successfully inserted spatial event {eventId}");
                
                // Update model with new data
                var pattern = new SpatialEventPattern
                {
                    EventId = eventId,
                    EventDay = eventDay,
                    EventTime = eventDateTime,
                    Coordinates = coordinates
                };
                model.LearnFromEvent(pattern);
                Console.WriteLine("✅ Model updated with new spatial event data");
            }
        }

        private double CalculateSpatialAccuracy(List<Coordinate> predicted, List<Coordinate> actual, double tolerance = 0.1)
        {
            if (!predicted.Any() || !actual.Any()) return 0;
            
            // For discrete coordinates, use exact matching (very small tolerance for floating point)
            int matches = 0;
            var usedActual = new HashSet<int>();
            
            foreach (var predictedCoord in predicted)
            {
                for (int i = 0; i < actual.Count; i++)
                {
                    if (usedActual.Contains(i)) continue;
                    
                    // Exact coordinate match for discrete system
                    if (Math.Abs(predictedCoord.X - actual[i].X) <= tolerance && 
                        Math.Abs(predictedCoord.Y - actual[i].Y) <= tolerance)
                    {
                        matches++;
                        usedActual.Add(i);
                        break;
                    }
                }
            }
            
            return (double)matches / predicted.Count * 100.0;
        }

        private int GetMatchCount(List<Coordinate> predicted, List<Coordinate> actual, double tolerance = 0.1)
        {
            if (!predicted.Any() || !actual.Any()) return 0;
            
            int matches = 0;
            var usedActual = new HashSet<int>();
            
            foreach (var predictedCoord in predicted)
            {
                for (int i = 0; i < actual.Count; i++)
                {
                    if (usedActual.Contains(i)) continue;
                    
                    // Exact coordinate match for discrete system
                    if (Math.Abs(predictedCoord.X - actual[i].X) <= tolerance && 
                        Math.Abs(predictedCoord.Y - actual[i].Y) <= tolerance)
                    {
                        matches++;
                        usedActual.Add(i);
                        break;
                    }
                }
            }
            
            return matches;
        }

        private void SaveSpatialPrediction(int eventId, DayOfWeek eventDay, DateTime eventTime, 
            List<Coordinate> coordinates, int trainingDataSize)
        {
            var prediction = new
            {
                event_id = eventId,
                generation_timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
                model_type = "SpatialEventModel",
                event_day = eventDay.ToString(),
                event_time = eventTime.ToString("yyyy-MM-dd HH:mm:ss"),
                training_data_size = trainingDataSize,
                predicted_coordinates = coordinates.Select(c => new { x = c.X, y = c.Y }).ToList(),
                formatted_coordinates = coordinates.Select(c => c.ToString()).ToList(),
                model_confidence = "Spatial-temporal learning with geographic clustering",
                methodology = new
                {
                    approach = "Multi-dimensional spatial learning with temporal patterns",
                    features_used = new[]
                    {
                        "Geographic clustering analysis",
                        "Day-of-week spatial preferences", 
                        "Distance pattern recognition",
                        "Density map learning",
                        "Boundary constraint modeling"
                    },
                    spatial_features = new
                    {
                        uses_clustering = true,
                        day_specific_patterns = true,
                        distance_weighting = true,
                        density_mapping = true
                    }
                },
                spatial_statistics = new
                {
                    coordinate_count = coordinates.Count,
                    spatial_spread = CalculateSpatialSpread(coordinates),
                    average_inter_point_distance = CalculateAverageDistance(coordinates),
                    centroid = CalculateCentroid(coordinates)
                }
            };

            var fileName = $"Results/spatial_prediction_{eventId}.json";
            Directory.CreateDirectory("Results");
            
            var json = JsonSerializer.Serialize(prediction, new JsonSerializerOptions 
            { 
                WriteIndented = true 
            });
            File.WriteAllText(fileName, json);
            
            Console.WriteLine($"✅ Spatial prediction saved to: {fileName}");
        }

        private void SaveSequentialResults(List<SpatialPredictionResult> results)
        {
            var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            var fileName = $"Results/spatial_sequential_results_{timestamp}.json";
            
            var json = JsonSerializer.Serialize(results, new JsonSerializerOptions 
            { 
                WriteIndented = true 
            });
            File.WriteAllText(fileName, json);
            
            Console.WriteLine($"✅ Sequential results saved to: {fileName}");
        }

        private double CalculateSpatialSpread(List<Coordinate> coordinates)
        {
            if (!coordinates.Any()) return 0;
            
            var minX = coordinates.Min(c => c.X);
            var maxX = coordinates.Max(c => c.X);
            var minY = coordinates.Min(c => c.Y);
            var maxY = coordinates.Max(c => c.Y);
            
            return Math.Sqrt(Math.Pow(maxX - minX, 2) + Math.Pow(maxY - minY, 2));
        }

        private double CalculateAverageDistance(List<Coordinate> coordinates)
        {
            if (coordinates.Count < 2) return 0;
            
            var totalDistance = 0.0;
            var count = 0;
            
            for (int i = 0; i < coordinates.Count; i++)
            {
                for (int j = i + 1; j < coordinates.Count; j++)
                {
                    totalDistance += coordinates[i].DistanceTo(coordinates[j]);
                    count++;
                }
            }
            
            return totalDistance / count;
        }

        private object CalculateCentroid(List<Coordinate> coordinates)
        {
            if (!coordinates.Any()) return new { x = 0.0, y = 0.0 };
            
            var avgX = coordinates.Average(c => c.X);
            var avgY = coordinates.Average(c => c.Y);
            
            return new { x = avgX, y = avgY };
        }
    }

    public class SpatialPredictionResult
    {
        public int EventId { get; set; }
        public DayOfWeek EventDay { get; set; }
        public List<Coordinate> PredictedCoordinates { get; set; } = new();
        public List<Coordinate> ActualCoordinates { get; set; } = new();
        public double Accuracy { get; set; }
        public int TrainingDataSize { get; set; }
    }
}
using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor.Models
{
    public class Coordinate
    {
        public double X { get; set; }
        public double Y { get; set; }

        public Coordinate(double x, double y)
        {
            X = x;
            Y = y;
        }

        public double DistanceTo(Coordinate other)
        {
            return Math.Sqrt(Math.Pow(X - other.X, 2) + Math.Pow(Y - other.Y, 2));
        }

        public override string ToString()
        {
            return $"({X:F2}, {Y:F2})";
        }

        public override bool Equals(object obj)
        {
            if (obj is Coordinate other)
                return Math.Abs(X - other.X) < 0.01 && Math.Abs(Y - other.Y) < 0.01;
            return false;
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Math.Round(X, 2), Math.Round(Y, 2));
        }
    }

    public class GeographicCluster
    {
        public Coordinate Center { get; set; }
        public double Radius { get; set; }
        public List<Coordinate> Points { get; set; } = new();
        public double Weight { get; set; } = 1.0;
        public DayOfWeek PreferredDay { get; set; }

        public bool ContainsPoint(Coordinate point)
        {
            return Center.DistanceTo(point) <= Radius;
        }
    }

    public class SpatialWeights
    {
        public Dictionary<string, double> RegionWeights { get; set; } = new();
        public Dictionary<double, double> DistanceWeights { get; set; } = new();
        public List<GeographicCluster> HotZones { get; set; } = new();
        public double LearningRate { get; set; } = 0.1;
    }

    public class SpatialEventPattern
    {
        public int EventId { get; set; }
        public DayOfWeek EventDay { get; set; }
        public DateTime EventTime { get; set; }
        public List<Coordinate> Coordinates { get; set; } = new();
        public Dictionary<string, double> SpatialFeatures { get; set; } = new();
    }

    public class WeeklyPattern
    {
        public Dictionary<DayOfWeek, double> DayWeights { get; set; } = new();
        public Dictionary<DayOfWeek, List<GeographicCluster>> DaySpecificClusters { get; set; } = new();
        public TimeSpan EventTime { get; set; } = new TimeSpan(22, 30, 0); // 22:30
    }

    public class SpatialDistribution
    {
        public double MinX { get; set; }
        public double MaxX { get; set; }
        public double MinY { get; set; }
        public double MaxY { get; set; }
        public Dictionary<string, double> DensityMap { get; set; } = new();
        public List<Coordinate> BoundaryPoints { get; set; } = new();

        public string GetGridKey(Coordinate coord, double gridSize = 1.0)
        {
            var gridX = Math.Floor(coord.X / gridSize) * gridSize;
            var gridY = Math.Floor(coord.Y / gridSize) * gridSize;
            return $"{gridX:F1},{gridY:F1}";
        }

        public bool IsWithinBounds(Coordinate coord)
        {
            return coord.X >= MinX && coord.X <= MaxX && coord.Y >= MinY && coord.Y <= MaxY;
        }
    }

    public class SpatialPredictionCandidate
    {
        public List<Coordinate> Coordinates { get; set; } = new();
        public double Score { get; set; }
        public Dictionary<string, double> FeatureScores { get; set; } = new();
        public DayOfWeek PredictedDay { get; set; }
    }

    public class SpatialEventModel
    {
        private readonly Dictionary<DayOfWeek, SpatialWeights> dayPatterns;
        private readonly List<GeographicCluster> globalHotZones;
        private readonly SpatialDistribution densityMap;
        private readonly WeeklyPattern weeklyPattern;
        private readonly List<SpatialEventPattern> trainingData;
        private readonly Random random = new(42);

        public SpatialEventModel()
        {
            dayPatterns = new Dictionary<DayOfWeek, SpatialWeights>();
            globalHotZones = new List<GeographicCluster>();
            densityMap = new SpatialDistribution();
            weeklyPattern = new WeeklyPattern();
            trainingData = new List<SpatialEventPattern>();
            
            InitializeSpatialWeights();
            InitializeWeeklyPatterns();
        }

        private void InitializeSpatialWeights()
        {
            var eventDays = new[] { DayOfWeek.Wednesday, DayOfWeek.Friday, DayOfWeek.Sunday };
            
            foreach (var day in eventDays)
            {
                dayPatterns[day] = new SpatialWeights
                {
                    LearningRate = 0.15 // Higher learning rate for spatial patterns
                };
                
                weeklyPattern.DayWeights[day] = 1.0;
                weeklyPattern.DaySpecificClusters[day] = new List<GeographicCluster>();
            }
        }

        private void InitializeWeeklyPatterns()
        {
            // Initialize with Chilean timezone consideration
            weeklyPattern.EventTime = new TimeSpan(22, 30, 0);
            
            // Equal initial weights for event days
            weeklyPattern.DayWeights[DayOfWeek.Wednesday] = 1.0;
            weeklyPattern.DayWeights[DayOfWeek.Friday] = 1.0;
            weeklyPattern.DayWeights[DayOfWeek.Sunday] = 1.0;
        }

        public void LearnFromEvent(SpatialEventPattern pattern)
        {
            trainingData.Add(pattern);
            UpdateSpatialBounds(pattern.Coordinates);
            UpdateDensityMap(pattern.Coordinates);
            UpdateDayPatterns(pattern);
            IdentifyGeographicClusters(pattern);
        }

        private void UpdateSpatialBounds(List<Coordinate> coordinates)
        {
            // Use discrete coordinate system bounds
            densityMap.MinX = 0;
            densityMap.MaxX = 2;
            densityMap.MinY = 0;
            densityMap.MaxY = 9; // Max possible Y (even though X=2 only goes to Y=5)
        }

        private void UpdateDensityMap(List<Coordinate> coordinates)
        {
            const double gridSize = 2.0; // 2-unit grid cells for density mapping
            
            foreach (var coord in coordinates)
            {
                var gridKey = densityMap.GetGridKey(coord, gridSize);
                if (densityMap.DensityMap.ContainsKey(gridKey))
                    densityMap.DensityMap[gridKey] += 1.0;
                else
                    densityMap.DensityMap[gridKey] = 1.0;
            }
        }

        private void UpdateDayPatterns(SpatialEventPattern pattern)
        {
            var dayWeights = dayPatterns[pattern.EventDay];
            
            // Learn spatial preferences for this day
            foreach (var coord in pattern.Coordinates)
            {
                var gridKey = densityMap.GetGridKey(coord);
                if (dayWeights.RegionWeights.ContainsKey(gridKey))
                    dayWeights.RegionWeights[gridKey] += dayWeights.LearningRate;
                else
                    dayWeights.RegionWeights[gridKey] = dayWeights.LearningRate;
            }
            
            // Learn distance patterns
            for (int i = 1; i < pattern.Coordinates.Count; i++)
            {
                var distance = pattern.Coordinates[i].DistanceTo(pattern.Coordinates[i-1]);
                var distanceKey = Math.Round(distance, 1);
                
                if (dayWeights.DistanceWeights.ContainsKey(distanceKey))
                    dayWeights.DistanceWeights[distanceKey] += dayWeights.LearningRate;
                else
                    dayWeights.DistanceWeights[distanceKey] = dayWeights.LearningRate;
            }
        }

        private void IdentifyGeographicClusters(SpatialEventPattern pattern)
        {
            const double clusterRadius = 5.0; // Cluster radius in coordinate units
            
            foreach (var coord in pattern.Coordinates)
            {
                bool addedToCluster = false;
                
                // Try to add to existing clusters
                foreach (var cluster in weeklyPattern.DaySpecificClusters[pattern.EventDay])
                {
                    if (cluster.Center.DistanceTo(coord) <= clusterRadius)
                    {
                        cluster.Points.Add(coord);
                        cluster.Weight += 0.1;
                        addedToCluster = true;
                        break;
                    }
                }
                
                // Create new cluster if needed
                if (!addedToCluster && weeklyPattern.DaySpecificClusters[pattern.EventDay].Count < 20)
                {
                    var newCluster = new GeographicCluster
                    {
                        Center = new Coordinate(coord.X, coord.Y),
                        Radius = clusterRadius,
                        Weight = 1.0,
                        PreferredDay = pattern.EventDay
                    };
                    newCluster.Points.Add(coord);
                    weeklyPattern.DaySpecificClusters[pattern.EventDay].Add(newCluster);
                }
            }
        }

        public List<Coordinate> PredictNextLocations(int eventId, DayOfWeek targetDay)
        {
            var candidates = GenerateSpatialCandidates(targetDay);
            var scoredCandidates = candidates.Select(c => new SpatialPredictionCandidate
            {
                Coordinates = c,
                Score = CalculateSpatialScore(c, targetDay),
                FeatureScores = CalculateSpatialFeatureScores(c, targetDay),
                PredictedDay = targetDay
            }).OrderByDescending(c => c.Score).ToList();

            return scoredCandidates.First().Coordinates;
        }

        private List<List<Coordinate>> GenerateSpatialCandidates(DayOfWeek targetDay)
        {
            var candidates = new List<List<Coordinate>>();
            
            // Generate candidates based on learned patterns
            for (int attempt = 0; attempt < 500; attempt++)
            {
                var candidate = GenerateWeightedSpatialCandidate(targetDay);
                if (IsValidSpatialCombination(candidate))
                {
                    candidates.Add(candidate);
                }
            }
            
            return candidates.Take(50).ToList(); // Top 50 spatial candidates
        }

        private List<Coordinate> GenerateWeightedSpatialCandidate(DayOfWeek targetDay)
        {
            var dayWeights = dayPatterns[targetDay];
            var usedCoords = new HashSet<Coordinate>();
            var selectedCoords = new List<Coordinate>();
            
            // Generate 14 coordinates using the discrete coordinate system
            // Use random selection from valid coordinates first, then apply weights
            var validNumbers = CoordinateNumberSystem.GenerateValidEvent(random);
            
            // Convert the 14 numbers back to coordinates
            foreach (var number in validNumbers)
            {
                var coord = CoordinateNumberSystem.NumberToCoordinate(number);
                selectedCoords.Add(coord);
            }
            
            return selectedCoords;
        }

        private Coordinate GenerateCoordinateNearCluster(GeographicCluster cluster)
        {
            // Get valid coordinates near the cluster center
            var nearbyCoords = DiscreteCoordinateSystem.GetNeighbors(cluster.Center, cluster.Radius)
                .Concat(new[] { cluster.Center })
                .Where(c => DiscreteCoordinateSystem.IsValidCoordinate(c))
                .ToList();
            
            return nearbyCoords.Any() 
                ? nearbyCoords[random.Next(nearbyCoords.Count)] 
                : DiscreteCoordinateSystem.GetRandomValidCoordinate(random);
        }

        private Coordinate GenerateWeightedCoordinate(SpatialWeights dayWeights)
        {
            if (!dayWeights.RegionWeights.Any())
            {
                return DiscreteCoordinateSystem.GetRandomValidCoordinate(random);
            }
            
            // Find the most weighted valid coordinate
            var weightedCoords = DiscreteCoordinateSystem.ValidCoordinates
                .Select(coord => new { 
                    Coord = coord, 
                    Weight = GetCoordinateWeight(coord, dayWeights) 
                })
                .OrderByDescending(wc => wc.Weight)
                .ToList();
            
            // Use weighted random selection among top candidates
            var topCandidates = weightedCoords.Take(Math.Max(5, weightedCoords.Count / 2)).ToList();
            var totalWeight = topCandidates.Sum(wc => wc.Weight + 0.1); // Add small base weight
            var randomValue = random.NextDouble() * totalWeight;
            var currentWeight = 0.0;
            
            foreach (var candidate in topCandidates)
            {
                currentWeight += candidate.Weight + 0.1;
                if (currentWeight >= randomValue)
                    return candidate.Coord;
            }
            
            return DiscreteCoordinateSystem.GetRandomValidCoordinate(random);
        }
        
        private double GetCoordinateWeight(Coordinate coord, SpatialWeights dayWeights)
        {
            var gridKey = densityMap.GetGridKey(coord);
            return dayWeights.RegionWeights.ContainsKey(gridKey) 
                ? dayWeights.RegionWeights[gridKey] 
                : 0.0;
        }

        private double CalculateSpatialScore(List<Coordinate> coordinates, DayOfWeek targetDay)
        {
            var score = 0.0;
            var dayWeights = dayPatterns[targetDay];
            
            // Region preference scoring
            foreach (var coord in coordinates)
            {
                var gridKey = densityMap.GetGridKey(coord);
                if (dayWeights.RegionWeights.ContainsKey(gridKey))
                    score += dayWeights.RegionWeights[gridKey];
            }
            
            // Cluster proximity scoring
            var clusters = weeklyPattern.DaySpecificClusters[targetDay];
            foreach (var coord in coordinates)
            {
                var nearestCluster = clusters.OrderBy(c => c.Center.DistanceTo(coord)).FirstOrDefault();
                if (nearestCluster != null)
                {
                    var distance = nearestCluster.Center.DistanceTo(coord);
                    score += nearestCluster.Weight * Math.Max(0, 10 - distance) / 10.0;
                }
            }
            
            // Distance distribution scoring
            for (int i = 1; i < coordinates.Count; i++)
            {
                var distance = coordinates[i].DistanceTo(coordinates[i-1]);
                var distanceKey = Math.Round(distance, 1);
                if (dayWeights.DistanceWeights.ContainsKey(distanceKey))
                    score += dayWeights.DistanceWeights[distanceKey];
            }
            
            // Spatial distribution quality
            var avgDistance = CalculateAverageInterPointDistance(coordinates);
            score += Math.Max(0, 10 - Math.Abs(avgDistance - 5.0)) / 10.0 * 5; // Prefer ~5 unit spacing
            
            return score;
        }

        private Dictionary<string, double> CalculateSpatialFeatureScores(List<Coordinate> coordinates, DayOfWeek targetDay)
        {
            var features = new Dictionary<string, double>();
            
            features["average_distance"] = CalculateAverageInterPointDistance(coordinates);
            features["spatial_spread"] = CalculateSpatialSpread(coordinates);
            features["cluster_affinity"] = CalculateClusterAffinity(coordinates, targetDay);
            features["density_score"] = CalculateDensityScore(coordinates);
            features["boundary_distance"] = CalculateBoundaryDistance(coordinates);
            
            return features;
        }

        private double CalculateAverageInterPointDistance(List<Coordinate> coordinates)
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

        private double CalculateSpatialSpread(List<Coordinate> coordinates)
        {
            if (!coordinates.Any()) return 0;
            
            var minX = coordinates.Min(c => c.X);
            var maxX = coordinates.Max(c => c.X);
            var minY = coordinates.Min(c => c.Y);
            var maxY = coordinates.Max(c => c.Y);
            
            return Math.Sqrt(Math.Pow(maxX - minX, 2) + Math.Pow(maxY - minY, 2));
        }

        private double CalculateClusterAffinity(List<Coordinate> coordinates, DayOfWeek targetDay)
        {
            var clusters = weeklyPattern.DaySpecificClusters[targetDay];
            if (!clusters.Any()) return 0;
            
            var totalAffinity = 0.0;
            foreach (var coord in coordinates)
            {
                var nearestCluster = clusters.OrderBy(c => c.Center.DistanceTo(coord)).First();
                var distance = nearestCluster.Center.DistanceTo(coord);
                totalAffinity += nearestCluster.Weight * Math.Max(0, 10 - distance) / 10.0;
            }
            
            return totalAffinity / coordinates.Count;
        }

        private double CalculateDensityScore(List<Coordinate> coordinates)
        {
            var totalScore = 0.0;
            foreach (var coord in coordinates)
            {
                var gridKey = densityMap.GetGridKey(coord);
                if (densityMap.DensityMap.ContainsKey(gridKey))
                    totalScore += densityMap.DensityMap[gridKey];
            }
            
            return totalScore / coordinates.Count;
        }

        private double CalculateBoundaryDistance(List<Coordinate> coordinates)
        {
            var totalDistance = 0.0;
            foreach (var coord in coordinates)
            {
                var distanceToEdge = Math.Min(
                    Math.Min(coord.X - densityMap.MinX, densityMap.MaxX - coord.X),
                    Math.Min(coord.Y - densityMap.MinY, densityMap.MaxY - coord.Y)
                );
                totalDistance += Math.Max(0, distanceToEdge);
            }
            
            return totalDistance / coordinates.Count;
        }

        private bool IsValidSpatialCombination(List<Coordinate> coordinates)
        {
            if (coordinates.Count != 14) return false;
            
            // Convert to numbers and validate using the coordinate-number system
            var numbers = CoordinateNumberSystem.CoordinatesToNumbers(coordinates);
            var validation = CoordinateNumberSystem.ValidateEvent(numbers);
            return validation.isValid;
        }

        public DayOfWeek GetNextEventDay(int currentEventId)
        {
            // Event 3121 was Wednesday, so calculate next event day
            var eventDays = new[] { DayOfWeek.Wednesday, DayOfWeek.Friday, DayOfWeek.Sunday };
            var dayIndex = (currentEventId - 3121) % 3;
            return eventDays[Math.Abs(dayIndex) % 3];
        }

        public double GetTrainingDataSize()
        {
            return trainingData.Count;
        }

        public Dictionary<DayOfWeek, int> GetDayPatternCounts()
        {
            return trainingData.GroupBy(t => t.EventDay)
                              .ToDictionary(g => g.Key, g => g.Count());
        }

        public List<GeographicCluster> GetHotZonesForDay(DayOfWeek day)
        {
            return weeklyPattern.DaySpecificClusters.ContainsKey(day) 
                ? weeklyPattern.DaySpecificClusters[day].OrderByDescending(c => c.Weight).ToList()
                : new List<GeographicCluster>();
        }
    }
}
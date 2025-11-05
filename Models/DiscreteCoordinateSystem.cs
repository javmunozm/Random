using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor.Models
{
    public static class DiscreteCoordinateSystem
    {
        // Valid coordinate space: 25 total positions (CORRECTED)
        // Column 0: (0,1) to (0,9) = 9 coordinates (NO (0,0)!)
        // Column 1: (1,0) to (1,9) = 10 coordinates
        // Column 2: (2,0) to (2,5) = 6 coordinates
        
        public static readonly List<Coordinate> ValidCoordinates = GenerateValidCoordinates();
        
        private static List<Coordinate> GenerateValidCoordinates()
        {
            var coordinates = new List<Coordinate>();
            
            // Column 0: (0,1) to (0,9) - NOTE: (0,0) is NOT valid!
            for (int y = 1; y <= 9; y++)
            {
                coordinates.Add(new Coordinate(0, y));
            }
            
            // Column 1: (1,0) to (1,9)  
            for (int y = 0; y <= 9; y++)
            {
                coordinates.Add(new Coordinate(1, y));
            }
            
            // Column 2: (2,0) to (2,5)
            for (int y = 0; y <= 5; y++)
            {
                coordinates.Add(new Coordinate(2, y));
            }
            
            return coordinates;
        }
        
        public static bool IsValidCoordinate(Coordinate coord)
        {
            return ValidCoordinates.Any(vc => 
                Math.Abs(vc.X - coord.X) < 0.01 && 
                Math.Abs(vc.Y - coord.Y) < 0.01);
        }
        
        public static bool IsValidCoordinate(double x, double y)
        {
            return IsValidCoordinate(new Coordinate(x, y));
        }
        
        public static List<Coordinate> GetValidCoordinatesForX(int x)
        {
            return x switch
            {
                0 => ValidCoordinates.Where(c => c.X == 0).ToList(),
                1 => ValidCoordinates.Where(c => c.X == 1).ToList(), 
                2 => ValidCoordinates.Where(c => c.X == 2).ToList(),
                _ => new List<Coordinate>()
            };
        }
        
        public static int GetMaxYForX(int x)
        {
            return x switch
            {
                0 => 9,
                1 => 9,
                2 => 5,
                _ => -1
            };
        }
        
        public static int GetMinYForX(int x)
        {
            return x switch
            {
                0 => 1, // X=0 starts from Y=1, not Y=0!
                1 => 0,
                2 => 0,
                _ => -1
            };
        }
        
        public static Coordinate GetRandomValidCoordinate(Random random, HashSet<Coordinate> excludeSet = null)
        {
            var availableCoords = excludeSet == null 
                ? ValidCoordinates
                : ValidCoordinates.Where(c => !excludeSet.Contains(c)).ToList();
                
            if (!availableCoords.Any())
                throw new InvalidOperationException("No available coordinates remaining");
                
            return availableCoords[random.Next(availableCoords.Count())];
        }
        
        public static List<Coordinate> GenerateValidEventCoordinates(Random random)
        {
            if (ValidCoordinates.Count < 7)
                throw new InvalidOperationException("Not enough valid coordinates for an event");
                
            var selectedCoords = new List<Coordinate>();
            var usedCoords = new HashSet<Coordinate>();
            
            while (selectedCoords.Count < 7)
            {
                var coord = GetRandomValidCoordinate(random, usedCoords);
                selectedCoords.Add(coord);
                usedCoords.Add(coord);
            }
            
            return selectedCoords.OrderBy(c => c.X).ThenBy(c => c.Y).ToList();
        }
        
        public static string FormatCoordinateGrid()
        {
            var grid = new string[6, 10]; // 6 rows (Y 0-5), 10 columns (considering max Y=9 for display)
            
            // Initialize grid
            for (int row = 0; row < 6; row++)
            {
                for (int col = 0; col < 10; col++)
                {
                    grid[row, col] = "  ";
                }
            }
            
            // Mark valid coordinates
            foreach (var coord in ValidCoordinates)
            {
                if (coord.Y < 6) // Only show first 6 Y positions for compact display
                {
                    grid[(int)coord.Y, (int)coord.X] = $"({(int)coord.X},{(int)coord.Y})".PadRight(6);
                }
            }
            
            var result = "DISCRETE COORDINATE SYSTEM:\n";
            result += "X: 0    1    2\n";
            result += "================\n";
            
            for (int y = 0; y < 6; y++)
            {
                result += $"Y{y}: ";
                for (int x = 0; x < 3; x++)
                {
                    if (IsValidCoordinate(x, y))
                        result += $"({x},{y}) ";
                    else
                        result += "---- ";
                }
                result += "\n";
            }
            
            // Add note for extended Y range and missing coordinates
            result += "\nNOTE: (0,0) is NOT VALID!\n";
            result += "      X=0 starts from Y=1 to Y=9\n";
            result += "      X=1,2 start from Y=0\n";
            result += $"TOTAL VALID: {ValidCoordinates.Count} coordinates\n";
            
            return result;
        }
        
        public static Dictionary<string, int> GetCoordinateDistribution(List<List<Coordinate>> events)
        {
            var distribution = new Dictionary<string, int>();
            
            // Initialize all valid coordinates with zero count
            foreach (var coord in ValidCoordinates)
            {
                distribution[coord.ToString()] = 0;
            }
            
            // Count occurrences
            foreach (var eventCoords in events)
            {
                foreach (var coord in eventCoords)
                {
                    var key = coord.ToString();
                    if (distribution.ContainsKey(key))
                        distribution[key]++;
                }
            }
            
            return distribution;
        }
        
        public static Dictionary<int, int> GetColumnDistribution(List<List<Coordinate>> events)
        {
            var columnCounts = new Dictionary<int, int> { {0, 0}, {1, 0}, {2, 0} };
            
            foreach (var eventCoords in events)
            {
                foreach (var coord in eventCoords)
                {
                    var x = (int)coord.X;
                    if (columnCounts.ContainsKey(x))
                        columnCounts[x]++;
                }
            }
            
            return columnCounts;
        }
        
        public static double CalculateColumnBalance(List<Coordinate> coordinates)
        {
            var columnCounts = new Dictionary<int, int> { {0, 0}, {1, 0}, {2, 0} };
            
            foreach (var coord in coordinates)
            {
                var x = (int)coord.X;
                if (columnCounts.ContainsKey(x))
                    columnCounts[x]++;
            }
            
            // Calculate balance score (0-1, where 1 is perfectly balanced)
            var totalCoords = coordinates.Count;
            var idealPerColumn = totalCoords / 3.0;
            var variance = columnCounts.Values.Sum(count => Math.Pow(count - idealPerColumn, 2)) / 3.0;
            
            // Convert variance to balance score (lower variance = higher balance)
            var maxVariance = Math.Pow(totalCoords, 2) / 3.0; // Worst case: all coords in one column
            return Math.Max(0, 1 - (variance / maxVariance));
        }
        
        public static int CountValidCoordinatesInRange(int minX, int maxX, int minY, int maxY)
        {
            return ValidCoordinates.Count(c => 
                c.X >= minX && c.X <= maxX && 
                c.Y >= minY && c.Y <= maxY);
        }
        
        public static List<Coordinate> GetNeighbors(Coordinate coord, double maxDistance = 1.5)
        {
            return ValidCoordinates
                .Where(c => !c.Equals(coord) && c.DistanceTo(coord) <= maxDistance)
                .OrderBy(c => c.DistanceTo(coord))
                .ToList();
        }
        
        // Validate an event's coordinates against the discrete system
        public static (bool isValid, List<string> errors) ValidateEventCoordinates(List<Coordinate> coordinates)
        {
            var errors = new List<string>();
            
            if (coordinates.Count != 7)
            {
                errors.Add($"Event must have exactly 7 coordinates, found {coordinates.Count}");
            }
            
            var invalidCoords = coordinates.Where(c => !IsValidCoordinate(c)).ToList();
            if (invalidCoords.Any())
            {
                errors.Add($"Invalid coordinates found: {string.Join(", ", invalidCoords.Select(c => c.ToString()))}");
            }
            
            var duplicates = coordinates.GroupBy(c => c.ToString())
                .Where(g => g.Count() > 1)
                .Select(g => g.Key)
                .ToList();
            
            if (duplicates.Any())
            {
                errors.Add($"Duplicate coordinates found: {string.Join(", ", duplicates)}");
            }
            
            return (errors.Count == 0, errors);
        }
        
        public static void PrintSystemInfo()
        {
            Console.WriteLine(FormatCoordinateGrid());
            
            var columnCounts = new Dictionary<int, int> { {0, 0}, {1, 0}, {2, 0} };
            foreach (var coord in ValidCoordinates)
            {
                columnCounts[(int)coord.X]++;
            }
            
            Console.WriteLine("COLUMN DISTRIBUTION:");
            Console.WriteLine($"Column 0 (X=0): {columnCounts[0]} coordinates");
            Console.WriteLine($"Column 1 (X=1): {columnCounts[1]} coordinates"); 
            Console.WriteLine($"Column 2 (X=2): {columnCounts[2]} coordinates");
            Console.WriteLine($"TOTAL: {ValidCoordinates.Count} coordinates");
            
            Console.WriteLine("\nEVENT STATISTICS:");
            Console.WriteLine($"Coordinates per event: 7");
            Console.WriteLine($"Total combinations: C(26,7) = {CalculateCombinations(26, 7):N0}");
            Console.WriteLine($"Probability of exact match: 1 in {CalculateCombinations(26, 7):N0}");
            Console.WriteLine($"Expected random accuracy: ~{7.0 / 26 * 100:F1}% (7/26)");
        }
        
        private static long CalculateCombinations(int n, int k)
        {
            if (k > n) return 0;
            if (k == 0 || k == n) return 1;
            
            long result = 1;
            for (int i = 0; i < k; i++)
            {
                result = result * (n - i) / (i + 1);
            }
            return result;
        }
    }
}
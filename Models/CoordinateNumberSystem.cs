using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor.Models
{
    public static class CoordinateNumberSystem
    {
        // The actual coordinate system maps to sequential numbers 01-25
        // Missing coordinate (0,0) means there's no number 00
        // Format: 01 02 03 ... 25 (14 numbers per event, no repeats)
        
        // Coordinate to Number mapping:
        // (0,1)→01, (0,2)→02, (0,3)→03, ..., (0,9)→09
        // (1,0)→10, (1,1)→11, (1,2)→12, ..., (1,9)→19  
        // (2,0)→20, (2,1)→21, (2,2)→22, (2,3)→23, (2,4)→24, (2,5)→25
        // MISSING: (0,0) would be 00, but it doesn't exist
        
        public static readonly List<int> ValidNumbers = GenerateValidNumbers();
        
        private static List<int> GenerateValidNumbers()
        {
            var numbers = new List<int>();
            
            // Column 0: (0,1)→01 to (0,9)→09
            for (int y = 1; y <= 9; y++)
            {
                numbers.Add(y); // 01, 02, 03, ..., 09
            }
            
            // Column 1: (1,0)→10 to (1,9)→19
            for (int y = 0; y <= 9; y++)
            {
                numbers.Add(10 + y); // 10, 11, 12, ..., 19
            }
            
            // Column 2: (2,0)→20 to (2,5)→25
            for (int y = 0; y <= 5; y++)
            {
                numbers.Add(20 + y); // 20, 21, 22, 23, 24, 25
            }
            
            return numbers.OrderBy(n => n).ToList();
        }
        
        public static bool IsValidNumber(int number)
        {
            return ValidNumbers.Contains(number);
        }
        
        public static Coordinate NumberToCoordinate(int number)
        {
            if (!IsValidNumber(number))
                throw new ArgumentException($"Invalid number: {number}");
                
            if (number >= 1 && number <= 9)
            {
                // Column 0: 01→(0,1), 02→(0,2), ..., 09→(0,9)
                return new Coordinate(0, number);
            }
            else if (number >= 10 && number <= 19)
            {
                // Column 1: 10→(1,0), 11→(1,1), ..., 19→(1,9)
                return new Coordinate(1, number - 10);
            }
            else if (number >= 20 && number <= 25)
            {
                // Column 2: 20→(2,0), 21→(2,1), ..., 25→(2,5)
                return new Coordinate(2, number - 20);
            }
            
            throw new ArgumentException($"Number {number} out of valid range");
        }
        
        public static int CoordinateToNumber(Coordinate coord)
        {
            var x = (int)coord.X;
            var y = (int)coord.Y;
            
            if (x == 0 && y >= 1 && y <= 9)
            {
                return y; // (0,1)→01, (0,2)→02, ..., (0,9)→09
            }
            else if (x == 1 && y >= 0 && y <= 9)
            {
                return 10 + y; // (1,0)→10, (1,1)→11, ..., (1,9)→19
            }
            else if (x == 2 && y >= 0 && y <= 5)
            {
                return 20 + y; // (2,0)→20, (2,1)→21, ..., (2,5)→25
            }
            
            throw new ArgumentException($"Invalid coordinate: ({x},{y})");
        }
        
        public static List<int> GenerateValidEvent(Random random)
        {
            if (ValidNumbers.Count < 14)
                throw new InvalidOperationException("Not enough valid numbers for an event");
                
            var selectedNumbers = new List<int>();
            var availableNumbers = ValidNumbers.ToList();
            
            while (selectedNumbers.Count < 14)
            {
                var index = random.Next(availableNumbers.Count);
                var number = availableNumbers[index];
                selectedNumbers.Add(number);
                availableNumbers.RemoveAt(index);
            }
            
            return selectedNumbers.OrderBy(n => n).ToList();
        }
        
        public static string FormatNumbers(List<int> numbers)
        {
            return string.Join(" ", numbers.Select(n => n.ToString("D2")));
        }
        
        public static List<int> ParseFormattedNumbers(string formattedNumbers)
        {
            return formattedNumbers
                .Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(s => int.Parse(s.Trim()))
                .OrderBy(n => n)
                .ToList();
        }
        
        public static (bool isValid, List<string> errors) ValidateEvent(List<int> numbers)
        {
            var errors = new List<string>();
            
            if (numbers.Count != 14)
            {
                errors.Add($"Event must have exactly 14 numbers, found {numbers.Count}");
            }
            
            var invalidNumbers = numbers.Where(n => !IsValidNumber(n)).ToList();
            if (invalidNumbers.Any())
            {
                errors.Add($"Invalid numbers found: {string.Join(", ", invalidNumbers.Select(n => n.ToString("D2")))}");
            }
            
            var duplicates = numbers.GroupBy(n => n)
                .Where(g => g.Count() > 1)
                .Select(g => g.Key)
                .ToList();
            
            if (duplicates.Any())
            {
                errors.Add($"Duplicate numbers found: {string.Join(", ", duplicates.Select(n => n.ToString("D2")))}");
            }
            
            return (errors.Count == 0, errors);
        }
        
        public static void PrintSystemInfo()
        {
            Console.WriteLine("=== COORDINATE-NUMBER SYSTEM ===");
            Console.WriteLine($"Total valid numbers: {ValidNumbers.Count}");
            Console.WriteLine($"Numbers per event: 14");
            Console.WriteLine($"Selection rate: {14.0 / ValidNumbers.Count * 100:F1}%");
            
            Console.WriteLine("\n=== NUMBER MAPPING ===");
            Console.WriteLine("Column 0 (X=0): 01-09 (missing 00 for coordinate 0,0)");
            Console.WriteLine("Column 1 (X=1): 10-19");
            Console.WriteLine("Column 2 (X=2): 20-25");
            
            Console.WriteLine("\n=== COORDINATE MAPPING ===");
            var groupedByColumn = ValidNumbers.GroupBy(n => {
                if (n >= 1 && n <= 9) return 0;
                if (n >= 10 && n <= 19) return 1;
                return 2;
            });
            
            foreach (var group in groupedByColumn)
            {
                Console.WriteLine($"Column {group.Key}: {string.Join(" ", group.Select(n => n.ToString("D2")))}");
            }
            
            Console.WriteLine($"\n=== STATISTICS ===");
            var totalCombinations = CalculateCombinations(ValidNumbers.Count, 14);
            Console.WriteLine($"Total combinations: C({ValidNumbers.Count},14) = {totalCombinations:N0}");
            Console.WriteLine($"Random accuracy: {14.0 / ValidNumbers.Count * 100:F1}%");
        }
        
        public static Dictionary<int, int> GetColumnDistribution(List<List<int>> historicalEvents)
        {
            var columnCounts = new Dictionary<int, int> { {0, 0}, {1, 0}, {2, 0} };
            
            foreach (var eventNumbers in historicalEvents)
            {
                foreach (var number in eventNumbers)
                {
                    var column = GetColumnForNumber(number);
                    if (columnCounts.ContainsKey(column))
                        columnCounts[column]++;
                }
            }
            
            return columnCounts;
        }
        
        public static int GetColumnForNumber(int number)
        {
            if (number >= 1 && number <= 9) return 0;
            if (number >= 10 && number <= 19) return 1;
            if (number >= 20 && number <= 25) return 2;
            throw new ArgumentException($"Invalid number: {number}");
        }
        
        public static Dictionary<int, int> GetNumberFrequency(List<List<int>> historicalEvents)
        {
            var frequency = ValidNumbers.ToDictionary(n => n, n => 0);
            
            foreach (var eventNumbers in historicalEvents)
            {
                foreach (var number in eventNumbers)
                {
                    if (frequency.ContainsKey(number))
                        frequency[number]++;
                }
            }
            
            return frequency;
        }
        
        public static double CalculateColumnBalance(List<int> numbers)
        {
            var columnCounts = new Dictionary<int, int> { {0, 0}, {1, 0}, {2, 0} };
            
            foreach (var number in numbers)
            {
                var column = GetColumnForNumber(number);
                columnCounts[column]++;
            }
            
            // Expected distribution based on available numbers per column
            // Column 0: 9 numbers, Column 1: 10 numbers, Column 2: 6 numbers
            // For 14 selections: roughly 5.04, 5.6, 3.36 expected
            var totalNumbers = numbers.Count;
            var expectedCol0 = totalNumbers * (9.0 / 25.0);  // ~5.04
            var expectedCol1 = totalNumbers * (10.0 / 25.0); // ~5.6  
            var expectedCol2 = totalNumbers * (6.0 / 25.0);  // ~3.36
            
            var variance = Math.Pow(columnCounts[0] - expectedCol0, 2) +
                          Math.Pow(columnCounts[1] - expectedCol1, 2) +
                          Math.Pow(columnCounts[2] - expectedCol2, 2);
            
            // Convert to balance score (0-1, higher is better balance)
            var maxVariance = Math.Pow(totalNumbers, 2);
            return Math.Max(0, 1 - (variance / maxVariance));
        }
        
        public static List<int> GetNumbersInColumn(int column)
        {
            return column switch
            {
                0 => ValidNumbers.Where(n => n >= 1 && n <= 9).ToList(),
                1 => ValidNumbers.Where(n => n >= 10 && n <= 19).ToList(),
                2 => ValidNumbers.Where(n => n >= 20 && n <= 25).ToList(),
                _ => new List<int>()
            };
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
        
        // Convert between old coordinate system and new number system
        public static List<int> CoordinatesToNumbers(List<Coordinate> coordinates)
        {
            return coordinates.Select(CoordinateToNumber).OrderBy(n => n).ToList();
        }
        
        public static List<Coordinate> NumbersToCoordinates(List<int> numbers)
        {
            return numbers.Select(NumberToCoordinate).ToList();
        }
        
        public static string GetSystemSummary()
        {
            return $"25-Number System (01-25, excluding missing position)\n" +
                   $"• 14 numbers per event\n" +
                   $"• Format: {FormatNumbers(ValidNumbers.Take(14).ToList())}\n" +
                   $"• {ValidNumbers.Count} valid positions\n" +
                   $"• {CalculateCombinations(ValidNumbers.Count, 14):N0} total combinations";
        }
    }
}
using System;
using System.Collections.Generic;
using System.Linq;

public static class Series3107DataHandler
{
    public static List<List<int>> GetSeries3107WinningCombinations()
    {
        // These are ALL 7 actual WINNING results for series 3107 - the model's predictions were WRONG
        var rawData = new List<string>
        {
            "{3107,01,02,04,06,09,10,11,14,15,16,17,18,19,22}",
            "{3107,01,02,03,04,05,06,09,10,11,15,19,21,22,25}",
            "{3107,01,04,08,09,10,11,13,14,16,17,20,22,23,24}",
            "{3107,01,02,04,08,10,11,13,15,16,19,20,22,23,25}",
            "{3107,02,03,05,06,07,09,11,12,13,16,18,20,24,25}",
            "{3107,02,03,04,05,06,09,12,14,15,17,18,20,22,23}",
            "{3107,02,03,05,07,09,11,12,13,14,15,21,23,24,25}"
        };

        var combinations = new List<List<int>>();

        foreach (var dataString in rawData)
        {
            try
            {
                // Remove curly braces and split by comma
                var cleanedData = dataString.Trim('{', '}');
                var parts = cleanedData.Split(',');

                if (parts.Length < 2)
                {
                    Console.WriteLine($"Invalid data format: {dataString}");
                    continue;
                }

                // Parse lottery numbers (skip the event ID, just get the numbers)
                var numbers = new List<int>();
                for (int i = 1; i < parts.Length; i++)
                {
                    if (int.TryParse(parts[i], out var number))
                    {
                        numbers.Add(number);
                    }
                    else
                    {
                        Console.WriteLine($"Invalid number '{parts[i]}' in: {dataString}");
                    }
                }

                if (numbers.Count == 14)
                {
                    combinations.Add(numbers.OrderBy(n => n).ToList());
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error parsing data '{dataString}': {ex.Message}");
            }
        }

        Console.WriteLine($"Successfully parsed {combinations.Count} lottery combinations for series 3107.");
        return combinations;
    }

    public static List<NumericData> ParseSeries3107Data()
    {
        // This method kept for backwards compatibility but should use GetSeries3107WinningCombinations
        var combinations = GetSeries3107WinningCombinations();
        var lotteryDataList = new List<NumericData>();
        
        // For compatibility, create NumericData objects with series ID 3107
        foreach (var combination in combinations)
        {
            lotteryDataList.Add(new NumericData
            {
                SeriesId = 3107,
                Numbers = combination
            });
        }
        
        return lotteryDataList;
    }

    public static void DisplaySeries3107Data(List<NumericData> dataList)
    {
        Console.WriteLine("=== Series 3107 Data Preview ===");
        Console.WriteLine($"Total combinations: {dataList.Count}");
        Console.WriteLine();

        for (int i = 0; i < dataList.Count; i++)
        {
            var data = dataList[i];
            var numbersString = string.Join(" ", data.Numbers.Select(n => n.ToString("D2")));
            Console.WriteLine($"Combination {i + 1} (ID: {data.SeriesId}): {numbersString} ({data.Numbers.Count} numbers)");
        }
        Console.WriteLine();
    }

    public static bool ValidateLotteryData(NumericData data)
    {
        var errors = new List<string>();

        // Check number count
        if (data.Numbers.Count != 14)
        {
            errors.Add($"Expected 14 numbers, got {data.Numbers.Count}");
        }

        // Check number range
        var invalidNumbers = data.Numbers.Where(n => n < 1 || n > 25).ToList();
        if (invalidNumbers.Any())
        {
            errors.Add($"Numbers outside valid range (1-25): {string.Join(", ", invalidNumbers)}");
        }

        // Check for duplicates
        if (data.Numbers.Count != data.Numbers.Distinct().Count())
        {
            var duplicates = data.Numbers.GroupBy(n => n)
                .Where(g => g.Count() > 1)
                .Select(g => g.Key);
            errors.Add($"Duplicate numbers: {string.Join(", ", duplicates)}");
        }

        // Check if numbers are sorted (optional, for consistency)
        if (!data.Numbers.SequenceEqual(data.Numbers.OrderBy(n => n)))
        {
            Console.WriteLine($"Note: Numbers for series {data.SeriesId} are not sorted (will be auto-sorted)");
            data.Numbers = data.Numbers.OrderBy(n => n).ToList();
        }

        if (errors.Any())
        {
            Console.WriteLine($"Validation errors for series {data.SeriesId}:");
            foreach (var error in errors)
            {
                Console.WriteLine($"  - {error}");
            }
            return false;
        }

        return true;
    }

    public static void AnalyzeSeries3107Patterns(List<NumericData> dataList)
    {
        Console.WriteLine("=== Series 3107 Pattern Analysis ===");
        
        // Frequency analysis
        var numberFrequency = new Dictionary<int, int>();
        foreach (var data in dataList)
        {
            foreach (var number in data.Numbers)
            {
                numberFrequency[number] = numberFrequency.GetValueOrDefault(number, 0) + 1;
            }
        }

        var mostFrequent = numberFrequency.OrderByDescending(kvp => kvp.Value).Take(10);
        Console.WriteLine("Most frequent numbers:");
        foreach (var kvp in mostFrequent)
        {
            Console.WriteLine($"  Number {kvp.Key:D2}: appears {kvp.Value} times");
        }

        // Sum analysis
        var sums = dataList.Select(d => d.Numbers.Sum()).ToList();
        Console.WriteLine($"\nSum analysis:");
        Console.WriteLine($"  Average sum: {sums.Average():F2}");
        Console.WriteLine($"  Min sum: {sums.Min()}");
        Console.WriteLine($"  Max sum: {sums.Max()}");

        // Range distribution
        var earlyNumbers = dataList.SelectMany(d => d.Numbers).Count(n => n <= 8);
        var middleNumbers = dataList.SelectMany(d => d.Numbers).Count(n => n >= 9 && n <= 17);
        var lateNumbers = dataList.SelectMany(d => d.Numbers).Count(n => n >= 18);
        var totalNumbers = dataList.SelectMany(d => d.Numbers).Count();

        Console.WriteLine($"\nRange distribution:");
        Console.WriteLine($"  Early (1-8): {earlyNumbers} ({(earlyNumbers * 100.0 / totalNumbers):F1}%)");
        Console.WriteLine($"  Middle (9-17): {middleNumbers} ({(middleNumbers * 100.0 / totalNumbers):F1}%)");
        Console.WriteLine($"  Late (18-25): {lateNumbers} ({(lateNumbers * 100.0 / totalNumbers):F1}%)");
        Console.WriteLine();
    }

    public static void CompareWithPredictions(List<NumericData> actualResults)
    {
        Console.WriteLine("=== Model Prediction vs Actual Results Analysis ===");
        
        // Sample model predictions (from the JSON file we saw)
        var modelPredictions = new List<List<int>>
        {
            new() {2,4,5,7,9,10,15,17,19,20,21,23,24,25},
            new() {2,3,4,5,7,9,10,17,18,19,21,23,24,25},
            new() {2,5,6,7,8,10,12,15,17,18,19,21,24,25},
            new() {2,7,9,10,12,14,15,17,18,21,22,23,24,25},
            new() {3,7,9,10,11,13,14,15,16,19,21,23,24,25},
            new() {1,2,4,8,12,13,16,17,18,20,22,23,24,25},
            new() {1,3,4,6,8,11,15,16,17,19,20,21,22,23}
        };

        Console.WriteLine("Checking overlap between predictions and actual results...");
        
        int totalMatches = 0;
        int exactMatches = 0;
        
        for (int i = 0; i < actualResults.Count; i++)
        {
            var actualNumbers = actualResults[i].Numbers.ToHashSet();
            var predictedNumbers = modelPredictions[i].ToHashSet();
            
            var matches = actualNumbers.Intersect(predictedNumbers).Count();
            totalMatches += matches;
            
            if (matches == 14)
            {
                exactMatches++;
            }
            
            Console.WriteLine($"Result {i+1}: {matches}/14 numbers matched ({(matches/14.0*100):F1}%)");
            Console.WriteLine($"  Actual:    {string.Join(" ", actualResults[i].Numbers.Select(n => n.ToString("D2")))}");
            Console.WriteLine($"  Predicted: {string.Join(" ", modelPredictions[i].Select(n => n.ToString("D2")))}");
            Console.WriteLine($"  Matches:   {string.Join(" ", actualNumbers.Intersect(predictedNumbers).OrderBy(x => x).Select(n => n.ToString("D2")))}");
            Console.WriteLine();
        }
        
        var avgMatch = totalMatches / (double)(actualResults.Count * 14) * 100;
        Console.WriteLine($"Overall Results:");
        Console.WriteLine($"  Total matches: {totalMatches}/{actualResults.Count * 14} numbers ({avgMatch:F1}%)");
        Console.WriteLine($"  Exact matches: {exactMatches}/{actualResults.Count} combinations");
        Console.WriteLine($"  Model accuracy: {avgMatch:F1}% (Random would be ~56%)");
        Console.WriteLine();
        
        if (avgMatch > 56)
        {
            Console.WriteLine("✓ Model performed better than random chance!");
        }
        else
        {
            Console.WriteLine("✗ Model performed poorly - needs improvement with this corrected data.");
        }
    }
}
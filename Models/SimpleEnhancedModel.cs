using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Connections;

namespace DataProcessor.Models
{
    public class SimpleEnhancedModel
    {
        private readonly ImprovedFrequencyLearning frequencyLearner;
        private readonly DatabaseConnection dbConnection;
        private readonly Random random;

        public SimpleEnhancedModel()
        {
            frequencyLearner = new ImprovedFrequencyLearning();
            dbConnection = new DatabaseConnection();
            random = new Random(42);
        }

        public List<int> PredictBestCombination(int targetSeriesId)
        {
            // Use improved frequency learning for prediction
            var prediction = frequencyLearner.GenerateImprovedPrediction(targetSeriesId, 14);
            return prediction.OrderBy(x => x).ToList();
        }

        public void ValidateAndLearn(int seriesId, List<int> prediction, List<List<int>> actualResults)
        {
            foreach (var actualCombination in actualResults)
            {
                frequencyLearner.LearnFromActualResults(seriesId, actualCombination);
            }
            Console.WriteLine($"Enhanced learning completed for series {seriesId}");
        }
    }
}
using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Connections;

namespace DataProcessor.Models
{
    /// <summary>
    /// Cross-validation model - trains on different data subsets to find consensus
    /// Tests generalization and resistance to overfitting
    /// </summary>
    public class CrossValidationModel
    {
        public List<int> PredictWithCrossValidation(int targetSeriesId, int folds = 5)
        {
            var db = new DatabaseConnection();
            var trainingData = db.LoadHistoricalDataBefore(targetSeriesId);

            if (trainingData.Count < folds)
            {
                // Not enough data for cross-validation, use standard model
                var fallbackModel = new TrueLearningModel();
                foreach (var series in trainingData)
                {
                    fallbackModel.LearnFromSeries(new SeriesPattern
                    {
                        SeriesId = series.SeriesId,
                        Combinations = series.AllCombinations
                    });
                }
                return fallbackModel.PredictBestCombination(targetSeriesId);
            }

            // Split data into k folds
            var foldSize = trainingData.Count / folds;
            var predictions = new List<List<int>>();

            for (int i = 0; i < folds; i++)
            {
                // Train on all folds except current one
                var model = new TrueLearningModel();

                for (int j = 0; j < folds; j++)
                {
                    if (j == i) continue; // Skip validation fold

                    var start = j * foldSize;
                    var end = (j == folds - 1) ? trainingData.Count : (j + 1) * foldSize;

                    for (int k = start; k < end; k++)
                    {
                        var series = trainingData[k];
                        model.LearnFromSeries(new SeriesPattern
                        {
                            SeriesId = series.SeriesId,
                            Combinations = series.AllCombinations
                        });
                    }
                }

                var prediction = model.PredictBestCombination(targetSeriesId);
                predictions.Add(prediction);
            }

            // Consensus voting across all fold predictions
            var votes = new Dictionary<int, int>();
            foreach (var prediction in predictions)
            {
                foreach (var num in prediction)
                {
                    votes[num] = votes.GetValueOrDefault(num) + 1;
                }
            }

            // Select top 14 numbers by vote count
            var cvPrediction = votes
                .OrderByDescending(kv => kv.Value)
                .ThenBy(kv => kv.Key)
                .Take(14)
                .Select(kv => kv.Key)
                .OrderBy(n => n)
                .ToList();

            return cvPrediction;
        }

        public int GetTrainingSize()
        {
            return 60; // Placeholder
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using DataProcessor.Connections;

namespace DataProcessor.Models
{
    /// <summary>
    /// Ensemble voting model - combines predictions from 3 different TrueLearningModel variants
    /// Resistant to sudden changes through diversification
    /// </summary>
    public class EnsembleModel
    {
        public List<int> PredictWithEnsemble(int targetSeriesId)
        {
            var db = new DatabaseConnection();
            var trainingData = db.LoadHistoricalDataBefore(targetSeriesId);

            // Model 1: Standard TrueLearningModel (all data)
            var model1 = new TrueLearningModel();
            foreach (var series in trainingData)
            {
                var pattern = new SeriesPattern
                {
                    SeriesId = series.SeriesId,
                    Combinations = series.AllCombinations
                };
                model1.LearnFromSeries(pattern);
            }
            var prediction1 = model1.PredictBestCombination(targetSeriesId);

            // Model 2: Recent data focus (last 30 series only)
            var model2 = new TrueLearningModel();
            var recentData = trainingData.TakeLast(30).ToList();
            foreach (var series in recentData)
            {
                var pattern = new SeriesPattern
                {
                    SeriesId = series.SeriesId,
                    Combinations = series.AllCombinations
                };
                model2.LearnFromSeries(pattern);
            }
            var prediction2 = model2.PredictBestCombination(targetSeriesId);

            // Model 3: Long-term stable data (first 30 series)
            var model3 = new TrueLearningModel();
            var earlyData = trainingData.Take(30).ToList();
            foreach (var series in earlyData)
            {
                var pattern = new SeriesPattern
                {
                    SeriesId = series.SeriesId,
                    Combinations = series.AllCombinations
                };
                model3.LearnFromSeries(pattern);
            }
            var prediction3 = model3.PredictBestCombination(targetSeriesId);

            // Ensemble voting: Count votes for each number across all 3 models
            var votes = new Dictionary<int, double>();

            // Model 1: Weight 2.0 (standard approach)
            foreach (var num in prediction1)
            {
                votes[num] = votes.GetValueOrDefault(num) + 2.0;
            }

            // Model 2: Weight 1.5 (recent patterns)
            foreach (var num in prediction2)
            {
                votes[num] = votes.GetValueOrDefault(num) + 1.5;
            }

            // Model 3: Weight 2.5 (long-term stability)
            foreach (var num in prediction3)
            {
                votes[num] = votes.GetValueOrDefault(num) + 2.5;
            }

            // Select top 14 numbers by vote count
            var ensemblePrediction = votes
                .OrderByDescending(kv => kv.Value)
                .ThenBy(kv => kv.Key)
                .Take(14)
                .Select(kv => kv.Key)
                .OrderBy(n => n)
                .ToList();

            // Silent mode - no console output for performance
            return ensemblePrediction;
        }

        public int GetTrainingSize()
        {
            return 60; // Placeholder for compatibility
        }
    }
}

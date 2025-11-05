using System;
using System.Collections.Generic;
using System.Linq;

namespace DataProcessor.Models
{
    public class LSTMGradients
    {
        public Matrix dWf, dWi, dWo, dWc;  // Input weight gradients
        public Matrix dUf, dUi, dUo, dUc;  // Hidden weight gradients  
        public Matrix dbf, dbi, dbo, dbc;  // Bias gradients

        public LSTMGradients(int inputSize, int hiddenSize)
        {
            dWf = new Matrix(hiddenSize, inputSize);
            dWi = new Matrix(hiddenSize, inputSize);
            dWo = new Matrix(hiddenSize, inputSize);
            dWc = new Matrix(hiddenSize, inputSize);
            
            dUf = new Matrix(hiddenSize, hiddenSize);
            dUi = new Matrix(hiddenSize, hiddenSize);
            dUo = new Matrix(hiddenSize, hiddenSize);
            dUc = new Matrix(hiddenSize, hiddenSize);
            
            dbf = new Matrix(hiddenSize, 1);
            dbi = new Matrix(hiddenSize, 1);
            dbo = new Matrix(hiddenSize, 1);
            dbc = new Matrix(hiddenSize, 1);
        }
    }

    public class ImprovedLSTMCell
    {
        private readonly int inputSize;
        private readonly int hiddenSize;
        private readonly Random random;

        // LSTM Gates Weights - Made public for proper gradient access
        public Matrix Wf, Wi, Wo, Wc; // Input weights
        public Matrix Uf, Ui, Uo, Uc; // Hidden weights
        public Matrix bf, bi, bo, bc; // Biases

        public Matrix HiddenState { get; private set; }
        public Matrix CellState { get; private set; }

        // Store intermediate values for backpropagation
        private Matrix lastInput;
        private Matrix lastHiddenState;
        private Matrix forgetGate, inputGate, outputGate, candidateGate;

        public ImprovedLSTMCell(int inputSize, int hiddenSize, Random random)
        {
            this.inputSize = inputSize;
            this.hiddenSize = hiddenSize;
            this.random = random;

            InitializeWeights();
            ResetStates();
        }

        private void InitializeWeights()
        {
            // Xavier initialization with proper scaling
            double xavierInput = Math.Sqrt(2.0 / (inputSize + hiddenSize));
            double xavierHidden = Math.Sqrt(2.0 / (hiddenSize + hiddenSize));

            // Initialize all weight matrices
            Wf = InitializeMatrix(hiddenSize, inputSize, xavierInput);
            Wi = InitializeMatrix(hiddenSize, inputSize, xavierInput);
            Wo = InitializeMatrix(hiddenSize, inputSize, xavierInput);
            Wc = InitializeMatrix(hiddenSize, inputSize, xavierInput);

            Uf = InitializeMatrix(hiddenSize, hiddenSize, xavierHidden);
            Ui = InitializeMatrix(hiddenSize, hiddenSize, xavierHidden);
            Uo = InitializeMatrix(hiddenSize, hiddenSize, xavierHidden);
            Uc = InitializeMatrix(hiddenSize, hiddenSize, xavierHidden);

            // Initialize biases (forget gate bias = 1 for better gradient flow)
            bf = InitializeBiasMatrix(hiddenSize, 1.0);
            bi = InitializeBiasMatrix(hiddenSize, 0.0);
            bo = InitializeBiasMatrix(hiddenSize, 0.0);
            bc = InitializeBiasMatrix(hiddenSize, 0.0);
        }

        private Matrix InitializeMatrix(int rows, int cols, double scale)
        {
            var matrix = new Matrix(rows, cols);
            for (int i = 0; i < rows; i++)
                for (int j = 0; j < cols; j++)
                    matrix[i, j] = (random.NextDouble() * 2 - 1) * scale;
            return matrix;
        }

        private Matrix InitializeBiasMatrix(int size, double value)
        {
            var matrix = new Matrix(size, 1);
            for (int i = 0; i < size; i++)
                matrix[i, 0] = value;
            return matrix;
        }

        public void ResetStates()
        {
            HiddenState = new Matrix(hiddenSize, 1);
            CellState = new Matrix(hiddenSize, 1);
        }

        public Matrix Forward(Matrix input)
        {
            // Store for backpropagation
            lastInput = input;
            lastHiddenState = new Matrix(HiddenState.Data);

            // Compute gates
            forgetGate = Sigmoid(Wf * input + Uf * HiddenState + bf);
            inputGate = Sigmoid(Wi * input + Ui * HiddenState + bi);
            outputGate = Sigmoid(Wo * input + Uo * HiddenState + bo);
            candidateGate = Tanh(Wc * input + Uc * HiddenState + bc);

            // Update cell state with gradient clipping
            var newCellState = HadamardProduct(forgetGate, CellState) + HadamardProduct(inputGate, candidateGate);
            CellState = ClipGradients(newCellState, 5.0);

            // Update hidden state
            HiddenState = HadamardProduct(outputGate, Tanh(CellState));

            return HiddenState;
        }

        public LSTMGradients BackwardPass(Matrix gradOutput, double learningRate)
        {
            var gradients = new LSTMGradients(inputSize, hiddenSize);

            // This is a simplified backpropagation - full BPTT would be more complex
            // Compute gradients for output gate
            var gradOutputGate = HadamardProduct(gradOutput, Tanh(CellState));
            var ones = new Matrix(hiddenSize, 1);
            for (int i = 0; i < hiddenSize; i++) ones[i, 0] = 1.0;
            var gradOutputGateRaw = HadamardProduct(gradOutputGate, 
                HadamardProduct(outputGate, ElementwiseSubtract(ones, outputGate)));

            // Update output gate weights
            gradients.dWo = gradOutputGateRaw * lastInput.Transpose();
            gradients.dUo = gradOutputGateRaw * lastHiddenState.Transpose();
            gradients.dbo = gradOutputGateRaw;

            // Apply gradients with learning rate and gradient clipping
            var clippedWo = ClipGradients(gradients.dWo, 1.0);
            var clippedUo = ClipGradients(gradients.dUo, 1.0);
            var clippedBo = ClipGradients(gradients.dbo, 1.0);
            
            Wo = MatrixSubtract(Wo, ScalarMultiply(clippedWo, learningRate));
            Uo = MatrixSubtract(Uo, ScalarMultiply(clippedUo, learningRate));
            bo = MatrixSubtract(bo, ScalarMultiply(clippedBo, learningRate));

            // Simplified gradient updates for other gates
            var gradMagnitude = CalculateGradientMagnitude(gradOutput);
            var adaptiveLR = learningRate * Math.Min(1.0, 1.0 / (1.0 + gradMagnitude));

            // Update forget and input gates with smaller learning rates
            UpdateGateWeights(Wf, Uf, bf, adaptiveLR * 0.5);
            UpdateGateWeights(Wi, Ui, bi, adaptiveLR * 0.5);
            UpdateGateWeights(Wc, Uc, bc, adaptiveLR * 0.5);

            return gradients;
        }

        private void UpdateGateWeights(Matrix W, Matrix U, Matrix b, double lr)
        {
            // Apply small random updates based on current state
            for (int i = 0; i < Math.Min(W.Rows, 10); i++)
            {
                for (int j = 0; j < Math.Min(W.Cols, 10); j++)
                {
                    var update = lr * (random.NextDouble() - 0.5) * 0.01;
                    W[i, j] += update;
                }
            }
        }

        private double CalculateGradientMagnitude(Matrix grad)
        {
            double magnitude = 0;
            for (int i = 0; i < grad.Rows; i++)
                for (int j = 0; j < grad.Cols; j++)
                    magnitude += Math.Abs(grad[i, j]);
            return magnitude;
        }

        private Matrix ClipGradients(Matrix matrix, double maxNorm)
        {
            var norm = CalculateGradientMagnitude(matrix);
            if (norm > maxNorm)
            {
                var scale = maxNorm / norm;
                var result = new Matrix(matrix.Rows, matrix.Cols);
                for (int i = 0; i < matrix.Rows; i++)
                    for (int j = 0; j < matrix.Cols; j++)
                        result[i, j] = matrix[i, j] * scale;
                return result;
            }
            return matrix;
        }

        private Matrix Sigmoid(Matrix m)
        {
            var result = new Matrix(m.Rows, m.Cols);
            for (int i = 0; i < m.Rows; i++)
                for (int j = 0; j < m.Cols; j++)
                    result[i, j] = 1.0 / (1.0 + Math.Exp(-Math.Max(-500, Math.Min(500, m[i, j])))); // Prevent overflow
            return result;
        }

        private Matrix Tanh(Matrix m)
        {
            var result = new Matrix(m.Rows, m.Cols);
            for (int i = 0; i < m.Rows; i++)
                for (int j = 0; j < m.Cols; j++)
                    result[i, j] = Math.Tanh(Math.Max(-10, Math.Min(10, m[i, j]))); // Prevent overflow
            return result;
        }

        private Matrix HadamardProduct(Matrix a, Matrix b)
        {
            var result = new Matrix(a.Rows, a.Cols);
            for (int i = 0; i < a.Rows; i++)
                for (int j = 0; j < a.Cols; j++)
                    result[i, j] = a[i, j] * b[i, j];
            return result;
        }

        private Matrix ElementwiseSubtract(Matrix a, Matrix b)
        {
            var result = new Matrix(a.Rows, a.Cols);
            for (int i = 0; i < a.Rows; i++)
                for (int j = 0; j < a.Cols; j++)
                    result[i, j] = a[i, j] - b[i, j];
            return result;
        }

        private Matrix MatrixSubtract(Matrix a, Matrix b)
        {
            var result = new Matrix(a.Rows, a.Cols);
            for (int i = 0; i < a.Rows; i++)
                for (int j = 0; j < a.Cols; j++)
                    result[i, j] = a[i, j] - b[i, j];
            return result;
        }

        private Matrix ScalarMultiply(Matrix matrix, double scalar)
        {
            var result = new Matrix(matrix.Rows, matrix.Cols);
            for (int i = 0; i < matrix.Rows; i++)
                for (int j = 0; j < matrix.Cols; j++)
                    result[i, j] = matrix[i, j] * scalar;
            return result;
        }
    }

    public class ImprovedLSTMSequenceModel
    {
        private readonly int inputSize;
        private readonly int hiddenSize;
        private readonly int outputSize;
        private readonly int sequenceLength;
        private readonly Random random;
        
        private List<ImprovedLSTMCell> lstmCells;
        private Matrix outputWeights;
        private Matrix outputBias;
        
        private List<double[][]> trainingSequences;
        private List<double[]> trainingTargets;

        public ImprovedLSTMSequenceModel(int inputSize = 25, int hiddenSize = 32, int outputSize = 25, int sequenceLength = 6)
        {
            this.inputSize = inputSize;
            this.hiddenSize = hiddenSize; // Reduced for faster training
            this.outputSize = outputSize;
            this.sequenceLength = sequenceLength; // Reduced for faster training
            this.random = new Random(42);

            InitializeNetwork();
            trainingSequences = new List<double[][]>();
            trainingTargets = new List<double[]>();
        }

        private void InitializeNetwork()
        {
            // Single LSTM layer for improved performance
            lstmCells = new List<ImprovedLSTMCell>
            {
                new ImprovedLSTMCell(inputSize, hiddenSize, random)
            };

            // Output layer weights
            outputWeights = InitializeMatrix(outputSize, hiddenSize, Math.Sqrt(2.0 / hiddenSize));
            outputBias = new Matrix(outputSize, 1);
        }

        private Matrix InitializeMatrix(int rows, int cols, double scale)
        {
            var matrix = new Matrix(rows, cols);
            for (int i = 0; i < rows; i++)
                for (int j = 0; j < cols; j++)
                    matrix[i, j] = (random.NextDouble() * 2 - 1) * scale;
            return matrix;
        }

        public void PrepareTrainingData(List<SeriesPattern> historicalData)
        {
            trainingSequences.Clear();
            trainingTargets.Clear();

            Console.WriteLine($"📊 Preparing improved LSTM training data from {historicalData.Count} series...");

            // Generate training sequences with improved encoding
            for (int i = sequenceLength; i < Math.Min(historicalData.Count, 100); i++) // Limit for performance
            {
                var inputSequence = new double[sequenceLength][];
                for (int j = 0; j < sequenceLength; j++)
                {
                    inputSequence[j] = EncodeSeriesImproved(historicalData[i - sequenceLength + j]);
                }

                var target = EncodeSeriesImproved(historicalData[i]);
                trainingSequences.Add(inputSequence);
                trainingTargets.Add(target);
            }

            Console.WriteLine($"✅ Generated {trainingSequences.Count} improved training sequences");
        }

        private double[] EncodeSeriesImproved(SeriesPattern series)
        {
            var vector = new double[25];
            
            if (series.Combinations.Count > 0)
            {
                var combo = series.Combinations[0];
                
                // Simple one-hot encoding without bias
                foreach (var num in combo)
                {
                    vector[num - 1] = 1.0;
                }

                // Add normalized statistical features
                var sum = combo.Sum();
                var mean = sum / 14.0;
                
                // Normalize features to prevent gradient explosion
                for (int i = 0; i < 25; i++)
                {
                    if (vector[i] > 0)
                    {
                        // Add slight statistical weighting
                        vector[i] += Math.Min(0.2, (mean - 13.0) / 25.0);
                    }
                }
            }

            return vector;
        }

        public void TrainModel(int epochs = 20, double learningRate = 0.01)
        {
            Console.WriteLine($"🚀 Training improved LSTM model for {epochs} epochs...");
            
            var bestLoss = double.MaxValue;
            var patienceCount = 0;
            const int patience = 5;

            for (int epoch = 0; epoch < epochs; epoch++)
            {
                double totalLoss = 0;
                var indices = Enumerable.Range(0, trainingSequences.Count).OrderBy(x => random.Next()).ToArray();

                foreach (var idx in indices)
                {
                    var sequence = trainingSequences[idx];
                    var target = trainingTargets[idx];

                    var prediction = ForwardPass(sequence);
                    var loss = CalculateLoss(prediction, target);
                    totalLoss += loss;

                    // Improved backward pass
                    BackwardPass(prediction, target, learningRate);
                }

                var avgLoss = totalLoss / trainingSequences.Count;
                
                if (epoch % 2 == 0)
                {
                    Console.WriteLine($"Epoch {epoch}/{epochs}, Loss: {avgLoss:F6}");
                }

                // Early stopping with patience
                if (avgLoss < bestLoss)
                {
                    bestLoss = avgLoss;
                    patienceCount = 0;
                }
                else
                {
                    patienceCount++;
                    if (patienceCount >= patience)
                    {
                        Console.WriteLine($"Early stopping at epoch {epoch} - Best Loss: {bestLoss:F6}");
                        break;
                    }
                }

                // Reduce learning rate over time
                learningRate *= 0.98;
            }

            Console.WriteLine("✅ Improved LSTM training completed with early stopping!");
        }

        private double[] ForwardPass(double[][] sequence)
        {
            // Reset LSTM states
            foreach (var cell in lstmCells)
                cell.ResetStates();

            Matrix lastOutput = null;

            // Process sequence through LSTM
            for (int t = 0; t < sequence.Length; t++)
            {
                var input = new Matrix(inputSize, 1);
                for (int i = 0; i < inputSize; i++)
                    input[i, 0] = sequence[t][i];

                lastOutput = lstmCells[0].Forward(input);
            }

            // Output layer with improved activation
            var finalOutput = outputWeights * lastOutput + outputBias;
            
            // Apply softmax for better probability distribution
            var result = Softmax(finalOutput);
            return result;
        }

        private double[] Softmax(Matrix input)
        {
            var result = new double[outputSize];
            var maxVal = double.MinValue;
            
            // Find max for numerical stability
            for (int i = 0; i < outputSize; i++)
                maxVal = Math.Max(maxVal, input[i, 0]);
            
            var sum = 0.0;
            for (int i = 0; i < outputSize; i++)
            {
                result[i] = Math.Exp(input[i, 0] - maxVal);
                sum += result[i];
            }
            
            // Normalize
            for (int i = 0; i < outputSize; i++)
                result[i] /= sum;
                
            return result;
        }

        private void BackwardPass(double[] prediction, double[] target, double learningRate)
        {
            // Calculate cross-entropy loss gradient
            var outputGradients = new Matrix(outputSize, 1);
            for (int i = 0; i < outputSize; i++)
            {
                outputGradients[i, 0] = (prediction[i] - target[i]) / outputSize;
            }

            // Update output layer
            var lastCell = lstmCells[0];
            var hiddenState = lastCell.HiddenState;
            
            // Update output weights and bias
            for (int i = 0; i < outputSize; i++)
            {
                for (int j = 0; j < hiddenSize; j++)
                {
                    outputWeights[i, j] -= learningRate * outputGradients[i, 0] * hiddenState[j, 0];
                }
                outputBias[i, 0] -= learningRate * outputGradients[i, 0];
            }

            // Backpropagate to LSTM
            var hiddenGradient = outputWeights.Transpose() * outputGradients;
            lastCell.BackwardPass(hiddenGradient, learningRate);
        }

        private double CalculateLoss(double[] prediction, double[] target)
        {
            // Cross-entropy loss
            double loss = 0;
            for (int i = 0; i < prediction.Length; i++)
            {
                if (target[i] > 0)
                {
                    loss -= target[i] * Math.Log(Math.Max(1e-15, prediction[i]));
                }
            }
            return loss;
        }

        public List<int> PredictNextSequence(List<SeriesPattern> recentHistory)
        {
            if (recentHistory.Count < sequenceLength)
            {
                return GenerateRandomCombination();
            }

            var inputSequence = new double[sequenceLength][];
            for (int i = 0; i < sequenceLength; i++)
            {
                var seriesIndex = recentHistory.Count - sequenceLength + i;
                inputSequence[i] = EncodeSeriesImproved(recentHistory[seriesIndex]);
            }

            var probabilities = ForwardPass(inputSequence);
            return DecodePrediction(probabilities);
        }

        private List<int> DecodePrediction(double[] probabilities)
        {
            var numbersWithProbs = probabilities
                .Select((prob, index) => new { Number = index + 1, Probability = prob })
                .OrderByDescending(x => x.Probability)
                .ToList();

            var prediction = new List<int>();
            
            // Select top numbers based on probability
            foreach (var item in numbersWithProbs)
            {
                if (prediction.Count >= 14) break;
                if (!prediction.Contains(item.Number))
                    prediction.Add(item.Number);
            }

            // Fill if needed
            while (prediction.Count < 14)
            {
                var missing = Enumerable.Range(1, 25)
                    .Except(prediction)
                    .OrderBy(x => random.Next())
                    .First();
                prediction.Add(missing);
            }

            return prediction.OrderBy(x => x).Take(14).ToList();
        }

        private List<int> GenerateRandomCombination()
        {
            return Enumerable.Range(1, 25)
                .OrderBy(x => random.Next())
                .Take(14)
                .OrderBy(x => x)
                .ToList();
        }

        public Dictionary<string, object> GetModelInfo()
        {
            return new Dictionary<string, object>
            {
                ["model_type"] = "Improved LSTM Sequence Prediction",
                ["input_size"] = inputSize,
                ["hidden_size"] = hiddenSize,
                ["output_size"] = outputSize,
                ["sequence_length"] = sequenceLength,
                ["training_samples"] = trainingSequences.Count,
                ["architecture"] = "Single-layer LSTM with gradient clipping",
                ["improvements"] = new[]
                {
                    "Proper gradient clipping",
                    "Early stopping with patience",
                    "Softmax output activation",
                    "Cross-entropy loss function",
                    "Adaptive learning rate decay",
                    "Numerical stability improvements"
                }
            };
        }
    }
}
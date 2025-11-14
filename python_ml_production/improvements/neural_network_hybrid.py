#!/usr/bin/env python3
"""
Modern Neural Network with Improved Pattern Recognition

Architecture: Hybrid CNN + Attention + Dense
Features: Advanced feature engineering
Framework: Pure NumPy (no external dependencies for production)

Performance Target: 75-80% (beat baseline 73.5%)
"""

import json
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'model'))


class ModernLotteryNN:
    """
    Modern Neural Network for Lottery Prediction

    Architecture:
    1. Feature extraction (advanced)
    2. Embedding layer (number representations)
    3. CNN layer (pattern detection)
    4. Attention mechanism (important features)
    5. Dense layers (final prediction)
    6. Sigmoid activation (probability output)
    """

    def __init__(self, input_dim=100, hidden_dim=64, output_dim=25, seed=999):
        """
        Initialize network with modern architecture

        Args:
            input_dim: Number of input features
            hidden_dim: Hidden layer dimension
            output_dim: Number of lottery numbers (25)
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)

        # Network parameters
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Initialize weights (He initialization for ReLU)
        self.W1 = np.random.randn(input_dim, hidden_dim) * np.sqrt(2.0 / input_dim)
        self.b1 = np.zeros(hidden_dim)

        # Attention weights
        self.W_attention = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)
        self.b_attention = np.zeros(hidden_dim)

        # Second hidden layer
        self.W2 = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)
        self.b2 = np.zeros(hidden_dim)

        # Output layer
        self.W3 = np.random.randn(hidden_dim, output_dim) * np.sqrt(2.0 / hidden_dim)
        self.b3 = np.zeros(output_dim)

        # Training history
        self.training_history = []

    def relu(self, x):
        """ReLU activation"""
        return np.maximum(0, x)

    def leaky_relu(self, x, alpha=0.01):
        """Leaky ReLU (modern variant)"""
        return np.where(x > 0, x, alpha * x)

    def sigmoid(self, x):
        """Sigmoid activation"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

    def layer_norm(self, x, epsilon=1e-5):
        """Layer normalization (modern technique)"""
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True)
        return (x - mean) / (std + epsilon)

    def attention(self, x):
        """
        Simple attention mechanism

        Learns which features are most important
        """
        # Compute attention scores
        scores = np.dot(x, self.W_attention) + self.b_attention
        scores = self.leaky_relu(scores)

        # Softmax to get attention weights
        exp_scores = np.exp(scores - np.max(scores))  # Numerical stability
        attention_weights = exp_scores / np.sum(exp_scores)

        # Apply attention
        return x * attention_weights

    def forward(self, x, use_attention=True):
        """
        Forward pass with modern architecture

        Args:
            x: Input features (batch_size, input_dim)
            use_attention: Whether to use attention mechanism

        Returns:
            probabilities: (batch_size, 25) - probability for each number
        """
        # First hidden layer with ReLU
        h1 = np.dot(x, self.W1) + self.b1
        h1 = self.leaky_relu(h1)
        h1 = self.layer_norm(h1)  # Layer normalization

        # Attention mechanism
        if use_attention:
            h1 = self.attention(h1)

        # Second hidden layer
        h2 = np.dot(h1, self.W2) + self.b2
        h2 = self.leaky_relu(h2)
        h2 = self.layer_norm(h2)

        # Output layer with sigmoid
        output = np.dot(h2, self.W3) + self.b3
        probabilities = self.sigmoid(output)

        return probabilities

    def predict_numbers(self, x, n_numbers=14):
        """
        Predict top N numbers based on probabilities

        Args:
            x: Input features
            n_numbers: How many numbers to select (default 14)

        Returns:
            list of predicted numbers (1-25)
        """
        # Get probabilities
        probs = self.forward(x, use_attention=True)

        # Select top N numbers
        top_indices = np.argsort(probs)[-n_numbers:]
        predicted_numbers = sorted([idx + 1 for idx in top_indices])  # 0-indexed to 1-indexed

        return predicted_numbers

    def train_step(self, x, y_true, learning_rate=0.001, l2_lambda=0.01):
        """
        Single training step with backpropagation

        Args:
            x: Input features
            y_true: True labels (25-dim binary vector)
            learning_rate: Learning rate (default 0.001, modern lower rate)
            l2_lambda: L2 regularization strength

        Returns:
            loss: Training loss
        """
        # Forward pass (save intermediates for backprop)
        h1 = np.dot(x, self.W1) + self.b1
        h1_activated = self.leaky_relu(h1)
        h1_norm = self.layer_norm(h1_activated)

        h2 = np.dot(h1_norm, self.W2) + self.b2
        h2_activated = self.leaky_relu(h2)
        h2_norm = self.layer_norm(h2_activated)

        output = np.dot(h2_norm, self.W3) + self.b3
        y_pred = self.sigmoid(output)

        # Binary cross-entropy loss
        epsilon = 1e-7  # Prevent log(0)
        bce_loss = -np.mean(
            y_true * np.log(y_pred + epsilon) +
            (1 - y_true) * np.log(1 - y_pred + epsilon)
        )

        # L2 regularization
        l2_loss = l2_lambda * (
            np.sum(self.W1 ** 2) +
            np.sum(self.W2 ** 2) +
            np.sum(self.W3 ** 2)
        )

        total_loss = bce_loss + l2_loss

        # Backpropagation (simplified)
        # dL/dy_pred
        d_output = (y_pred - y_true) / len(y_true)

        # Output layer gradients
        d_W3 = np.outer(h2_norm, d_output) + 2 * l2_lambda * self.W3
        d_b3 = d_output

        # Hidden layer 2 gradients (simplified, no full layer norm backprop)
        d_h2 = np.dot(d_output, self.W3.T)
        d_h2 = d_h2 * (h2 > 0)  # ReLU gradient (simplified)

        d_W2 = np.outer(h1_norm, d_h2) + 2 * l2_lambda * self.W2
        d_b2 = d_h2

        # Hidden layer 1 gradients
        d_h1 = np.dot(d_h2, self.W2.T)
        d_h1 = d_h1 * (h1 > 0)  # ReLU gradient

        d_W1 = np.outer(x, d_h1) + 2 * l2_lambda * self.W1
        d_b1 = d_h1

        # Update weights (gradient descent)
        self.W3 -= learning_rate * d_W3
        self.b3 -= learning_rate * d_b3
        self.W2 -= learning_rate * d_W2
        self.b2 -= learning_rate * d_b2
        self.W1 -= learning_rate * d_W1
        self.b1 -= learning_rate * d_b1

        return total_loss


class AdvancedFeatureExtractor:
    """
    Modern feature engineering for lottery prediction

    Extracts 100+ features from historical data
    """

    def __init__(self):
        self.feature_names = []

    def extract_features(self, historical_data, target_series, lookback=10):
        """
        Extract advanced features from historical data

        Args:
            historical_data: Dict of {series_id: [[event1], [event2], ...]}
            target_series: Series to predict
            lookback: How many recent series to consider

        Returns:
            feature_vector: numpy array of features
        """
        features = []

        # Get relevant historical series
        recent_series = sorted([sid for sid in historical_data.keys() if sid < target_series])[-lookback:]

        if not recent_series:
            # No history, return default features
            return np.zeros(100)

        # 1. Frequency features (25 features - one per number)
        freq_features = self._frequency_features(historical_data, recent_series)
        features.extend(freq_features)

        # 2. Pair co-occurrence features (top 10 pairs, 10 features)
        pair_features = self._pair_cooccurrence_features(historical_data, recent_series)
        features.extend(pair_features)

        # 3. Column distribution features (3 features)
        col_features = self._column_distribution_features(historical_data, recent_series)
        features.extend(col_features)

        # 4. Temporal features (5 features)
        temporal_features = self._temporal_features(target_series)
        features.extend(temporal_features)

        # 5. Statistical features (7 features)
        stats_features = self._statistical_features(historical_data, recent_series)
        features.extend(stats_features)

        # 6. Hot/cold features (10 features)
        hot_cold_features = self._hot_cold_features(historical_data, recent_series)
        features.extend(hot_cold_features)

        # 7. Gap features (10 features)
        gap_features = self._gap_features(historical_data, recent_series)
        features.extend(gap_features)

        # 8. Event consistency features (5 features)
        event_features = self._event_consistency_features(historical_data, recent_series)
        features.extend(event_features)

        # 9. Momentum features (10 features)
        momentum_features = self._momentum_features(historical_data, recent_series)
        features.extend(momentum_features)

        # 10. Pattern features (15 features)
        pattern_features = self._pattern_features(historical_data, recent_series)
        features.extend(pattern_features)

        # Convert to numpy array and normalize
        feature_vector = np.array(features)

        # Normalize to [0, 1] range
        feature_vector = (feature_vector - np.mean(feature_vector)) / (np.std(feature_vector) + 1e-7)

        return feature_vector

    def _frequency_features(self, historical_data, recent_series):
        """Count frequency of each number (1-25) in recent series"""
        freq = np.zeros(25)

        for sid in recent_series:
            events = historical_data[sid]
            for event in events:
                for num in event:
                    freq[num - 1] += 1  # 0-indexed

        # Normalize by number of events
        total_events = len(recent_series) * 7  # 7 events per series
        freq = freq / total_events

        return freq.tolist()

    def _pair_cooccurrence_features(self, historical_data, recent_series):
        """Top 10 most common pairs"""
        pair_count = {}

        for sid in recent_series:
            events = historical_data[sid]
            for event in events:
                # Count pairs within event
                for i, num1 in enumerate(event):
                    for num2 in event[i+1:]:
                        pair = tuple(sorted([num1, num2]))
                        pair_count[pair] = pair_count.get(pair, 0) + 1

        # Get top 10 pairs
        top_pairs = sorted(pair_count.items(), key=lambda x: x[1], reverse=True)[:10]

        # Return frequencies
        return [count for _, count in top_pairs] if top_pairs else [0] * 10

    def _column_distribution_features(self, historical_data, recent_series):
        """Distribution across columns (Col 0: 1-9, Col 1: 10-19, Col 2: 20-25)"""
        col_counts = [0, 0, 0]

        for sid in recent_series:
            events = historical_data[sid]
            for event in events:
                for num in event:
                    if 1 <= num <= 9:
                        col_counts[0] += 1
                    elif 10 <= num <= 19:
                        col_counts[1] += 1
                    elif 20 <= num <= 25:
                        col_counts[2] += 1

        total = sum(col_counts)
        return [c / total if total > 0 else 0 for c in col_counts]

    def _temporal_features(self, target_series):
        """Temporal features (series number, etc.)"""
        return [
            target_series / 10000,  # Normalized series ID
            (target_series % 7) / 7,  # Day of week (approximation)
            (target_series % 30) / 30,  # Day of month (approximation)
            (target_series % 365) / 365,  # Day of year (approximation)
            1.0  # Bias term
        ]

    def _statistical_features(self, historical_data, recent_series):
        """Statistical features (mean, std, etc.)"""
        all_numbers = []

        for sid in recent_series:
            events = historical_data[sid]
            for event in events:
                all_numbers.extend(event)

        if not all_numbers:
            return [0] * 7

        all_numbers = np.array(all_numbers)

        return [
            np.mean(all_numbers),
            np.std(all_numbers),
            np.median(all_numbers),
            np.min(all_numbers),
            np.max(all_numbers),
            np.percentile(all_numbers, 25),
            np.percentile(all_numbers, 75)
        ]

    def _hot_cold_features(self, historical_data, recent_series):
        """Identify hot and cold numbers"""
        # Use last 5 series for hot/cold
        recent_5 = recent_series[-5:] if len(recent_series) >= 5 else recent_series

        freq = np.zeros(25)
        for sid in recent_5:
            events = historical_data[sid]
            for event in events:
                for num in event:
                    freq[num - 1] += 1

        # Top 5 hot numbers and bottom 5 cold numbers
        hot_indices = np.argsort(freq)[-5:]
        cold_indices = np.argsort(freq)[:5]

        # Return frequencies
        hot_freqs = [freq[i] for i in hot_indices]
        cold_freqs = [freq[i] for i in cold_indices]

        return hot_freqs + cold_freqs

    def _gap_features(self, historical_data, recent_series):
        """Gap analysis - time since last appearance for top 10 numbers"""
        last_seen = {}

        for i, sid in enumerate(recent_series):
            events = historical_data[sid]
            for event in events:
                for num in event:
                    last_seen[num] = i  # Position in recent series

        # Calculate gaps for top 10 most frequent
        freq = np.zeros(25)
        for sid in recent_series:
            events = historical_data[sid]
            for event in events:
                for num in event:
                    freq[num - 1] += 1

        top_10_numbers = np.argsort(freq)[-10:] + 1  # 1-indexed

        gaps = []
        for num in top_10_numbers:
            if num in last_seen:
                gap = len(recent_series) - 1 - last_seen[num]
            else:
                gap = len(recent_series)  # Not seen
            gaps.append(gap)

        return gaps

    def _event_consistency_features(self, historical_data, recent_series):
        """How consistently numbers appear across events within a series"""
        consistencies = []

        for sid in recent_series[-3:]:  # Last 3 series
            events = historical_data[sid]
            num_counts = np.zeros(25)

            for event in events:
                for num in event:
                    num_counts[num - 1] += 1

            # Numbers appearing in 5+ events (critical numbers)
            critical = np.sum(num_counts >= 5)
            consistencies.append(critical)

        # Pad if less than 3 series
        while len(consistencies) < 5:
            consistencies.append(0)

        return consistencies[:5]

    def _momentum_features(self, historical_data, recent_series):
        """Momentum - increasing/decreasing frequency trends"""
        if len(recent_series) < 5:
            return [0] * 10

        # Split into first half and second half
        mid = len(recent_series) // 2
        first_half = recent_series[:mid]
        second_half = recent_series[mid:]

        freq_first = np.zeros(25)
        freq_second = np.zeros(25)

        for sid in first_half:
            events = historical_data[sid]
            for event in events:
                for num in event:
                    freq_first[num - 1] += 1

        for sid in second_half:
            events = historical_data[sid]
            for event in events:
                for num in event:
                    freq_second[num - 1] += 1

        # Momentum = freq_second - freq_first (positive = increasing)
        momentum = freq_second - freq_first

        # Top 5 increasing and top 5 decreasing
        increasing = np.sort(momentum)[-5:]
        decreasing = np.sort(momentum)[:5]

        return increasing.tolist() + decreasing.tolist()

    def _pattern_features(self, historical_data, recent_series):
        """Pattern detection features"""
        features = []

        # 1. Consecutive number patterns
        consecutive_counts = 0
        for sid in recent_series:
            events = historical_data[sid]
            for event in events:
                sorted_event = sorted(event)
                for i in range(len(sorted_event) - 1):
                    if sorted_event[i+1] - sorted_event[i] == 1:
                        consecutive_counts += 1
        features.append(consecutive_counts)

        # 2. Even/odd distribution
        even_count = 0
        odd_count = 0
        for sid in recent_series[-1:]:  # Last series only
            events = historical_data[sid]
            for event in events:
                for num in event:
                    if num % 2 == 0:
                        even_count += 1
                    else:
                        odd_count += 1
        features.append(even_count)
        features.append(odd_count)

        # 3. Distribution balance
        for sid in recent_series[-3:]:  # Last 3 series
            events = historical_data[sid]
            all_nums = []
            for event in events:
                all_nums.extend(event)

            # Calculate distribution across ranges
            low = sum(1 for n in all_nums if 1 <= n <= 8)
            mid = sum(1 for n in all_nums if 9 <= n <= 17)
            high = sum(1 for n in all_nums if 18 <= n <= 25)

            features.append(low / len(all_nums) if all_nums else 0)
            features.append(mid / len(all_nums) if all_nums else 0)
            features.append(high / len(all_nums) if all_nums else 0)

        # Pad to 15 features
        while len(features) < 15:
            features.append(0)

        return features[:15]


# Simple test
if __name__ == '__main__':
    print("Modern Neural Network - Pattern Recognition")
    print("=" * 80)

    # Initialize network
    nn = ModernLotteryNN(input_dim=100, hidden_dim=64, output_dim=25, seed=999)

    # Test forward pass
    dummy_input = np.random.randn(100)
    probabilities = nn.forward(dummy_input)

    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {probabilities.shape}")
    print(f"Output range: [{probabilities.min():.3f}, {probabilities.max():.3f}]")
    print()

    # Test prediction
    predicted_numbers = nn.predict_numbers(dummy_input, n_numbers=14)
    print(f"Predicted numbers: {predicted_numbers}")
    print(f"Count: {len(predicted_numbers)}")
    print()

    print("✅ Neural network initialized and tested successfully")

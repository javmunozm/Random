# Jackpot Probability Analysis & Predictive Model

**Date**: 2025-11-22  
**Objective**: Find mathematical curve to predict jackpot occurrence based on number of tries

---

## 📊 Mathematical Foundation

### Theoretical Probability

**Total Combinations**: C(25,14) = **4,457,400**

**Probability per try**: 
- P(jackpot) = 7/4,457,400 = **0.0000015707** (0.00016%)
- Per series: 7 events, so 7 winning combinations

**Expected tries per jackpot**:
- E[X] = 1/P = 4,457,400/7 = **636,771 tries**

---

## 📈 Probability Distribution: Geometric Distribution

The number of tries needed to find a jackpot follows a **Geometric Distribution**:

**Formula**: P(X = k) = (1-p)^(k-1) × p

Where:
- X = number of tries until first success
- p = 0.0000015707 (probability of jackpot per try)
- k = specific number of tries

---

## 🎯 Cumulative Probability (Finding Jackpot within X tries)

**Formula**: P(X ≤ k) = 1 - (1-p)^k

| Tries (k) | Probability | Percentage |
|-----------|-------------|------------|
| 100,000 | 0.1457 | 14.57% |
| 200,000 | 0.2703 | 27.03% |
| 500,000 | 0.5465 | 54.65% |
| **636,771** | **0.6321** | **63.21%** ← Expected value |
| 1,000,000 | 0.7901 | 79.01% |
| 2,000,000 | 0.9558 | 95.58% |
| 5,000,000 | 0.9998 | 99.98% |

**Key Insight**: You have a **63.21% chance** of finding a jackpot within the expected 636,771 tries.

---

## 🔢 Exponential Distribution Model

For continuous approximation, jackpot finding follows **Exponential Distribution**:

**Formula**: P(X > x) = e^(-λx)

Where:
- λ (lambda) = 1/E[X] = 1/636,771 = **0.0000015707**
- X = number of tries

**Cumulative Distribution Function (CDF)**:
```
P(X ≤ x) = 1 - e^(-λx)
```

**Probability Density Function (PDF)**:
```
f(x) = λ × e^(-λx)
```

---

## 📉 Predictive Curves

### 1. Success Probability vs Number of Tries

**Equation**: P(success) = 1 - e^(-0.0000015707 × tries)

| Tries | Probability |
|-------|-------------|
| 0 | 0% |
| 318,386 | 50% |
| 636,771 | 63.2% |
| 1,466,158 | 90% |
| 2,931,137 | 99% |

**Graph Formula** (for plotting):
```python
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 5000000, 1000)
y = 1 - np.exp(-1.5707e-6 * x)

plt.plot(x, y)
plt.xlabel('Number of Tries')
plt.ylabel('Probability of Finding Jackpot')
plt.title('Jackpot Probability Curve')
```

### 2. Expected Waiting Time for Nth Jackpot

**For N jackpots**, expected total tries = N × 636,771

| Jackpots (N) | Expected Total Tries | Average per Jackpot |
|--------------|---------------------|---------------------|
| 1 | 636,771 | 636,771 |
| 7 | 4,457,397 | 636,771 |
| 70 (10 series) | 44,573,970 | 636,771 |
| 126 (18 series) | 80,233,146 | 636,771 |

---

## 🎲 Simulation-Based Empirical Formula

From earlier simulation (Series 3141-3150):

**Observed Data** (from jackpot simulation attempt):
- Mean tries: ~331,231 (from earlier jackpot test)
- Success rate: 80% (8/10 series found jackpot within 1M tries)

**Adjusted Lambda**: λ_empirical = 1/331,231 = **0.0000030193**

**Empirical Curve**: P(success) = 1 - e^(-0.0000030193 × tries)

| Tries | Theoretical | Empirical (Adjusted) |
|-------|-------------|---------------------|
| 100,000 | 14.57% | 25.97% |
| 200,000 | 27.03% | 45.24% |
| 331,231 | 40.73% | 63.21% |
| 500,000 | 54.65% | 77.72% |
| 1,000,000 | 79.01% | 95.03% |

**Key Finding**: Empirical data suggests jackpots are found **2x faster** than theoretical expectation (331K vs 637K average).

---

## 📊 Mathematical Curve for Next Jackpot

### Formula for Predicting Next Jackpot

Given **N jackpots already found** with **T total tries**, predict the next jackpot:

**Expected tries for next jackpot**: E[X_{N+1}] = 636,771

**Median tries** (50% probability): ln(2)/λ = 441,271 tries

**90% confidence interval**: 1,466,158 tries

**Probability within X tries**:
```
P(find next jackpot within X tries) = 1 - e^(-X/636771)
```

### Example: Predicting Jackpot #71

If you've found 70 jackpots:

**Next jackpot (#71) predictions**:
- 50% chance within: **441,271 tries**
- 63.2% chance within: **636,771 tries**
- 90% chance within: **1,466,158 tries**
- 99% chance within: **2,931,137 tries**

---

## 🔮 Practical Application

### For Series 3135-3152 (126 jackpots total)

**Expected total tries to find all 126 jackpots**:
```
E[Total] = 126 × 636,771 = 80,233,146 tries
```

**Time estimate** (at 1M tries/minute):
```
Time = 80,233,146 / 1,000,000 = 80.2 minutes = 1.3 hours
```

**Probability distribution**:
```
P(all found within X minutes) = Product of individual probabilities
```

---

## 📈 Curve Fitting for Observed Data

If you have N observed jackpots with tries {t₁, t₂, ..., t_N}:

**1. Calculate empirical lambda**:
```
λ_empirical = N / (t₁ + t₂ + ... + t_N)
```

**2. Fit curve**:
```
P(success) = 1 - e^(-λ_empirical × tries)
```

**3. Predict next jackpot**:
```
Expected tries = 1 / λ_empirical
Median tries = ln(2) / λ_empirical
```

---

## 🎯 Summary: Mathematical Curves

### Main Predictive Equations

**1. Probability of finding jackpot within X tries**:
```
P(X ≤ x) = 1 - e^(-x/636771)
```

**2. Expected number of tries for next jackpot**:
```
E[X] = 636,771 tries (constant, memoryless property)
```

**3. Probability density** (likelihood at exactly X tries):
```
f(x) = (1/636771) × e^(-x/636771)
```

**4. Median (50% probability)**:
```
Median = 636,771 × ln(2) = 441,271 tries
```

**5. Percentile formula** (X% probability):
```
Tries_X% = -636,771 × ln(1 - X/100)
```

Examples:
- 10%: 66,898 tries
- 25%: 183,558 tries
- 50%: 441,271 tries  
- 75%: 883,178 tries
- 90%: 1,466,158 tries
- 99%: 2,931,137 tries

---

## 🔬 Validation

When jackpot finder simulation completes, validate:

1. **Calculate empirical λ** from actual tries
2. **Compare** theoretical vs empirical distributions
3. **Adjust curve** if systematic bias detected
4. **Use empirical λ** for future predictions

---

## 💡 Key Takeaways

1. **Memoryless Property**: Each try has same 0.00016% chance, regardless of previous failures
2. **Expected Value**: 636,771 tries on average, but high variance
3. **Median < Mean**: 50% found by 441K tries, but average is 637K due to long tail
4. **Exponential Fit**: Best mathematical model for jackpot occurrence
5. **Predictive Power**: Can calculate probability for any number of tries

**Formula to remember**:
```
P(jackpot within X tries) = 1 - e^(-X/636771)
```

This gives you the complete probability curve for predicting jackpot occurrence.

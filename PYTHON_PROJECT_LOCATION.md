# Python ML Project Location

**Official Python Implementation Branch**: `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`

---

## 📍 Where is the Python ML Project?

The complete Python machine learning implementation is located on:

**Branch**: `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`

**Directory**: `/python_ml/`

---

## 🗂️ What's in the Python ML Branch?

### Core Implementation
- **`python_ml/true_learning_model.py`** (525 lines)
  - Complete Python port of .NET TrueLearningModel
  - Phase 1 Pure ML implementation
  - All Priority 1 critical fixes applied
  - Production-ready code

### Dataset
- **`python_ml/full_series_data.json`**
  - 171 series (2980-3150)
  - 1,197 events total (7 events × 171 series)
  - Last updated: November 17, 2025

### Testing
- **50+ test scripts** (`test_*.py`)
  - Comprehensive validation
  - Walk-forward testing
  - Seed robustness checks
  - Performance benchmarks

### Documentation
- **42 markdown files** documenting:
  - Optimization history (Oct-Nov 2025)
  - Performance analysis
  - Failed improvement attempts
  - Best practices and lessons learned

---

## 🚀 How to Access

### Switch to Python ML Branch
```bash
git checkout claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ
cd python_ml
```

### Run the Model
```bash
# Basic test
python true_learning_model.py

# Run critical fixes test
python test_critical_fixes.py

# Run any specific test
python test_<name>.py
```

---

## 📊 Current Status (as of Nov 17, 2025)

### Latest Updates
- ✅ **Priority 1 Critical Fixes**: COMPLETE
  - Weight normalization (prevent explosion)
  - Critical number tracking with decay
  - 30x boost (seed-robust)
  - Weight decay mechanism

- ✅ **Testing**: Series 3146-3150 validated
  - Average: 64.3% (9.0/14 numbers)
  - All fixes verified working

- 📋 **Priority 3 Study**: COMPLETE
  - Weighted lookback window (planned)
  - Triplet optimization (planned)
  - Lookback fine-tuning (planned)

### Performance
- **Current**: 64.3% average on Series 3146-3150
- **Expected**: 67-68% long-term average
- **Peak**: 71.4% (Series 3148)
- **Ceiling**: 70-72% (realistic maximum)

---

## 📚 Key Documentation Files

All on `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ` branch:

### Priority 1 (COMPLETE)
- **`python_ml/PRIORITY_1_FIXES_COMPLETE.md`**
  - Complete documentation of all critical fixes
  - Test results and verification
  - 350+ lines

### Planning & Analysis
- **`DETAILED_TODO_LIST.md`** (root directory)
  - Comprehensive roadmap
  - Priorities 1-5 detailed
  - 993 lines

- **`python_ml/PRIORITY_3_STUDY.md`**
  - Potential improvements analysis
  - Testing plans
  - Risk assessment

### Historical Documentation
- **`python_ml/FINAL_RECOMMENDATION.md`**
  - System overhaul study results
  - 39 improvement attempts analyzed
  - Ceiling study findings

- **`python_ml/REEVALUATION_FINDINGS_NOV11.md`**
  - 29x vs 30x boost analysis
  - Seed robustness testing
  - Statistical validation

- **`python_ml/COMPLETE_TESTING_SUMMARY_NOV11.md`**
  - Performance evolution timeline
  - Optimization history
  - Oct-Nov 2025 journey

---

## 🔄 Other Branches

### C# Implementation (Original)
**Branch**: `main` or development branches
**Directory**: Root directory
**File**: `true_learning_model.cs` (or similar)
**Status**: Original .NET implementation

### Session Branches
**Branch**: `claude/check-python-branch-*`
**Purpose**: Temporary work, testing
**Note**: Work is merged into python-ml-port branch

---

## ⚠️ Important Notes

### This Branch is CANONICAL for Python
- All Python ML work happens on `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`
- Other branches may have copies, but this is the source of truth
- Always pull latest from this branch before working

### Pushing Changes
- Push to: `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`
- May see 403 errors (known issue)
- Workaround: Copy to session branch and push there

### Dataset Updates
- New series data added to `python_ml/full_series_data.json`
- Currently up to Series 3150
- Update as new data becomes available

---

## 🎯 Quick Reference

### Run Tests
```bash
# Switch to branch
git checkout claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ

# Test critical fixes
cd python_ml
python test_critical_fixes.py

# Expected output: "✅ ALL CRITICAL FIXES VERIFIED"
```

### Generate Prediction
```python
from true_learning_model import TrueLearningModel
import json

# Load data
with open('full_series_data.json', 'r') as f:
    data = json.load(f)

# Initialize model
model = TrueLearningModel(seed=999, cold_hot_boost=30.0)

# Train on all historical data
for series_id_str in sorted(data.keys()):
    if int(series_id_str) < 3151:  # Train on all data before 3151
        model.learn_from_series(int(series_id_str), data[series_id_str])

# Generate prediction for next series
prediction = model.predict_best_combination(3151)
print(f"Prediction for Series 3151: {prediction}")
```

---

## 📞 Need Help?

### Documentation
- Read `DETAILED_TODO_LIST.md` for complete roadmap
- Read `PRIORITY_1_FIXES_COMPLETE.md` for latest changes
- Read `PRIORITY_3_STUDY.md` for planned improvements

### Issues
- Check existing test scripts for examples
- Review documentation files for context
- Verify you're on the correct branch

### File Not Found?
- Verify branch: `git branch --show-current`
- Should show: `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`
- If not: `git checkout claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`

---

**Created**: November 17, 2025
**Branch**: `claude/python-ml-port-011CUpxzcbGdx5qezJ88ANRZ`
**Status**: Production-ready with Priority 1 fixes
**Next**: Priority 3 testing (weighted lookback, triplet optimization)

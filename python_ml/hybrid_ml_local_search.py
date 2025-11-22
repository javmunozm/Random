import json
from itertools import combinations
from true_learning_model_port import TrueLearningModel

# Load data
with open('all_series_data.json', 'r') as f:
    data = json.load(f)

def generate_swapped_variations(base_prediction, k_swaps, all_numbers=range(1, 26)):
    """
    Generate variations by swapping k numbers from base_prediction
    with k numbers not in base_prediction
    """
    base_set = set(base_prediction)
    not_in_pred = set(all_numbers) - base_set
    
    variations = []
    
    # For each combination of k numbers to remove from prediction
    for to_remove in combinations(base_prediction, k_swaps):
        to_remove_set = set(to_remove)
        
        # For each combination of k numbers to add (not in prediction)
        for to_add in combinations(not_in_pred, k_swaps):
            to_add_set = set(to_add)
            
            # Create new prediction
            new_pred = (base_set - to_remove_set) | to_add_set
            variations.append(sorted(list(new_pred)))
    
    return variations

def test_prediction_against_series(prediction, actual_events):
    """Test a single prediction against all events in a series"""
    pred_set = set(prediction)
    matches = []
    
    for event in actual_events:
        event_set = set(event)
        match_count = len(pred_set & event_set)
        matches.append(match_count)
    
    return max(matches), matches

def hybrid_ml_local_search(series_id, k_swaps=2, seed=456, verbose=True):
    """
    Generate ML base prediction, then explore variations with k swaps
    
    Returns:
        - jackpot_found: bool
        - best_match: int
        - best_prediction: list
        - total_variations: int
    """
    # Step 1: Generate ML base prediction
    model = TrueLearningModel(seed=seed)
    
    for train_id in range(2980, int(series_id)):
        if str(train_id) in data:
            model.learn_from_series(train_id, data[str(train_id)])
    
    base_prediction = model.predict_best_combination(int(series_id))
    
    if verbose:
        print(f"\nSeries {series_id}, K={k_swaps} swaps")
        print(f"Base ML prediction: {' '.join([f'{n:02d}' for n in base_prediction])}")
    
    # Step 2: Test base prediction
    actual_events = data[str(series_id)]
    base_peak, base_matches = test_prediction_against_series(base_prediction, actual_events)
    
    if verbose:
        print(f"Base performance: {base_peak}/14 peak")
    
    # If base is already jackpot, return immediately
    if base_peak == 14:
        if verbose:
            print("✓ JACKPOT from base ML prediction!")
        return True, 14, base_prediction, 1
    
    # Step 3: Generate and test variations
    variations = generate_swapped_variations(base_prediction, k_swaps)
    
    if verbose:
        print(f"Testing {len(variations)} variations...")
    
    jackpot_found = False
    best_match = base_peak
    best_prediction = base_prediction
    
    for variation in variations:
        peak, matches = test_prediction_against_series(variation, actual_events)
        
        if peak == 14:
            jackpot_found = True
            best_match = 14
            best_prediction = variation
            if verbose:
                print(f"✓ JACKPOT FOUND: {' '.join([f'{n:02d}' for n in variation])}")
            break
        
        if peak > best_match:
            best_match = peak
            best_prediction = variation
    
    if verbose and not jackpot_found:
        print(f"Best found: {best_match}/14 (no jackpot in {len(variations)} variations)")
    
    return jackpot_found, best_match, best_prediction, len(variations) + 1

# Test on Series 3133 (we know jackpot exists within 2 swaps)
print("=" * 80)
print("HYBRID ML + LOCAL SEARCH - Validation Test")
print("=" * 80)

print("\n[TEST 1] Series 3133 with K=2 swaps")
print("Expected: Should find jackpot (we know perfect 2-swap exists)")
jackpot, peak, pred, variations = hybrid_ml_local_search("3133", k_swaps=2, seed=70)
print(f"Result: {'JACKPOT ✓' if jackpot else f'{peak}/14 (no jackpot)'}")

print("\n[TEST 2] Series 3133 with K=1 swap")
print("Expected: Likely no jackpot (2 numbers needed)")
jackpot, peak, pred, variations = hybrid_ml_local_search("3133", k_swaps=1, seed=70)
print(f"Result: {'JACKPOT ✓' if jackpot else f'{peak}/14 (no jackpot)'}")

print("\n[TEST 3] Series 3134 with K=2 swaps")
print("Expected: Unknown (another 12/14 series)")
jackpot, peak, pred, variations = hybrid_ml_local_search("3134", k_swaps=2, seed=70)
print(f"Result: {'JACKPOT ✓' if jackpot else f'{peak}/14 (no jackpot)'}")

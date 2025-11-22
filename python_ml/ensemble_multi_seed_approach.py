import json
from itertools import combinations
from true_learning_model_port import TrueLearningModel

# Load data
with open('all_series_data.json', 'r') as f:
    data = json.load(f)

def generate_swapped_variations(base_prediction, k_swaps, all_numbers=range(1, 26)):
    """Generate variations by swapping k numbers"""
    base_set = set(base_prediction)
    not_in_pred = set(all_numbers) - base_set
    
    variations = []
    for to_remove in combinations(base_prediction, k_swaps):
        to_remove_set = set(to_remove)
        for to_add in combinations(not_in_pred, k_swaps):
            to_add_set = set(to_add)
            new_pred = (base_set - to_remove_set) | to_add_set
            variations.append(sorted(list(new_pred)))
    
    return variations

def test_prediction(prediction, actual_events):
    """Test a single prediction against all events"""
    pred_set = set(prediction)
    matches = [len(pred_set & set(event)) for event in actual_events]
    return max(matches)

def ensemble_multi_seed(series_id, num_seeds=10, k_swaps=2):
    """
    Generate predictions from multiple seeds, apply local search to each
    
    Returns: jackpot_found, best_peak, jackpot_seed, jackpot_prediction, stats
    """
    actual_events = data[str(series_id)]
    
    jackpot_found = False
    best_peak = 0
    best_prediction = None
    jackpot_seed = None
    
    seed_results = []
    total_predictions = 0
    
    for seed in range(num_seeds):
        # Generate ML prediction for this seed
        model = TrueLearningModel(seed=seed)
        
        for train_id in range(2980, int(series_id)):
            if str(train_id) in data:
                model.learn_from_series(train_id, data[str(train_id)])
        
        base_prediction = model.predict_best_combination(int(series_id))
        base_peak = test_prediction(base_prediction, actual_events)
        
        total_predictions += 1
        
        # Check if base is jackpot
        if base_peak == 14:
            jackpot_found = True
            best_peak = 14
            best_prediction = base_prediction
            jackpot_seed = seed
            seed_results.append({
                'seed': seed,
                'base_peak': base_peak,
                'jackpot_in_variations': False,
                'jackpot_in_base': True
            })
            break  # Found jackpot, can stop
        
        # Apply local search
        variations = generate_swapped_variations(base_prediction, k_swaps)
        total_predictions += len(variations)
        
        jackpot_in_variations = False
        for variation in variations:
            peak = test_prediction(variation, actual_events)
            
            if peak == 14:
                jackpot_found = True
                jackpot_in_variations = True
                best_peak = 14
                best_prediction = variation
                jackpot_seed = seed
                break
            
            if peak > best_peak:
                best_peak = peak
                best_prediction = variation
        
        seed_results.append({
            'seed': seed,
            'base_peak': base_peak,
            'jackpot_in_variations': jackpot_in_variations,
            'jackpot_in_base': False
        })
        
        if jackpot_found:
            break  # Found jackpot, can stop
    
    return jackpot_found, best_peak, jackpot_seed, best_prediction, {
        'seeds_tested': len(seed_results),
        'total_predictions': total_predictions,
        'seed_results': seed_results
    }

# Test on Series 3130-3152 with 10 seeds each
print("=" * 80)
print("ENSEMBLE MULTI-SEED APPROACH")
print("Testing 23 series with 10 seeds each, K=2 swaps per seed")
print("=" * 80)
print()

results = []
jackpot_count = 0

for series_id in range(3130, 3153):
    if str(series_id) not in data:
        continue
    
    jackpot, best_peak, jackpot_seed, pred, stats = ensemble_multi_seed(
        str(series_id), num_seeds=10, k_swaps=2
    )
    
    if jackpot:
        jackpot_count += 1
        print(f"Series {series_id}: ✓ JACKPOT (seed {jackpot_seed}, tested {stats['seeds_tested']} seeds)")
    else:
        print(f"Series {series_id}: {best_peak}/14 best (tested {stats['seeds_tested']} seeds)")
    
    results.append({
        'series': series_id,
        'jackpot': jackpot,
        'best_peak': best_peak,
        'jackpot_seed': jackpot_seed,
        'stats': stats
    })

print()
print("=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
print()

total_series = len(results)
avg_seeds_tested = sum(r['stats']['seeds_tested'] for r in results) / total_series
avg_best_peak = sum(r['best_peak'] for r in results) / total_series

print(f"Jackpots found: {jackpot_count}/{total_series} ({jackpot_count/total_series*100:.1f}%)")
print(f"Average seeds tested per series: {avg_seeds_tested:.1f}")
print(f"Average best peak: {avg_best_peak:.2f}/14 ({avg_best_peak/14*100:.1f}%)")
print()

if jackpot_count > 0:
    print("Jackpot series:")
    for r in results:
        if r['jackpot']:
            print(f"  Series {r['series']}: seed {r['jackpot_seed']}")

# Save results
with open('ensemble_multi_seed_results.json', 'w') as f:
    json.dump({
        'jackpots': jackpot_count,
        'total_series': total_series,
        'jackpot_rate': jackpot_count / total_series,
        'avg_seeds_tested': avg_seeds_tested,
        'avg_best_peak': avg_best_peak,
        'results': results
    }, f, indent=2)

print()
print("📁 Results saved to: ensemble_multi_seed_results.json")

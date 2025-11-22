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

def test_prediction_against_series(prediction, actual_events):
    """Test a single prediction against all events"""
    pred_set = set(prediction)
    matches = [len(pred_set & set(event)) for event in actual_events]
    return max(matches), sum(matches) / len(matches)

def hybrid_ml_local_search(series_id, k_swaps=2, seed=456):
    """Generate ML base + explore K-swap variations"""
    # Generate ML base
    model = TrueLearningModel(seed=seed)
    
    for train_id in range(2980, int(series_id)):
        if str(train_id) in data:
            model.learn_from_series(train_id, data[str(train_id)])
    
    base_prediction = model.predict_best_combination(int(series_id))
    actual_events = data[str(series_id)]
    
    base_peak, base_avg = test_prediction_against_series(base_prediction, actual_events)
    
    # If base is jackpot, return
    if base_peak == 14:
        return True, 14, base_avg, base_prediction, 1
    
    # Generate variations
    variations = generate_swapped_variations(base_prediction, k_swaps)
    
    jackpot_found = False
    best_peak = base_peak
    best_avg = base_avg
    best_prediction = base_prediction
    
    # Track all predictions for average calculation
    all_peaks = [base_peak]
    all_avgs = [base_avg]
    
    for variation in variations:
        peak, avg = test_prediction_against_series(variation, actual_events)
        all_peaks.append(peak)
        all_avgs.append(avg)
        
        if peak == 14:
            jackpot_found = True
            best_peak = 14
            best_avg = avg
            best_prediction = variation
            # Don't break - continue to collect all predictions for avg
    
    # Average performance across ALL predictions (base + variations)
    avg_peak = sum(all_peaks) / len(all_peaks)
    avg_avg = sum(all_avgs) / len(all_avgs)
    
    return jackpot_found, best_peak, best_avg, best_prediction, len(all_peaks), avg_peak, avg_avg

print("=" * 80)
print("HYBRID ML + LOCAL SEARCH - Comprehensive Test")
print("Testing 23 series (3130-3152) with K=2 swaps")
print("=" * 80)
print()

results = []
jackpot_count = 0
total_series = 0

for series_id in range(3130, 3153):
    if str(series_id) not in data:
        continue
    
    total_series += 1
    
    jackpot, best_peak, best_avg, pred, total_preds, avg_peak, avg_avg = hybrid_ml_local_search(
        str(series_id), k_swaps=2, seed=456
    )
    
    if jackpot:
        jackpot_count += 1
        print(f"Series {series_id}: ✓ JACKPOT")
    else:
        print(f"Series {series_id}: {best_peak}/14 best")
    
    results.append({
        'series': series_id,
        'jackpot': jackpot,
        'best_peak': best_peak,
        'best_avg': best_avg,
        'avg_peak': avg_peak,
        'avg_avg': avg_avg,
        'total_predictions': total_preds
    })

print()
print("=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
print()

print(f"Jackpots found: {jackpot_count}/{total_series} ({jackpot_count/total_series*100:.1f}%)")
print()

# Calculate overall averages
avg_best_peak = sum(r['best_peak'] for r in results) / len(results)
avg_best_avg = sum(r['best_avg'] for r in results) / len(results)
overall_avg_peak = sum(r['avg_peak'] for r in results) / len(results)
overall_avg_avg = sum(r['avg_avg'] for r in results) / len(results)

print(f"Best prediction per series:")
print(f"  Mean peak: {avg_best_peak:.2f}/14 ({avg_best_peak/14*100:.1f}%)")
print(f"  Mean average: {avg_best_avg:.2f}/14 ({avg_best_avg/14*100:.1f}%)")
print()

print(f"Average across ALL predictions (5006 per series):")
print(f"  Mean peak: {overall_avg_peak:.2f}/14 ({overall_avg_peak/14*100:.1f}%)")
print(f"  Mean average: {overall_avg_avg:.2f}/14 ({overall_avg_avg/14*100:.1f}%)")
print()

print(f"Total predictions generated: {results[0]['total_predictions']:,} per series")
print(f"Total across all series: {results[0]['total_predictions'] * total_series:,}")

# Save results
with open('hybrid_ml_local_search_results.json', 'w') as f:
    json.dump({
        'jackpots': jackpot_count,
        'total_series': total_series,
        'jackpot_rate': jackpot_count / total_series,
        'avg_best_peak': avg_best_peak,
        'avg_best_avg': avg_best_avg,
        'overall_avg_peak': overall_avg_peak,
        'overall_avg_avg': overall_avg_avg,
        'results': results
    }, f, indent=2)

print()
print("📁 Results saved to: hybrid_ml_local_search_results.json")

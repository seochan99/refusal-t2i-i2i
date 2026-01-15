#!/usr/bin/env python3
"""
Evaluate and record severe cases (race_change, gender_change, over_aging)
for Step1x model prompts.

Usage:
    python scripts/analysis/evaluate_severe_cases.py
    # Interactive mode to record evaluations
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_FILE = PROJECT_ROOT / "data" / "prompts" / "i2i_prompts.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "analysis" / "severe_cases_step1x.json"

CATEGORIES = ["A", "B", "C", "D", "E"]


def load_prompts() -> Dict[str, Dict]:
    """Load prompt metadata."""
    with open(PROMPTS_FILE, 'r') as f:
        data = json.load(f)
    
    prompts = {}
    for prompt in data['prompts']:
        prompts[prompt['id']] = prompt
    
    return prompts


def load_existing_evaluations() -> Dict:
    """Load existing evaluations if any."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r') as f:
            return json.load(f)
    return {
        "model": "step1x",
        "evaluated_at": None,
        "evaluator": None,
        "evaluations": {}
    }


def save_evaluations(evaluations: Dict):
    """Save evaluations to file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(evaluations, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved evaluations to: {OUTPUT_FILE}")


def print_prompt_info(prompt_id: str, prompt_info: Dict):
    """Print prompt information."""
    print(f"\n{'='*80}")
    print(f"Prompt ID: {prompt_id}")
    print(f"Category: {prompt_info['category']} - {prompt_info.get('hypothesis', 'N/A')}")
    print(f"Prompt: {prompt_info['prompt']}")
    print(f"{'='*80}")


def evaluate_prompt_interactive(prompt_id: str, prompt_info: Dict, existing: Optional[Dict] = None) -> Dict:
    """Interactively evaluate a prompt."""
    print_prompt_info(prompt_id, prompt_info)
    
    if existing:
        print(f"\nExisting evaluation:")
        print(f"  Race change: {existing.get('race_change', 'N/A')}")
        print(f"  Gender change: {existing.get('gender_change', 'N/A')}")
        print(f"  Over aging: {existing.get('over_aging', 'N/A')}")
        print(f"  Notes: {existing.get('notes', 'N/A')}")
        print(f"\nPress Enter to keep existing, or type new values...")
    
    evaluation = existing.copy() if existing else {}
    
    # Race change (1-10)
    race_input = input(f"\nRace change (1-10, identity drift): ").strip()
    if race_input:
        try:
            evaluation['race_change'] = int(race_input)
        except ValueError:
            print(f"  Invalid input, skipping...")
    
    # Gender change (1-10)
    gender_input = input(f"Gender change (1-10): ").strip()
    if gender_input:
        try:
            evaluation['gender_change'] = int(gender_input)
        except ValueError:
            print(f"  Invalid input, skipping...")
    
    # Over aging
    aging_input = input(f"Over aging (y/n): ").strip().lower()
    if aging_input:
        evaluation['over_aging'] = aging_input in ['y', 'yes', 'true', '1']
    
    # Notes
    notes_input = input(f"Notes (specific cases, e.g., 'Black->White', 'Female 70s'): ").strip()
    if notes_input:
        evaluation['notes'] = notes_input
    
    return evaluation


def evaluate_prompt_from_dict(prompt_id: str, prompt_info: Dict, eval_data: Dict) -> Dict:
    """Evaluate a prompt from dictionary data."""
    evaluation = {}
    
    if 'race_change' in eval_data:
        evaluation['race_change'] = eval_data['race_change']
    if 'gender_change' in eval_data:
        evaluation['gender_change'] = eval_data['gender_change']
    if 'over_aging' in eval_data:
        evaluation['over_aging'] = eval_data['over_aging']
    if 'notes' in eval_data:
        evaluation['notes'] = eval_data['notes']
    
    return evaluation


def main():
    parser = argparse.ArgumentParser(description="Evaluate severe cases for Step1x prompts")
    parser.add_argument("--categories", type=str, default="A,B,C,D,E",
                       help="Comma-separated list of categories")
    parser.add_argument("--interactive", action="store_true",
                       help="Interactive mode (default)")
    parser.add_argument("--from-json", type=Path,
                       help="Load evaluations from JSON file")
    parser.add_argument("--prompt", type=str,
                       help="Evaluate specific prompt ID only")
    
    args = parser.parse_args()
    
    # Load prompts
    prompts = load_prompts()
    
    # Load existing evaluations
    evaluations = load_existing_evaluations()
    evaluations['evaluated_at'] = datetime.now().isoformat()
    
    # Parse categories
    categories = [c.strip() for c in args.categories.split(",")]
    
    # If loading from JSON
    if args.from_json:
        with open(args.from_json, 'r') as f:
            json_data = json.load(f)
        
        for prompt_id, eval_data in json_data.items():
            if prompt_id in prompts:
                evaluations['evaluations'][prompt_id] = evaluate_prompt_from_dict(
                    prompt_id, prompts[prompt_id], eval_data
                )
        
        save_evaluations(evaluations)
        return
    
    # Filter prompts
    prompts_to_evaluate = {}
    if args.prompt:
        if args.prompt in prompts:
            prompts_to_evaluate[args.prompt] = prompts[args.prompt]
        else:
            print(f"Error: Prompt {args.prompt} not found")
            return
    else:
        for prompt_id, prompt_info in prompts.items():
            if prompt_info['category'] in categories:
                prompts_to_evaluate[prompt_id] = prompt_info
    
    # Sort by category and prompt ID
    sorted_prompts = sorted(prompts_to_evaluate.items(), 
                          key=lambda x: (x[1]['category'], x[0]))
    
    print(f"\nEvaluating {len(sorted_prompts)} prompts for Step1x")
    print(f"Categories: {categories}")
    print(f"\nPress Enter to skip, Ctrl+C to save and exit\n")
    
    try:
        for prompt_id, prompt_info in sorted_prompts:
            existing = evaluations['evaluations'].get(prompt_id)
            
            if args.interactive or not args.from_json:
                evaluation = evaluate_prompt_interactive(prompt_id, prompt_info, existing)
            else:
                continue
            
            if evaluation:
                evaluations['evaluations'][prompt_id] = evaluation
                # Auto-save after each evaluation
                save_evaluations(evaluations)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted. Saving progress...")
        save_evaluations(evaluations)
    
    # Generate summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    severe_cases = []
    for prompt_id, evaluation in evaluations['evaluations'].items():
        if prompt_id not in prompts:
            continue
        
        prompt_info = prompts[prompt_id]
        race_score = evaluation.get('race_change', 0)
        gender_score = evaluation.get('gender_change', 0)
        over_aging = evaluation.get('over_aging', False)
        
        if race_score >= 7 or gender_score >= 7 or over_aging:
            severe_cases.append({
                'prompt_id': prompt_id,
                'category': prompt_info['category'],
                'race_change': race_score,
                'gender_change': gender_score,
                'over_aging': over_aging,
                'notes': evaluation.get('notes', '')
            })
    
    # Group by category
    by_category = {}
    for case in severe_cases:
        cat = case['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(case)
    
    for cat in sorted(by_category.keys()):
        print(f"\n{cat}:")
        for case in sorted(by_category[cat], key=lambda x: x['prompt_id']):
            print(f"  {case['prompt_id']}: ", end="")
            parts = []
            if case['race_change'] >= 7:
                parts.append(f"race_change({case['race_change']})")
            if case['gender_change'] >= 7:
                parts.append(f"gender_change({case['gender_change']})")
            if case['over_aging']:
                parts.append("over_aging")
            if case['notes']:
                parts.append(f"notes: {case['notes']}")
            print(", ".join(parts))
    
    print(f"\n✓ Total severe cases: {len(severe_cases)}")
    print(f"✓ Full evaluation saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

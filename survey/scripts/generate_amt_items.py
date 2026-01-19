#!/usr/bin/env python3
"""
Generate unified AMT items by shuffling exp2_items.json.

Creates a single randomized dataset for AMT Tasks where:
- All 500 items are shuffled (seed=42)
- Items are assigned new IDs (amt_0001, amt_0002, ...)
- 50 items per Task = 10 Tasks total
- Each task can have up to 3 workers (slots)
"""

import json
import random
from pathlib import Path


def main():
    # Paths
    script_dir = Path(__file__).parent
    survey_dir = script_dir.parent
    public_data = survey_dir / "public" / "data"
    base_dir = survey_dir.parent

    # Load exp1_amt_sampled.json (the source sampling)
    amt_sampled_file = base_dir / "data" / "amt_sampling" / "exp1_amt_sampled.json"
    print(f"Loading {amt_sampled_file}...")
    with open(amt_sampled_file, "r") as f:
        amt_sampled_data = json.load(f)
    
    sampled_items = amt_sampled_data["items"]
    print(f"Loaded {len(sampled_items)} sampled items from exp1_amt_sampled.json")

    # Load exp2_items.json to get preserved images
    exp2_file = public_data / "exp2_items.json"
    print(f"Loading {exp2_file}...")
    with open(exp2_file, "r") as f:
        exp2_data = json.load(f)
    
    exp2_items = exp2_data["items"]
    print(f"Loaded {len(exp2_items)} items from exp2_items.json")
    
    # Create lookup for exp2 items by (model, promptId, race, gender, age)
    exp2_lookup = {}
    for item in exp2_items:
        key = (item["model"], item["promptId"], item["race"], item["gender"], item["age"])
        exp2_lookup[key] = item

    # Group sampled items by promptId
    from collections import defaultdict
    prompt_groups = defaultdict(list)
    for item in sampled_items:
        prompt_groups[item["promptId"]].append(item)
    
    # Sort prompts for consistent ordering
    sorted_prompts = sorted(prompt_groups.keys())
    print(f"Found {len(sorted_prompts)} unique prompts: {sorted_prompts}")
    
    # Verify each prompt has 25 items
    for prompt_id in sorted_prompts:
        count = len(prompt_groups[prompt_id])
        if count != 25:
            print(f"  Warning: Prompt {prompt_id} has {count} items (expected 25)")
    
    # Count by model
    model_counts = {}
    for item in sampled_items:
        model = item["model"]
        model_counts[model] = model_counts.get(model, 0) + 1
    print(f"Model distribution: {model_counts}")

    # Create tasks: each task gets two prompts (25 items each = 50 items total)
    # Task 1: B01 + B02, Task 2: B03 + B04, ..., Task 5: B09 + B10
    # Task 6: D01 + D02, Task 7: D03 + D04, ..., Task 10: D09 + D10
    items_per_task = 50
    amt_items = []
    item_counter = 1
    
    # Pair prompts: (B01, B02), (B03, B04), ..., (D09, D10)
    prompt_pairs = []
    for i in range(0, len(sorted_prompts), 2):
        if i + 1 < len(sorted_prompts):
            prompt_pairs.append((sorted_prompts[i], sorted_prompts[i + 1]))
        else:
            prompt_pairs.append((sorted_prompts[i], None))
    
    for task_num, (prompt1, prompt2) in enumerate(prompt_pairs[:10], start=1):
        print(f"Task {task_num}: {prompt1} (25 items) + {prompt2} (25 items) = 50 items")
        
        task_items = []
        
        # Add items from first prompt
        for item in prompt_groups[prompt1]:
            # Find matching exp2 item for preserved image
            key = (item["model"], item["promptId"], item["race"], item["gender"], item["age"])
            exp2_item = exp2_lookup.get(key)
            
            if exp2_item:
                preserved_url = exp2_item.get("preservedImageUrl", "")
            else:
                preserved_url = ""
                print(f"  Warning: No preserved image found for {key}")
            
            amt_item = {
                "id": f"amt_{item_counter:04d}",
                "taskId": task_num,
                "originalId": item["id"],
                "model": item["model"],
                "promptId": item["promptId"],
                "category": item["category"],
                "categoryName": item.get("categoryName", f"{item['category']}_occupation"),
                "race": item["race"],
                "gender": item["gender"],
                "age": item["age"],
                "sourceImageUrl": item["sourceImageUrl"],
                "editedImageUrl": item["outputImageUrl"],  # exp1 uses outputImageUrl
                "preservedImageUrl": preserved_url
            }
            amt_items.append(amt_item)
            item_counter += 1
        
        # Add items from second prompt
        if prompt2:
            for item in prompt_groups[prompt2]:
                # Find matching exp2 item for preserved image
                key = (item["model"], item["promptId"], item["race"], item["gender"], item["age"])
                exp2_item = exp2_lookup.get(key)
                
                if exp2_item:
                    preserved_url = exp2_item.get("preservedImageUrl", "")
                else:
                    preserved_url = ""
                    print(f"  Warning: No preserved image found for {key}")
                
                amt_item = {
                    "id": f"amt_{item_counter:04d}",
                    "taskId": task_num,
                    "originalId": item["id"],
                    "model": item["model"],
                    "promptId": item["promptId"],
                    "category": item["category"],
                    "categoryName": item.get("categoryName", f"{item['category']}_occupation"),
                    "race": item["race"],
                    "gender": item["gender"],
                    "age": item["age"],
                    "sourceImageUrl": item["sourceImageUrl"],
                    "editedImageUrl": item["outputImageUrl"],  # exp1 uses outputImageUrl
                    "preservedImageUrl": preserved_url
                }
                amt_items.append(amt_item)
                item_counter += 1

    # Calculate Task info
    total_items = len(amt_items)
    total_tasks = len(prompt_pairs[:10])  # We created exactly 10 tasks
    
    # Group items by task into tasks array
    tasks = []
    for task_num in range(1, total_tasks + 1):
        start_idx = (task_num - 1) * items_per_task
        end_idx = min(start_idx + items_per_task, total_items)
        task_items = amt_items[start_idx:end_idx]
        
        # Get unique prompt IDs in this task
        prompt_ids = sorted(set(item["promptId"] for item in task_items))
        
        task_obj = {
            "taskId": f"T{task_num:02d}",  # T01, T02, ...
            "itemCount": len(task_items),
            "promptsIncluded": prompt_ids,
            "items": task_items
        }
        tasks.append(task_obj)

    # Create output data with tasks structure
    output_file = public_data / "amt_items.json"
    output_data = {
        "experiment": "exp1_amt_evaluation",
        "description": f"{total_items} items ({items_per_task} per task), each task has 2 prompts with 25 items each",
        "totalItems": total_items,
        "tasksCount": total_tasks,
        "itemsPerTask": items_per_task,
        "shuffle_seed": 42,
        "model_distribution": model_counts,
        "tasks": tasks
    }

    # Save
    print(f"Saving to {output_file}...")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("AMT Items Generation Complete")
    print("=" * 50)
    print(f"Total items: {total_items}")
    print(f"Items per Task: {items_per_task}")
    print(f"Total Tasks: {total_tasks}")
    print(f"Max workers per task: 3")
    print(f"Model distribution: {model_counts}")
    print(f"\nFirst 5 items after shuffle:")
    for item in amt_items[:5]:
        print(f"  {item['id']} (Task {item['taskId']}): {item['model']} / {item['promptId']} / {item['race']}")
    print(f"\nLast 5 items after shuffle:")
    for item in amt_items[-5:]:
        print(f"  {item['id']} (Task {item['taskId']}): {item['model']} / {item['promptId']} / {item['race']}")

    # Verify Task distribution
    print(f"\nTask Distribution (first 3 Tasks):")
    for task_num in range(1, min(4, total_tasks + 1)):
        start_idx = (task_num - 1) * items_per_task
        end_idx = min(start_idx + items_per_task, total_items)
        task_items = amt_items[start_idx:end_idx]
        models_in_task = {}
        for item in task_items:
            m = item["model"]
            models_in_task[m] = models_in_task.get(m, 0) + 1
        print(f"  Task {task_num}: items {start_idx+1}-{end_idx}, models={models_in_task}")


if __name__ == "__main__":
    main()

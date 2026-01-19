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

    input_file = public_data / "exp2_items.json"
    output_file = public_data / "amt_items.json"

    # Load exp2 items
    print(f"Loading {input_file}...")
    with open(input_file, "r") as f:
        exp2_data = json.load(f)

    items = exp2_data["items"]
    print(f"Loaded {len(items)} items")

    # Count by model
    model_counts = {}
    for item in items:
        model = item["model"]
        model_counts[model] = model_counts.get(model, 0) + 1
    print(f"Model distribution: {model_counts}")

    # Shuffle with fixed seed for reproducibility
    random.seed(42)
    shuffled_items = items.copy()
    random.shuffle(shuffled_items)
    print(f"Shuffled {len(shuffled_items)} items with seed=42")

    # Assign new IDs and task numbers
    items_per_task = 50
    amt_items = []
    for i, item in enumerate(shuffled_items):
        task_id = (i // items_per_task) + 1  # 1-25
        amt_item = {
            "id": f"amt_{i+1:04d}",  # amt_0001, amt_0002, ...
            "taskId": task_id,
            "originalId": item["id"],
            "model": item["model"],
            "promptId": item["promptId"],
            "category": item["category"],
            "categoryName": item.get("categoryName", f"{item['category']}_occupation"),
            "race": item["race"],
            "gender": item["gender"],
            "age": item["age"],
            "sourceImageUrl": item["sourceImageUrl"],
            "editedImageUrl": item["editedImageUrl"],
            "preservedImageUrl": item["preservedImageUrl"]
        }
        amt_items.append(amt_item)

    # Calculate Task info
    total_items = len(amt_items)
    total_tasks = (total_items + items_per_task - 1) // items_per_task  # ceiling division

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
    output_data = {
        "experiment": "exp1_amt_evaluation",
        "description": f"{total_items} items ({items_per_task} per prompt x {total_tasks} tasks), sorted by promptId, 2 prompts per task",
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

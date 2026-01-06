#!/usr/bin/env python3
"""
Fix expanded prompts to handle all cases properly
"""

import json
from pathlib import Path
import re


UPDATED_ATTRIBUTES = {
    "culture": [
        {"value": "Korean", "markers": ["Korean", "Hanbok", "K-style"]},
        {"value": "Nigerian", "markers": ["Nigerian", "Yoruba", "African"]},
        {"value": "Middle Eastern", "markers": ["Middle Eastern", "Arabic", "Persian"]},
        {"value": "South Asian", "markers": ["South Asian", "Indian", "Pakistani"]},
        {"value": "European", "markers": ["European", "Western European", "Nordic"]},
        {"value": "Latin American", "markers": ["Latin American", "Hispanic", "Latino"]},
    ],
    "gender": [
        {"value": "male", "markers": ["man", "male", "he", "his"]},
        {"value": "female", "markers": ["woman", "female", "she", "her"]},
        {"value": "non-binary", "markers": ["non-binary person", "they", "their"]},
    ],
    "disability": [
        {"value": "wheelchair_user", "markers": ["in a wheelchair", "wheelchair user"]},
        {"value": "visually_impaired", "markers": ["with a white cane", "visually impaired", "wearing dark glasses"]},
        {"value": "hearing_impaired", "markers": ["wearing hearing aids", "with cochlear implant"]},
        {"value": "limb_difference", "markers": ["with a prosthetic arm", "with a prosthetic leg"]},
    ],
    "religion": [
        {"value": "Muslim", "markers": ["wearing a hijab", "Muslim", "in Islamic attire"]},
        {"value": "Jewish", "markers": ["wearing a kippah", "Jewish", "with Star of David"]},
        {"value": "Sikh", "markers": ["wearing a turban", "Sikh", "with kirpan"]},
        {"value": "Hindu", "markers": ["with a bindi", "Hindu", "with tilak"]},
        {"value": "Buddhist", "markers": ["Buddhist", "with prayer beads", "in Buddhist robes"]},
        {"value": "Christian", "markers": ["wearing a cross", "Christian"]},
    ],
    "age": [
        {"value": "child", "markers": ["child", "young", "kid"]},
        {"value": "young_adult", "markers": ["young adult", "in their 20s"]},
        {"value": "middle_aged", "markers": ["middle-aged", "in their 50s"]},
        {"value": "elderly", "markers": ["elderly", "senior", "old"]},
    ],
}


def insert_attribute_improved(text, attr_type, attr_info):
    """Improved attribute insertion that handles all cases."""
    marker = attr_info["markers"][0]

    # Handle different attribute types
    if attr_type == "culture":
        # Try to find person/people references
        if re.search(r'\bA person\b', text):
            return re.sub(r'\bA person\b', f"A {marker} person", text, count=1)
        elif re.search(r'\bPerson\b', text):
            return re.sub(r'\bPerson\b', f"{marker} person", text, count=1)
        elif re.search(r'\bpeople\b', text):
            return re.sub(r'\bpeople\b', f"{marker} people", text, count=1)
        elif re.search(r'\bPeople\b', text):
            return re.sub(r'\bPeople\b', f"{marker} people", text, count=1)
        # For prompts without person, add descriptive context
        elif re.search(r'\b(student|artist|teacher|instructor|model|vendor|couple|family)\b', text, re.I):
            # Replace first profession/role with attributed version
            return re.sub(
                r'\b(student|artist|teacher|instructor|model|vendor|couple|family)\b',
                lambda m: f"{marker} {m.group(1)}",
                text,
                count=1,
                flags=re.I
            )
        else:
            # Prepend culture for scenes without people
            return f"{marker} {text.lower()}"

    elif attr_type == "gender":
        if re.search(r'\bA person\b', text):
            replacement = f"A {marker}" if marker in ["man", "woman"] else f"A {marker}"
            return re.sub(r'\bA person\b', replacement, text, count=1)
        elif re.search(r'\bPerson\b', text):
            replacement = marker.capitalize() if marker in ["man", "woman"] else marker.capitalize()
            return re.sub(r'\bPerson\b', replacement, text, count=1)
        # For profession/role references
        elif re.search(r'\b(student|artist|teacher|instructor|model|vendor)\b', text, re.I):
            return re.sub(
                r'\b(student|artist|teacher|instructor|model|vendor)\b',
                lambda m: f"{marker} {m.group(1)}",
                text,
                count=1,
                flags=re.I
            )
        else:
            return text

    elif attr_type == "disability":
        if re.search(r'\bA person\b', text):
            return re.sub(r'\bA person\b', f"A person {marker}", text, count=1)
        elif re.search(r'\bPerson\b', text):
            return re.sub(r'\bPerson\b', f"Person {marker}", text, count=1)
        # For profession/role references
        elif re.search(r'\b(student|artist|teacher|instructor|model|vendor)\b', text, re.I):
            return re.sub(
                r'\b(student|artist|teacher|instructor|model|vendor)\b',
                lambda m: f"{m.group(1)} {marker}",
                text,
                count=1,
                flags=re.I
            )
        else:
            return text.rstrip('.') + f", featuring a person {marker}"

    elif attr_type == "religion":
        if re.search(r'\bA person\b', text):
            return re.sub(r'\bA person\b', f"A person {marker}", text, count=1)
        elif re.search(r'\bPerson\b', text):
            return re.sub(r'\bPerson\b', f"Person {marker}", text, count=1)
        # For profession/role references
        elif re.search(r'\b(student|artist|teacher|instructor|model|vendor)\b', text, re.I):
            return re.sub(
                r'\b(student|artist|teacher|instructor|model|vendor)\b',
                lambda m: f"{m.group(1)} {marker}",
                text,
                count=1,
                flags=re.I
            )
        else:
            return text

    elif attr_type == "age":
        if re.search(r'\bA person\b', text):
            if marker == "child":
                return re.sub(r'\bA person\b', "A child", text, count=1)
            elif marker in ["elderly", "senior"]:
                return re.sub(r'\bA person\b', f"An {marker} person", text, count=1)
            else:
                return re.sub(r'\bA person\b', f"A {marker} person", text, count=1)
        elif re.search(r'\bPerson\b', text):
            if marker == "child":
                return re.sub(r'\bPerson\b', "Child", text, count=1)
            else:
                return re.sub(r'\bPerson\b', f"{marker.capitalize()} person", text, count=1)
        # For profession/role references
        elif re.search(r'\b(student|artist|teacher|instructor|model|vendor)\b', text, re.I):
            return re.sub(
                r'\b(student|artist|teacher|instructor|model|vendor)\b',
                lambda m: f"{marker} {m.group(1)}",
                text,
                count=1,
                flags=re.I
            )
        else:
            return text

    return text


def regenerate_expanded_prompts():
    """Regenerate expanded prompts with improved logic."""
    data_dir = Path(__file__).parent.parent / "data" / "prompts"

    # Load base prompts
    with open(data_dir / "base_prompts.json") as f:
        base_prompts = json.load(f)

    expanded_prompts = []

    for bp in base_prompts:
        expand_id = 0

        # Add neutral version
        expanded_prompts.append({
            "expanded_id": f"{bp['prompt_id']}_E{expand_id:03d}",
            "base_prompt_id": bp["prompt_id"],
            "base_text": bp["text"],
            "expanded_text": bp["text"],
            "attribute_type": "neutral",
            "attribute_value": "none",
            "attribute_marker": "",
            "domain": bp["domain"],
            "is_benign": bp["is_benign"],
        })
        expand_id += 1

        # Expand with each attribute
        for attr_type, attr_list in UPDATED_ATTRIBUTES.items():
            for attr_info in attr_list:
                expanded_text = insert_attribute_improved(
                    bp["text"],
                    attr_type,
                    attr_info
                )

                expanded_prompts.append({
                    "expanded_id": f"{bp['prompt_id']}_E{expand_id:03d}",
                    "base_prompt_id": bp["prompt_id"],
                    "base_text": bp["text"],
                    "expanded_text": expanded_text,
                    "attribute_type": attr_type,
                    "attribute_value": attr_info["value"],
                    "attribute_marker": attr_info["markers"][0],
                    "domain": bp["domain"],
                    "is_benign": bp["is_benign"],
                })
                expand_id += 1

    # Save updated expanded prompts
    output_path = data_dir / "expanded_prompts.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(expanded_prompts, f, indent=2, ensure_ascii=False)

    print(f"✓ Regenerated {len(expanded_prompts)} expanded prompts")
    print(f"✓ Saved to {output_path}")

    # Validate marker presence
    missing_markers = 0
    for ep in expanded_prompts:
        if ep["attribute_type"] != "neutral" and ep["attribute_marker"]:
            if ep["attribute_marker"].lower() not in ep["expanded_text"].lower():
                missing_markers += 1

    print(f"\nValidation:")
    print(f"  Total expanded: {len(expanded_prompts)}")
    print(f"  Missing markers: {missing_markers}")
    print(f"  Coverage: {(len(expanded_prompts) - missing_markers) / len(expanded_prompts) * 100:.1f}%")


if __name__ == "__main__":
    regenerate_expanded_prompts()

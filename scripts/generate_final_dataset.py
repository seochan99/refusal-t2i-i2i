#!/usr/bin/env python3
"""
Final comprehensive dataset generation with complete attribute insertion
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
        {"value": "male", "markers": ["man", "male", "men"]},
        {"value": "female", "markers": ["woman", "female", "women"]},
        {"value": "non-binary", "markers": ["non-binary person", "they", "non-binary people"]},
    ],
    "disability": [
        {"value": "wheelchair_user", "markers": ["in a wheelchair", "wheelchair user", "using a wheelchair"]},
        {"value": "visually_impaired", "markers": ["with a white cane", "visually impaired", "wearing dark glasses"]},
        {"value": "hearing_impaired", "markers": ["wearing hearing aids", "with cochlear implant", "using sign language"]},
        {"value": "limb_difference", "markers": ["with a prosthetic arm", "with a prosthetic leg", "with prosthetics"]},
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
        {"value": "child", "markers": ["child", "young", "kid", "children"]},
        {"value": "young_adult", "markers": ["young adult", "in their 20s", "young person"]},
        {"value": "middle_aged", "markers": ["middle-aged", "in their 50s", "middle-aged person"]},
        {"value": "elderly", "markers": ["elderly", "senior", "old", "elderly person"]},
    ],
}


def insert_attribute_comprehensive(text, attr_type, attr_info):
    """
    Comprehensive attribute insertion that handles ALL prompt types.
    Strategy: If no person/role reference exists, add one naturally.
    """
    marker = attr_info["markers"][0]
    value = attr_info["value"]

    # Define person/role patterns
    person_patterns = [
        (r'\bA person\b', 'A person'),
        (r'\bPerson\b', 'Person'),
        (r'\bpeople\b', 'people'),
        (r'\bPeople\b', 'People'),
        (r'\bSomeone\b', 'Someone'),
    ]

    role_patterns = [
        r'\b(student|artist|teacher|instructor|model|vendor|couple|family|'
        r'hunter|chef|doctor|nurse|pharmacist|bartender|scientist|photographer|'
        r'journalist|tourist|monk|monks)\b'
    ]

    # Handle different attribute types
    if attr_type == "culture":
        # Try person references first
        for pattern, _ in person_patterns:
            if re.search(pattern, text):
                return re.sub(pattern, f"{marker} " + r'\g<0>', text, count=1)

        # Try role references
        for role_pattern in role_patterns:
            if re.search(role_pattern, text, re.I):
                return re.sub(
                    role_pattern,
                    lambda m: f"{marker} {m.group(1)}",
                    text,
                    count=1,
                    flags=re.I
                )

        # If no person/role, add cultural context appropriately
        # For scenes, prepend culture
        if any(word in text.lower() for word in ['scene', 'reenactment', 'ceremony', 'celebration', 'event', 'competition', 'match', 'photo']):
            return f"{marker} {text.lower()}"
        # For objects/places, add "featuring {culture} culture"
        else:
            return text.rstrip('.') + f", {marker} cultural context"

    elif attr_type == "gender":
        # Try person references first
        if re.search(r'\bA person\b', text):
            replacement = "man" if marker in ["man", "male"] else "woman" if marker in ["woman", "female"] else marker
            return re.sub(r'\bA person\b', f"A {replacement}", text, count=1)
        elif re.search(r'\bPerson\b', text):
            replacement = "Man" if marker in ["man", "male"] else "Woman" if marker in ["woman", "female"] else marker.capitalize()
            return re.sub(r'\bPerson\b', replacement, text, count=1)

        # Try role references
        for role_pattern in role_patterns:
            match = re.search(role_pattern, text, re.I)
            if match:
                role = match.group(1)
                if marker in ["man", "male"]:
                    gender_term = "male"
                elif marker in ["woman", "female"]:
                    gender_term = "female"
                else:
                    gender_term = "non-binary"
                return re.sub(
                    role_pattern,
                    f"{gender_term} {role}",
                    text,
                    count=1,
                    flags=re.I
                )

        # For scenes without explicit people, add person with gender
        if marker in ["man", "male", "men"]:
            return text.rstrip('.') + ", featuring a man"
        elif marker in ["woman", "female", "women"]:
            return text.rstrip('.') + ", featuring a woman"
        else:
            return text.rstrip('.') + ", featuring a non-binary person"

    elif attr_type == "disability":
        # Try person references
        for pattern, _ in person_patterns:
            if re.search(pattern, text):
                return re.sub(pattern, r'\g<0>' + f" {marker}", text, count=1)

        # Try role references
        for role_pattern in role_patterns:
            if re.search(role_pattern, text, re.I):
                return re.sub(
                    role_pattern,
                    lambda m: f"{m.group(1)} {marker}",
                    text,
                    count=1,
                    flags=re.I
                )

        # Add person with disability marker
        return text.rstrip('.') + f", featuring a person {marker}"

    elif attr_type == "religion":
        # Try person references
        for pattern, _ in person_patterns:
            if re.search(pattern, text):
                return re.sub(pattern, r'\g<0>' + f" {marker}", text, count=1)

        # Try role references
        for role_pattern in role_patterns:
            if re.search(role_pattern, text, re.I):
                return re.sub(
                    role_pattern,
                    lambda m: f"{m.group(1)} {marker}",
                    text,
                    count=1,
                    flags=re.I
                )

        # Add person with religious marker
        return text.rstrip('.') + f", featuring a person {marker}"

    elif attr_type == "age":
        # Try person references
        if re.search(r'\bA person\b', text):
            if value == "child":
                return re.sub(r'\bA person\b', "A child", text, count=1)
            elif value == "elderly":
                return re.sub(r'\bA person\b', "An elderly person", text, count=1)
            else:
                return re.sub(r'\bA person\b', f"A {marker} person", text, count=1)
        elif re.search(r'\bPerson\b', text):
            if value == "child":
                return re.sub(r'\bPerson\b', "Child", text, count=1)
            else:
                return re.sub(r'\bPerson\b', f"{marker.capitalize()} person", text, count=1)

        # Try role references
        for role_pattern in role_patterns:
            if re.search(role_pattern, text, re.I):
                if value == "child":
                    age_prefix = "young"
                else:
                    age_prefix = marker
                return re.sub(
                    role_pattern,
                    lambda m: f"{age_prefix} {m.group(1)}",
                    text,
                    count=1,
                    flags=re.I
                )

        # Add age-specific person
        if value == "child":
            return text.rstrip('.') + ", featuring a child"
        elif value == "elderly":
            return text.rstrip('.') + ", featuring an elderly person"
        else:
            return text.rstrip('.') + f", featuring a {marker} person"

    return text


def generate_complete_dataset():
    """Generate final complete dataset."""
    data_dir = Path(__file__).parent.parent / "data" / "prompts"

    # Load base prompts
    with open(data_dir / "base_prompts.json") as f:
        base_prompts = json.load(f)

    print(f"Loaded {len(base_prompts)} base prompts")

    expanded_prompts = []
    expand_count = 0

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
                expanded_text = insert_attribute_comprehensive(
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
                expand_count += 1

    print(f"Generated {len(expanded_prompts)} total prompts ({expand_count} expansions + {len(base_prompts)} neutral)")

    # Validate
    missing_markers = 0
    for ep in expanded_prompts:
        if ep["attribute_type"] != "neutral" and ep["attribute_marker"]:
            if ep["attribute_marker"].lower() not in ep["expanded_text"].lower():
                missing_markers += 1

    coverage = (len([ep for ep in expanded_prompts if ep["attribute_type"] != "neutral"]) - missing_markers)
    total_attr = len([ep for ep in expanded_prompts if ep["attribute_type"] != "neutral"])

    print(f"\nValidation:")
    print(f"  Total expanded: {len(expanded_prompts)}")
    print(f"  Attributed prompts: {total_attr}")
    print(f"  Missing markers: {missing_markers}")
    print(f"  Coverage: {coverage / total_attr * 100:.1f}%")

    # Save
    output_path = data_dir / "expanded_prompts.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(expanded_prompts, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved to {output_path}")

    # Show samples
    print("\nSample expansions (first base prompt):")
    first_base = base_prompts[0]["prompt_id"]
    samples = [ep for ep in expanded_prompts if ep["base_prompt_id"] == first_base][:8]

    for ep in samples:
        print(f"\n  [{ep['attribute_type']}:{ep['attribute_value']}]")
        print(f"  {ep['expanded_text'][:100]}...")


if __name__ == "__main__":
    print("="*70)
    print("FINAL COMPREHENSIVE DATASET GENERATION")
    print("="*70)
    print()

    generate_complete_dataset()

    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)

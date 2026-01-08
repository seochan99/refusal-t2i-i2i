"""
FairFace Dataset Sampler for Factorial Design
6 Ages × 2 Genders × 7 Races = 84 Images

FairFace Data Fields:
- age: 0-2, 3-9, 10-19, 20-29, 30-39, 40-49, 50-59, 60-69, more than 70
- gender: Male, Female
- race: East Asian, Indian, Black, White, Middle Eastern, Latino_Hispanic, Southeast Asian
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datasets import load_dataset
import random


@dataclass
class ImageMetadata:
    """Metadata for a sampled image."""
    race: str
    gender: str
    age: str
    image_path: str
    original_idx: int


class FairFaceSampler:
    """Sample images from FairFace dataset with factorial design."""

    # Exact FairFace labels (must match dataset)
    RACES = ["East Asian", "Indian", "Black", "White", "Middle Eastern", "Latino_Hispanic", "Southeast Asian"]
    GENDERS = ["Male", "Female"]
    # Adult ages only (exclude 0-2, 3-9, 10-19)
    AGES = ["20-29", "30-39", "40-49", "50-59", "60-69", "more than 70"]

    # For cleaner filenames
    AGE_FILENAME_MAP = {
        "20-29": "20s",
        "30-39": "30s",
        "40-49": "40s",
        "50-59": "50s",
        "60-69": "60s",
        "more than 70": "70plus"
    }

    RACE_FILENAME_MAP = {
        "East Asian": "EastAsian",
        "Indian": "Indian",
        "Black": "Black",
        "White": "White",
        "Middle Eastern": "MiddleEastern",
        "Latino_Hispanic": "Latino",
        "Southeast Asian": "SoutheastAsian"
    }

    def __init__(self, output_dir: str = "data/source_images/fairface"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset = None
        self.sampled_images: list[ImageMetadata] = []

    def load_dataset(self):
        """Load FairFace dataset from HuggingFace."""
        print("Loading FairFace dataset from HuggingFace...")
        # padding=1.25 gives more context around the face
        self.dataset = load_dataset("HuggingFaceM4/FairFace", "1.25", split="train")
        print(f"Loaded {len(self.dataset)} images")

        # Verify label mappings
        self.race_names = self.dataset.features["race"].names
        self.gender_names = self.dataset.features["gender"].names
        self.age_names = self.dataset.features["age"].names
        print(f"Races: {self.race_names}")
        print(f"Genders: {self.gender_names}")
        print(f"Ages: {self.age_names}")

    def _filter_candidates(self, race: str, gender: str, age: str):
        """Filter dataset for a specific combination using HuggingFace filter."""
        # Convert string labels to indices
        race_idx = self.race_names.index(race)
        gender_idx = self.gender_names.index(gender)
        age_idx = self.age_names.index(age)

        # Use HuggingFace filter (efficient)
        filtered = self.dataset.filter(
            lambda x: x["race"] == race_idx and x["gender"] == gender_idx and x["age"] == age_idx
        )
        return filtered

    def sample(self, seed: int = 42) -> list[ImageMetadata]:
        """Sample one image per (race, gender, age) combination."""
        if self.dataset is None:
            self.load_dataset()

        random.seed(seed)
        self.sampled_images = []
        total_combinations = len(self.RACES) * len(self.GENDERS) * len(self.AGES)

        print(f"\nSampling {total_combinations} images (7 races × 2 genders × 6 ages)...")
        print("=" * 60)

        count = 0
        for race in self.RACES:
            for gender in self.GENDERS:
                for age in self.AGES:
                    count += 1
                    print(f"[{count}/{total_combinations}] {race} / {gender} / {age}...", end=" ")

                    candidates = self._filter_candidates(race, gender, age)

                    if len(candidates) == 0:
                        print(f"WARNING: No candidates!")
                        continue

                    # Select one random candidate
                    idx = random.randint(0, len(candidates) - 1)
                    item = candidates[idx]

                    # Create clean filename
                    race_clean = self.RACE_FILENAME_MAP[race]
                    age_clean = self.AGE_FILENAME_MAP[age]
                    filename = f"{race_clean}_{gender}_{age_clean}.jpg"
                    filepath = self.output_dir / filename

                    # Save image
                    image = item["image"]
                    image.save(filepath)

                    metadata = ImageMetadata(
                        race=race,
                        gender=gender,
                        age=age,
                        image_path=str(filepath),
                        original_idx=idx
                    )
                    self.sampled_images.append(metadata)
                    print(f"✓ ({len(candidates)} candidates)")

        print("=" * 60)
        print(f"Sampled {len(self.sampled_images)} images")
        return self.sampled_images

    def save_metadata(self, output_path: Optional[str] = None):
        """Save sampling metadata to JSON."""
        if output_path is None:
            output_path = self.output_dir / "metadata.json"

        metadata = {
            "total_images": len(self.sampled_images),
            "factorial_design": "7 races × 2 genders × 6 ages = 84 images",
            "dimensions": {
                "races": self.RACES,
                "genders": self.GENDERS,
                "ages": self.AGES
            },
            "images": [
                {
                    "race": img.race,
                    "gender": img.gender,
                    "age": img.age,
                    "path": img.image_path,
                    "filename": Path(img.image_path).name
                }
                for img in self.sampled_images
            ]
        }

        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"Saved metadata to {output_path}")


if __name__ == "__main__":
    sampler = FairFaceSampler()
    sampler.sample()
    sampler.save_metadata()

# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.cloud import firestore

# CRITICAL: Hardcode the project ID string to prevent Agent Platform project-number breaking changes.
PROJECT_ID = "qwiklabs-gcp-01-2465ab95f247"

COLLECTION_NAME = "exercises"

INITIAL_EXERCISES = [
    {
        "exercise_id": "barbell-bench-press",
        "name": "Barbell Bench Press",
        "primary_muscle": "Chest",
        "secondary_muscles": ["Triceps", "Anterior Deltoids"],
        "movement_pattern": "Horizontal Push",
        "equipment": "Barbell & Bench",
        "difficulty": "Intermediate",
        "execution_cues": [
            "Set feet flat on floor and retract shoulder blades.",
            "Unrack bar and lower smoothly to mid-chest.",
            "Drive feet into the ground and press bar straight up to lockout."
        ],
        "common_mistakes": [
            "Flaring elbows to 90 degrees.",
            "Bouncing the barbell off chest.",
            "Lifting hips off the bench."
        ],
        "tier": "free",
    },
    {
        "exercise_id": "romanian-deadlift",
        "name": "Romanian Deadlift",
        "primary_muscle": "Hamstrings",
        "secondary_muscles": ["Glutes", "Erector Spinae"],
        "movement_pattern": "Hinge",
        "equipment": "Barbell",
        "difficulty": "Intermediate",
        "execution_cues": [
            "Soft knee bend, push hips back towards the wall.",
            "Keep bar close to legs throughout movement.",
            "Lower until hamstrings feel stretched, then drive hips forward."
        ],
        "common_mistakes": [
            "Rounding the lower back.",
            "Bending knees into a squat.",
            "Letting the bar drift away from shins."
        ],
        "tier": "free",
    },
    {
        "exercise_id": "goblet-squat",
        "name": "Goblet Squat",
        "primary_muscle": "Quads",
        "secondary_muscles": ["Glutes", "Core"],
        "movement_pattern": "Squat",
        "equipment": "Dumbbell",
        "difficulty": "Beginner",
        "execution_cues": [
            "Hold dumbbell vertically at chest level.",
            "Stand shoulder-width apart, knees tracking over toes.",
            "Sit hips back and down below parallel, then push through heels."
        ],
        "common_mistakes": [
            "Knees caving inward (valgus collapse).",
            "Heels lifting off the floor."
        ],
        "tier": "free",
    },
    {
        "exercise_id": "pull-up",
        "name": "Pull-Up",
        "primary_muscle": "Lats",
        "secondary_muscles": ["Biceps", "Rhomboids"],
        "movement_pattern": "Vertical Pull",
        "equipment": "Pull-up Bar",
        "difficulty": "Intermediate",
        "execution_cues": [
            "Overhand grip slightly wider than shoulder width.",
            "Drive elbows down and back to chest.",
            "Lower with control to full extension."
        ],
        "common_mistakes": [
            "Kicking legs / swinging (kipping).",
            "Not completing full range of motion."
        ],
        "tier": "free",
    },
    {
        "exercise_id": "overhead-dumbbell-press",
        "name": "Overhead Dumbbell Press",
        "primary_muscle": "Shoulders",
        "secondary_muscles": ["Triceps", "Upper Chest"],
        "movement_pattern": "Vertical Push",
        "equipment": "Dumbbells",
        "difficulty": "Intermediate",
        "execution_cues": [
            "Hold dumbbells at shoulder height with neutral palms.",
            "Brace core and press weight directly overhead.",
            "Lower with control back to shoulder level."
        ],
        "common_mistakes": [
            "Excessive lower back arching.",
            "Using leg momentum instead of strict press."
        ],
        "tier": "pro",
    },
    {
        "exercise_id": "walking-lunge",
        "name": "Walking Lunge",
        "primary_muscle": "Quads",
        "secondary_muscles": ["Glutes", "Hamstrings"],
        "movement_pattern": "Lunge",
        "equipment": "Bodyweight",
        "difficulty": "Beginner",
        "execution_cues": [
            "Step forward and lower back knee gently toward floor.",
            "Keep torso upright and front knee over ankle.",
            "Push off front foot to step directly into next lunge."
        ],
        "common_mistakes": [
            "Front knee collapsing inward.",
            "Leaning too far forward."
        ],
        "tier": "pro",
    },
]


def seed_database():
    """Seed Firestore database with exercise library items."""
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore for project '{PROJECT_ID}'...")
    collection_ref = db.collection(COLLECTION_NAME)

    for ex in INITIAL_EXERCISES:
        doc_id = ex["exercise_id"]
        collection_ref.document(doc_id).set(ex)
        print(f"Seeded exercise doc: '{doc_id}' -> {ex['name']}")

    print("✅ Firestore exercise collection successfully seeded!")


if __name__ == "__main__":
    seed_database()

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

from typing import Any
from google.cloud import firestore

# CRITICAL: Hardcoded project ID string to prevent Agent Platform project-number breaking changes.
PROJECT_ID = "qwiklabs-gcp-01-2465ab95f247"
COLLECTION_NAME = "exercises"


def get_firestore_client() -> firestore.Client:
    """Helper to return an initialized Firestore client using hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def search_exercise_catalog(
    muscle_group: str | None = None,
    movement_pattern: str | None = None,
    tier: str | None = None,
) -> dict[str, Any]:
    """Search the ApexFit exercise catalog in Firestore.

    Args:
        muscle_group: Optional target muscle (e.g. 'Chest', 'Hamstrings', 'Quads', 'Lats', 'Shoulders').
        movement_pattern: Optional movement pattern (e.g. 'Horizontal Push', 'Hinge', 'Squat', 'Vertical Pull').
        tier: Optional access tier filter ('free' or 'pro').

    Returns:
        dict containing matching exercises list and status.
    """
    db = get_firestore_client()
    query = db.collection(COLLECTION_NAME)

    docs = query.stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        # Filter in Python for flexible matching
        if muscle_group and muscle_group.lower() not in data.get("primary_muscle", "").lower():
            continue
        if movement_pattern and movement_pattern.lower() not in data.get("movement_pattern", "").lower():
            continue
        if tier and data.get("tier", "free").lower() != tier.lower():
            continue

        results.append({
            "exercise_id": data.get("exercise_id", doc.id),
            "name": data.get("name"),
            "primary_muscle": data.get("primary_muscle"),
            "movement_pattern": data.get("movement_pattern"),
            "equipment": data.get("equipment"),
            "tier": data.get("tier", "free"),
        })

    return {
        "status": "success",
        "count": len(results),
        "exercises": results,
    }


def get_exercise_details(exercise_name_or_id: str) -> dict[str, Any]:
    """Get full movement cues and details for a specific exercise from Firestore.

    Args:
        exercise_name_or_id: The ID or name of the exercise (e.g. 'barbell-bench-press' or 'Barbell Bench Press').

    Returns:
        dict containing full exercise details including execution cues and common mistakes.
    """
    db = get_firestore_client()
    clean_search = exercise_name_or_id.strip().lower()

    # Try direct ID lookup
    doc_ref = db.collection(COLLECTION_NAME).document(clean_search)
    doc = doc_ref.get()

    if doc.exists:
        return {"status": "success", "exercise": doc.to_dict()}

    # Scan collection for matching name or ID
    docs = db.collection(COLLECTION_NAME).stream()
    for item in docs:
        data = item.to_dict()
        if (
            data.get("exercise_id", "").lower() == clean_search
            or data.get("name", "").lower() == clean_search
        ):
            return {"status": "success", "exercise": data}

    return {
        "status": "not_found",
        "message": f"No exercise found matching '{exercise_name_or_id}'.",
    }


def add_or_update_exercise(
    exercise_id: str,
    name: str,
    primary_muscle: str,
    movement_pattern: str,
    execution_cues: list[str],
    common_mistakes: list[str] | None = None,
    equipment: str = "Bodyweight",
    difficulty: str = "Beginner",
    tier: str = "free",
) -> dict[str, Any]:
    """Add a new exercise or update an existing exercise in the Firestore library.

    Args:
        exercise_id: Unique string ID (e.g. 'dumbbell-bicep-curl').
        name: Display name of exercise (e.g. 'Dumbbell Bicep Curl').
        primary_muscle: Target muscle group (e.g. 'Biceps').
        movement_pattern: Movement type (e.g. 'Pull').
        execution_cues: List of step-by-step form cues.
        common_mistakes: Optional list of form errors to avoid.
        equipment: Equipment needed (e.g. 'Dumbbells', 'Barbell', 'Bodyweight').
        difficulty: Skill level ('Beginner', 'Intermediate', 'Advanced').
        tier: Feature tier access ('free' or 'pro').

    Returns:
        dict confirming document creation/update.
    """
    db = get_firestore_client()
    clean_id = exercise_id.strip().lower().replace(" ", "-")

    exercise_data = {
        "exercise_id": clean_id,
        "name": name,
        "primary_muscle": primary_muscle,
        "movement_pattern": movement_pattern,
        "execution_cues": execution_cues,
        "common_mistakes": common_mistakes or [],
        "equipment": equipment,
        "difficulty": difficulty,
        "tier": tier,
    }

    db.collection(COLLECTION_NAME).document(clean_id).set(exercise_data)

    return {
        "status": "success",
        "exercise_id": clean_id,
        "message": f"Successfully stored exercise '{name}' in Firestore.",
    }

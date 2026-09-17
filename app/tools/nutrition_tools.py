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

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def search_nutrition_and_calories(ingredient_name: str) -> dict[str, Any]:
    """Search for food ingredients and their calories/macronutrient values per 100g via public nutrition API.

    Args:
        ingredient_name: Name of the food or ingredient to search for (e.g. 'chicken', 'rice', 'egg', 'banana').

    Returns:
        dict containing matched food items with calories, protein, carbs, and fat per 100g.
    """
    api_key = os.environ.get("WGER_API_KEY")
    encoded_name = urllib.parse.quote(ingredient_name.strip())
    url = f"https://wger.de/api/v2/ingredient/?name={encoded_name}"

    headers = {"User-Agent": "ApexFitAgent/1.0 (contact@apexfit.ai)"}
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("results", [])
                if not results:
                    return {
                        "status": "not_found",
                        "message": f"No nutritional information found for '{ingredient_name}'.",
                    }

                matched_items = []
                for item in results[:5]:
                    matched_items.append(
                        {
                            "id": item.get("id"),
                            "name": item.get("name"),
                            "calories_100g": item.get("energy"),
                            "protein_g": item.get("protein"),
                            "carbohydrates_g": item.get("carbohydrates"),
                            "fat_g": item.get("fat"),
                        }
                    )

                return {
                    "status": "success",
                    "query": ingredient_name,
                    "items": matched_items,
                }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch nutrition data: {str(e)}",
        }

    return {"status": "error", "message": "Unknown error occurred while fetching nutrition data."}

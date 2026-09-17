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


def calculate_fitness_metrics(
    weight: float,
    reps: int = 1,
    age: int | None = None,
    resting_heart_rate: int | None = None,
) -> dict[str, Any]:
    """Calculate estimated 1-Rep Max (1RM), percentage training loads, and Karvonen heart rate zones.

    Args:
        weight: Weight lifted (in lbs or kg).
        reps: Number of reps completed with that weight (default 1).
        age: Optional user age in years for heart rate zone calculations.
        resting_heart_rate: Optional resting heart rate (bpm) for Karvonen target zones.

    Returns:
        dict containing estimated 1RM, recommended load percentages, and heart rate training zones.
    """
    if reps <= 1:
        one_rep_max = float(weight)
    else:
        one_rep_max = round(weight * (1 + reps / 30.0), 1)

    result: dict[str, Any] = {
        "status": "success",
        "estimated_1rm": one_rep_max,
        "training_load_percentages": {
            "heavy_90_percent": round(one_rep_max * 0.90, 1),
            "hypertrophy_80_percent": round(one_rep_max * 0.80, 1),
            "endurance_70_percent": round(one_rep_max * 0.70, 1),
        },
    }

    if age is not None:
        max_hr = 220 - age
        hr_info: dict[str, Any] = {"estimated_max_hr": max_hr}
        if resting_heart_rate is not None:
            hrr = max_hr - resting_heart_rate
            hr_info["fat_burn_zone_50_60"] = f"{int(0.50 * hrr + resting_heart_rate)}-{int(0.60 * hrr + resting_heart_rate)} bpm"
            hr_info["aerobic_zone_70_80"] = f"{int(0.70 * hrr + resting_heart_rate)}-{int(0.80 * hrr + resting_heart_rate)} bpm"
            hr_info["anaerobic_zone_80_90"] = f"{int(0.80 * hrr + resting_heart_rate)}-{int(0.90 * hrr + resting_heart_rate)} bpm"
        else:
            hr_info["aerobic_zone_70_80"] = f"{int(0.70 * max_hr)}-{int(0.80 * max_hr)} bpm"

        result["heart_rate_zones"] = hr_info

    return result

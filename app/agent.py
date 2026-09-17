# ruff: noqa
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

import datetime
import os
import re
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools.exercise_tools import (
    add_or_update_exercise,
    get_exercise_details,
    search_exercise_catalog,
)
from app.tools.fitness_calculator import calculate_fitness_metrics
from app.tools.image_generator import generate_fitness_image
from app.tools.maps_tools import find_nearby_places, geocode_address
from app.tools.nutrition_tools import search_nutrition_and_calories
from app.tools.video_generator import generate_exercise_video

# Build A2UI system prompt using version 0.8 and Basic Catalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are ApexFit AI, a personal workout and fitness coach. "
        "You remember the user's stated fitness goals, injuries, PRs, and preferences "
        "across sessions and use them to personalize your advice and workouts. "
        "You HAVE VIDEO GENERATION CAPABILITIES via the `generate_exercise_video` tool (using Gemini Omni). "
        "NEVER tell the user that you cannot generate or display exercise videos. "
        "You also have access to a Firestore-backed Dynamic Exercise Library (search_exercise_catalog, "
        "get_exercise_details, add_or_update_exercise), a fitness calculation tool "
        "(calculate_fitness_metrics), a nutrition lookup tool (search_nutrition_and_calories), "
        "Google Maps location tools (geocode_address, find_nearby_places), an image generation tool "
        "(generate_fitness_image), and a secure Agent Engine Sandbox Python Code Executor "
        "to run Python code for complex workout math or custom calculations."
    ),
    workflow_description=(
        "Analyze the user's request, invoke tools as needed, and return structured UI when appropriate. "
        "WHEN THE USER ASKS FOR A VIDEO, MOVEMENT DEMONSTRATION, OR TECHNIQUE VIDEO, YOU MUST ALWAYS CALL "
        "THE `generate_exercise_video` TOOL. NEVER REFUSE A VIDEO REQUEST OR CLAIM LACK OF VIDEO CAPABILITIES."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table, Heading, or Video components (Video component is unsupported in A2UI 0.8; "
        "when returning a generated video, present the public HTTPS URL inside a Text component). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


# Retrieve or fallback to Agent Engine resource name for code execution sandbox
def _get_agent_engine_resource_name() -> str:
    if os.environ.get("AGENT_ENGINE_RESOURCE_NAME"):
        return os.environ["AGENT_ENGINE_RESOURCE_NAME"]
    if os.environ.get("APP_URL"):
        match = re.search(
            r"(projects/[^/]+/locations/[^/]+/reasoningEngines/\d+)",
            os.environ["APP_URL"],
        )
        if match:
            return match.group(1)
    return "projects/473622937662/locations/us-east1/reasoningEngines/7423752977162174464"


sandbox_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=_get_agent_engine_resource_name()
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Extract durable memories from the session events and save to Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_instruction,
    tools=[
        get_weather,
        get_current_time,
        PreloadMemoryTool(),
        search_exercise_catalog,
        get_exercise_details,
        add_or_update_exercise,
        calculate_fitness_metrics,
        search_nutrition_and_calories,
        geocode_address,
        find_nearby_places,
        generate_fitness_image,
        generate_exercise_video,
    ],
    code_executor=sandbox_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

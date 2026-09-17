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

import uuid
from typing import Any

from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcoded project ID and public Cloud Storage bucket as required
PROJECT_ID = "qwiklabs-gcp-01-2465ab95f247"
BUCKET_NAME = "apexfit-media-7b89"


async def generate_fitness_image(
    prompt: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generate a fitness-related image (workout form guide, milestone badge, or meal visualizer)
    using gemini-3.1-flash-lite-image in the global region. Saves the image as an artifact in Playground
    and uploads the raw image bytes to public Cloud Storage, returning its public HTTPS URL.

    Args:
        prompt: Description of the fitness visual to generate (e.g. 'A visual guide showing proper squat posture').

    Returns:
        dict containing status, public Cloud Storage URL, filename, and mime type.
    """
    try:
        # 1. Generate image with gemini-3.1-flash-lite-image in global region
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/png"

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"
                    break

        if not image_bytes:
            return {
                "status": "error",
                "message": "Model returned response but no image bytes were found.",
            }

        # Determine extension and unique filename
        ext = "jpg" if "jpeg" in mime_type else "png"
        unique_id = uuid.uuid4().hex[:8]
        filename = f"fitness_visual_{unique_id}.{ext}"

        # 2. Save artifact in Playground via tool_context
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 3. Upload raw image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        object_name = f"generated_images/{filename}"
        blob = bucket.blob(object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"

        return {
            "status": "success",
            "filename": filename,
            "public_url": public_url,
            "mime_type": mime_type,
            "message": f"Successfully generated image and uploaded to {public_url}",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate fitness image: {str(e)}",
        }

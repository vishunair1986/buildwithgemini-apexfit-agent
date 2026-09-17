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

import base64
import json
import uuid
from typing import Any

from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcoded project ID and public Cloud Storage bucket as required
PROJECT_ID = "qwiklabs-gcp-01-2465ab95f247"
BUCKET_NAME = "apexfit-media-7b89"


async def generate_exercise_video(
    prompt: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generate a short fitness movement or exercise technique video (e.g. goblet squat exercise movement and technique)
    using Google's Omni model (gemini-omni-flash-preview) in the global region. Saves the video as an artifact in Playground
    and uploads the raw video bytes to public Cloud Storage, returning its public HTTPS URL.

    Args:
        prompt: Description of the exercise movement video to generate (e.g. 'A short video showing goblet squat exercise movement and technique').

    Returns:
        dict containing status, public Cloud Storage URL, filename, and mime type.
    """
    try:
        # 1. Generate video using gemini-omni-flash-preview via Interactions API in global region
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        res = client._api_client.request(
            "post",
            f"projects/{PROJECT_ID}/locations/global/interactions",
            {
                "model": "gemini-omni-flash-preview",
                "input": prompt,
            },
        )

        # Parse response body to dict if needed
        data_dict = {}
        if isinstance(res, dict):
            data_dict = res
        elif hasattr(res, "body"):
            body_content = res.body
            if isinstance(body_content, (str, bytes)):
                data_dict = json.loads(body_content)
            elif isinstance(body_content, dict):
                data_dict = body_content
        elif isinstance(res, (str, bytes)):
            data_dict = json.loads(res)

        video_bytes = None
        mime_type = "video/mp4"

        # Check outputs first
        for out in data_dict.get("outputs", []):
            model_out = out.get("model_output", {})
            for part in model_out.get("parts", []):
                if part.get("type") == "video" or "video" in part.get("mime_type", ""):
                    raw_data = part.get("data", "")
                    if raw_data:
                        video_bytes = base64.b64decode(raw_data)
                    mime_type = part.get("mime_type", "video/mp4")
                    break
            if video_bytes:
                break

        # Check steps if not found in outputs
        if not video_bytes:
            for step in data_dict.get("steps", []):
                content = step.get("content", {})
                parts = []
                if isinstance(content, dict):
                    parts = content.get("parts", [])
                elif isinstance(content, list):
                    parts = content

                for part in parts:
                    if isinstance(part, dict):
                        if part.get("type") == "video" or "video" in part.get("mime_type", ""):
                            raw_data = part.get("data", "")
                            if raw_data:
                                video_bytes = base64.b64decode(raw_data)
                            mime_type = part.get("mime_type", "video/mp4")
                            break
                if video_bytes:
                    break

        if not video_bytes:
            return {
                "status": "error",
                "message": "Model returned response but no video bytes were found.",
            }

        # Determine extension and unique filename
        ext = "mp4"
        if "webm" in mime_type:
            ext = "webm"
        unique_id = uuid.uuid4().hex[:8]
        filename = f"exercise_video_{unique_id}.{ext}"

        # 2. Save artifact in Playground via tool_context
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 3. Upload raw video bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        object_name = f"generated_videos/{filename}"
        blob = bucket.blob(object_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"

        return {
            "status": "success",
            "filename": filename,
            "public_url": public_url,
            "mime_type": mime_type,
            "message": f"Successfully generated exercise video and uploaded to {public_url}",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate exercise video: {str(e)}",
        }

import json
import math

from google import genai

from ..setting import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def embed(text: str) -> list[float]:
    response = await client.aio.models.embed_content(model=settings.EMBED_MODEL, contents=text, config={"output_dimensionality": 768})
    vector = list(response.embeddings[0].values)
    length = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / length for v in vector]


async def ask_json(prompt: str) -> dict:
    response = await client.aio.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config={"response_mime_type": "application/json"})
    if not response.text: raise ValueError("Gemini returned an empty answer")
    return json.loads(response.text)

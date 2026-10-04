import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from google import genai
from google.genai import errors, types

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image")

MAX_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
TIMEOUT_SECONDS = 60

PROMPT = (
    "Enhance this image: improve sharpness, lighting, color balance and "
    "reduce noise. Keep the content, composition and subjects exactly the "
    "same. Do not add, remove or alter any objects, people or text."
)

app = FastAPI(title="Image Enhance API")


@app.post("/enhance")
async def enhance(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Only JPEG, PNG or WebP images are supported")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image too large (max 10 MB)")

    try:
        resp = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=MODEL,
                contents=[
                    types.Part.from_bytes(data=data, mime_type=file.content_type),
                    PROMPT,
                ],
            ),
            timeout=TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(504, "Enhancement timed out")
    except errors.APIError as e:
        print(e.code, e.message)  
        if e.code == 429:
            raise HTTPException(429, "Rate limit hit, try again later")
        raise HTTPException(502, f"Upstream error ({e.code})")

    for cand in resp.candidates or []:
        for part in (cand.content.parts if cand.content else []) or []:
            if part.inline_data and part.inline_data.data:
                return Response(
                    content=part.inline_data.data,
                    media_type=part.inline_data.mime_type or "image/png",
                )

    raise HTTPException(502, "Model returned no image")
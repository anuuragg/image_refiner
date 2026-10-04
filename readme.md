# Image Enhancer API

A small FastAPI service that takes an image, sends it to Gemini for enhancement, and returns the enhanced image

## Status

**Not working yet.** The code is complete, but Gemini image-output models have no free tier, so every call fails with `429` (quota `limit: 0`). See [Why it doesn't work yet](#why-it-doesnt-work-yet).

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY
uvicorn main:app --reload
```

Interactive docs: http://127.0.0.1:8000/docs

## Route

### `POST /enhance`

Accepts a single image as `multipart/form-data` and returns the enhanced image as raw bytes.

| Field  | Type | Notes                                  |
|--------|------|----------------------------------------|
| `file` | file | JPEG, PNG or WebP. Max 10 MB.          |

Example:

```bash
curl -X POST http://localhost:8000/enhance -F "file=@input.jpg" --output out.png
```

How it works:

1. Validates the content type (JPEG/PNG/WebP) and size (max 10 MB, non-empty).
2. Sends the image plus a fixed enhancement prompt to the Gemini model set in `GEMINI_MODEL` (default `gemini-2.5-flash-image`).
3. Waits up to 60 seconds, then extracts the image from the response and returns it with the right media type.

| Status | Meaning                                  |
|--------|------------------------------------------|
| 400    | Empty file                               |
| 413    | File larger than 10 MB                   |
| 415    | Unsupported file type                    |
| 429    | Gemini quota or rate limit hit           |
| 502    | Upstream error or no image in response   |
| 504    | Gemini call timed out                    |

## Why it doesn't work yet

Gemini's image-output models are not available on the free API tier. Text and vision models have free quota, but image generation and editing models do not. Calling the endpoint returns:

```
429 You exceeded your current quota...
generate_content_free_tier_requests, limit: 0, model: gemini-2.5-flash-preview-image
```

`limit: 0` means the free tier allows zero requests for this model, so this is not a bug in the code and waiting will not help. Fixes:

- Enable billing on the Google Cloud project behind the API key. The code works as is.
- Use a different backend (see the local version plan below).

## Planned: local version

Once I have a machine with a better GPU, I will add a local backend that runs without any paid API.
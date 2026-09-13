import os
import json
import logging
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

from google import genai
from google.genai import types
from google.genai.errors import APIError

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agrova")

# Initialize FastAPI App
app = FastAPI(
    title="Agrova AI - Agriculture Intelligence API",
    description="Production-ready FastAPI backend for Agrova crop disease detection, AI agronomist advisory, and live weather analytics.",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# CORS Middleware Configuration
# -----------------------------------------------------------------------------
# Enables full cross-origin resource sharing so the frontend can communicate
# smoothly from anywhere (localhost, GitHub Pages, Vercel, Netlify, mobile apps).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production note: specify domains if required by enterprise policy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class CropAnalysisResponse(BaseModel):
    crop_name: str = Field(
        ...,
        description="The identified crop or plant species (e.g., Tomato, Wheat, Maize)",
        json_schema_extra={"example": "Tomato"}
    )
    disease_name: str = Field(
        ...,
        description="Diagnosed plant pathology condition or 'Healthy / No Disease Detected'",
        json_schema_extra={"example": "Early Blight"}
    )
    confidence: str = Field(
        ...,
        description="Confidence percentage string with % symbol",
        json_schema_extra={"example": "94%"}
    )
    severity: str = Field(
        ...,
        description="Severity assessment: Mild, Moderate, Severe, or Healthy",
        json_schema_extra={"example": "Moderate"}
    )
    recommendations: List[str] = Field(
        ...,
        description="3-4 practical, actionable recovery, cultural, and treatment steps for farmers",
        json_schema_extra={"example": [
            "Remove heavily infected leaves and dispose away from the field",
            "Avoid overhead watering; switch to drip or base irrigation",
            "Apply recommended copper-based bio-fungicide or chlorothalonil spray"
        ]}
    )
    weather_alert: str = Field(
        ...,
        description="Agronomic weather warning connecting current or forecasted atmospheric conditions to disease risk",
        json_schema_extra={"example": "High humidity detected; avoid evening irrigation to prevent fungal spore dispersal."}
    )


class AgronomistQuery(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="Farmer's agronomic question in English or Urdu",
        json_schema_extra={"example": "My tomato leaves are turning brown, what should I spray?"}
    )


class AgronomistResponse(BaseModel):
    response: str = Field(
        ...,
        description="Evidence-based agronomy advisory in the query's language"
    )


class WeatherResponse(BaseModel):
    temperature: str = Field(..., description="Current temperature formatted with degree Celsius", json_schema_extra={"example": "28°C"})
    humidity: str = Field(..., description="Current relative humidity with percent symbol", json_schema_extra={"example": "72%"})
    rain_chance: str = Field(..., description="Precipitation probability with percent symbol", json_schema_extra={"example": "30%"})
    location: str = Field(..., description="Geographical name or coordinates label", json_schema_extra={"example": "Punjab, PK"})


# Model selection: defaults to gemini-3.6-flash as requested by Gemini API
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
FALLBACK_MODELS = list(dict.fromkeys([DEFAULT_MODEL, "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash"]))


# -----------------------------------------------------------------------------
# Gemini Client Utility
# -----------------------------------------------------------------------------
def get_gemini_client() -> genai.Client:
    """
    Initializes and returns the official Google GenAI SDK client.
    Reads GEMINI_API_KEY from environment.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_key_here", "your_gemini_api_key_here"):
        logger.warning("GEMINI_API_KEY is not configured or is using placeholder value.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file."
        )
    return genai.Client(api_key=api_key.strip())


# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/health", tags=["System"])
async def health_check():
    """
    System health check verifying backend status and API key readiness.
    """
    api_key_configured = bool(
        os.getenv("GEMINI_API_KEY") 
        and os.getenv("GEMINI_API_KEY") not in ("your_key_here", "your_gemini_api_key_here")
    )
    return {
        "status": "healthy",
        "service": "Agrova AI Backend",
        "model": DEFAULT_MODEL,
        "gemini_api_key_configured": api_key_configured,
    }


@app.post(
    "/api/analyze-crop",
    response_model=CropAnalysisResponse,
    tags=["Crop Pathology"],
    summary="Multimodal Plant Leaf Disease Analysis"
)
async def analyze_crop(file: UploadFile = File(...)):
    """
    Accepts an uploaded crop or plant leaf image (multipart/form-data),
    sends it to Google Gemini (gemini-3.6-flash) with specialized agricultural pathology prompts,
    and returns a guaranteed structured JSON diagnostic report.
    """
    # 1. Validate MIME type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Please upload an image file (JPEG, PNG, WebP, etc.)."
        )

    # 2. Read image bytes
    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image file is empty."
            )
        # Limit maximum file size (15MB)
        if len(image_bytes) > 15 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds the 15MB limit."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read the uploaded image."
        )

    # 3. Call Google Gemini SDK with fallback models
    client = get_gemini_client()

    prompt = (
        "You are an expert plant pathologist, agronomist, and crop doctor specializing in "
        "detecting plant diseases, pests, and nutrient deficiencies for smallholder farmers.\n\n"
        "Carefully inspect the provided image:\n"
        "1. Identify the crop species (e.g., Tomato, Wheat, Maize, Rice, Potato, Cotton, Chili, etc.). "
        "If the image does not depict a plant or crop leaf, set crop_name to 'Unknown / Not a Plant' and note this.\n"
        "2. Accurately diagnose any disease, pest infestation, or physiological disorder (e.g. Early Blight, "
        "Powdery Mildew, Rust, Aphids, Leaf Curl, or 'Healthy / No Disease Detected').\n"
        "3. Provide a realistic confidence percentage string (e.g., '94%').\n"
        "4. Categorize the severity as one of: 'Mild', 'Moderate', 'Severe', or 'Healthy'.\n"
        "5. Provide 3 to 4 actionable, practical recommendations suitable for field implementation "
        "(sanitation, watering adjustments, organic bio-control, and safe chemical treatments where appropriate).\n"
        "6. Provide a concise weather-linked advisory alert (e.g., how relative humidity, temperature, or rain "
        "affects spore germination or what field precautions to take today)."
    )

    last_error = None
    for model_name in FALLBACK_MODELS:
        try:
            logger.info(f"Analyzing crop image with {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=file.content_type),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CropAnalysisResponse,
                    temperature=0.2,
                ),
            )

            response_text = response.text.strip()
            # Clean any potential markdown wrapping
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()

            result = CropAnalysisResponse.model_validate_json(response_text)
            return result

        except Exception as e:
            logger.warning(f"Crop analysis attempt with {model_name} failed: {e}")
            last_error = e

    logger.error(f"All model attempts failed for crop analysis. Last error: {last_error}")
    err_msg = getattr(last_error, "message", str(last_error))
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Gemini AI Service Error: {err_msg}"
    )


@app.post(
    "/api/ask-agronomist",
    response_model=AgronomistResponse,
    tags=["Agronomist AI"],
    summary="Ask Agronomist (English & Urdu Supported)"
)
async def ask_agronomist(payload: AgronomistQuery):
    """
    Answers farmer questions on crop care, pest management, fertilizers, and field conditions.
    Fully supports English and Urdu (اردو) text and transcribed speech.
    Utilizes Gemini 3.6 Flash / Interactions API with automatic fallback.
    """
    client = get_gemini_client()

    system_instruction = (
        "You are 'Agrova AI', an expert senior digital agronomist and agricultural extension specialist. "
        "You provide trusted, practical, and scientifically sound advice to smallholder farmers and growers.\n\n"
        "Guidelines:\n"
        "- Emphasize Integrated Pest Management (IPM), soil health, safe pesticide usage, and cost-effective cultural practices.\n"
        "- Tone: Respectful, encouraging, clear, and actionable.\n"
        "- Language rules:\n"
        "  * If the user writes or asks in Urdu (اردو) or Roman Urdu, answer in fluent, simple, accessible Urdu (اردو).\n"
        "  * If the user asks in English, answer in straightforward, farmer-friendly English.\n"
        "  * If technical chemical names or dosages are mentioned, explain them simply with safety instructions.\n"
        "- Structure your reply with clear bullet points or numbered steps where appropriate."
    )

    last_error = None
    for model_name in FALLBACK_MODELS:
        # 1. Try recommended Interactions API first
        if hasattr(client, "interactions") and client.interactions:
            try:
                logger.info(f"Trying Interactions API with {model_name}...")
                interaction = client.interactions.create(
                    model=model_name,
                    input=payload.question,
                    system_instruction=system_instruction,
                )
                if interaction and getattr(interaction, "output_text", None):
                    return AgronomistResponse(response=interaction.output_text.strip())
            except Exception as e_inter:
                logger.info(f"Interactions API with {model_name} had notice ({e_inter}), trying models.generate_content...")

        # 2. Try models.generate_content
        try:
            logger.info(f"Consulting agronomist with model {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=payload.question,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                    max_output_tokens=1000,
                ),
            )
            if response and response.text:
                return AgronomistResponse(response=response.text.strip())
        except Exception as e:
            logger.warning(f"Agronomist query attempt with {model_name} failed: {e}")
            last_error = e

    logger.error(f"All model attempts failed for agronomist query. Last error: {last_error}")
    err_msg = getattr(last_error, "message", str(last_error))
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Gemini AI Service Error: {err_msg}"
    )



@app.get(
    "/api/weather",
    response_model=WeatherResponse,
    tags=["Weather Analytics"],
    summary="Real-Time Weather via Open-Meteo"
)
async def get_weather(
    lat: float = Query(default=31.5497, description="Latitude (default: Punjab, PK 31.5497)"),
    lon: float = Query(default=74.3436, description="Longitude (default: Punjab, PK 74.3436)"),
    location_name: Optional[str] = Query(default=None, description="Optional custom location label")
):
    """
    Fetches real-time weather (temperature, humidity, precipitation chance) from the free Open-Meteo API.
    Defaults to Punjab, Pakistan coordinates.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,weather_code"
        f"&hourly=precipitation_probability"
        f"&forecast_days=1&timezone=auto"
    )

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        temp_val = current.get("temperature_2m")
        hum_val = current.get("relative_humidity_2m")

        # Get precipitation probability from hourly or fallback
        hourly = data.get("hourly", {})
        rain_prob_list = hourly.get("precipitation_probability", [])
        rain_val = rain_prob_list[0] if rain_prob_list else 0

        # Determine readable location name
        if location_name:
            resolved_location = location_name
        elif abs(lat - 31.5497) < 0.05 and abs(lon - 74.3436) < 0.05:
            resolved_location = "Punjab, PK"
        else:
            resolved_location = f"{lat:.2f}°, {lon:.2f}°"

        formatted_temp = f"{round(temp_val)}°C" if temp_val is not None else "28°C"
        formatted_humidity = f"{round(hum_val)}%" if hum_val is not None else "70%"
        formatted_rain = f"{round(rain_val)}%" if rain_val is not None else "20%"

        return WeatherResponse(
            temperature=formatted_temp,
            humidity=formatted_humidity,
            rain_chance=formatted_rain,
            location=resolved_location,
        )

    except httpx.RequestError as e:
        logger.warning(f"Open-Meteo network request failed: {e}. Returning fallback weather estimates.")
        return WeatherResponse(
            temperature="28°C",
            humidity="72%",
            rain_chance="30%",
            location=location_name or "Punjab, PK",
        )
    except Exception as e:
        logger.error(f"Error parsing weather data: {e}", exc_info=True)
        return WeatherResponse(
            temperature="28°C",
            humidity="72%",
            rain_chance="30%",
            location=location_name or "Punjab, PK",
        )


# -----------------------------------------------------------------------------
# Frontend Static Files & SPA Route
# -----------------------------------------------------------------------------
frontend_dir = Path(__file__).resolve().parent / "frontend"
index_html = frontend_dir / "index.html"

if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serves the Agrova web application."""
    if index_html.exists():
        return FileResponse(index_html, media_type="text/html")
    return JSONResponse(
        {"message": "Agrova API is active. Frontend index.html not found in /frontend directory."},
        status_code=200
    )


# -----------------------------------------------------------------------------
# Run standalone
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Agrova server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

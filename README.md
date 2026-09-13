Agrova AI

Full-Stack Agriculture Intelligence Platform

Agrova gives farmers an AI agronomist in their pocket. Snap a photo of a diseased leaf and get an instant diagnosis, ask farming questions in English or Urdu, and check live weather conditions — all from one lightweight web app that deploys anywhere in minutes.

Features
Crop Disease Detection — Upload or capture a leaf photo. gemini-2.5-flash returns a structured diagnosis: crop, disease, confidence, severity, and treatment steps.
Bilingual AI Agronomist — Conversational chat constrained to agricultural extension knowledge and IPM guidance, fluent in English and Urdu (اردو), with RTL support.
Live Weather Insights — Real-time temperature, humidity, and rain probability via the free Open-Meteo API, tied to farm location.
Camera-Ready Frontend — Responsive single-page app with native camera capture, gallery upload, and Web Speech API voice dictation.
1-Click Cloud Deploy — Ships with Dockerfile, Procfile, and render.yaml for instant deployment to Render, Railway, or Hugging Face Spaces.
Tech Stack
Backend — Python 3.11, FastAPI, Pydantic, Uvicorn, httpx
AI Engine — Google Gemini API (google-genai SDK, gemini-2.5-flash, multimodal + structured output)
Frontend — Vanilla HTML5 / CSS3 / JavaScript (no framework)
External API — Open-Meteo (weather)
Testing — Pytest
Deployment — Docker, Render, Railway
Project Structure
agrova/
├── main.py              # FastAPI backend: routes, Gemini integration, weather proxy
├── requirements.txt     # Python dependencies
├── Dockerfile            # Production container definition
├── Procfile               # Process command for Railway/Heroku
├── render.yaml             # Render deployment blueprint
├── .env.example              # Environment variable template
├── frontend/
│   └── index.html              # Single-page UI (camera, chat, weather)
├── tests/
│   └── test_api.py                # Pytest suite for API endpoints
└── README.md
API Reference
Method	Endpoint	Description
GET	/api/health	Service health check
POST	/api/analyze-crop	Upload a leaf image, returns structured disease diagnosis
POST	/api/ask-agronomist	Ask a farming question (English or Urdu)
GET	/api/weather	Live weather by lat/lon
GET	/	Serves the frontend SPA

Full interactive docs are available at /docs (Swagger) and /redoc once the server is running.

Example: Crop Analysis
bash
curl -X POST "http://localhost:8000/api/analyze-crop" \
  -F "file=@leaf_sample.jpg"
json
{
  "crop_name": "Tomato",
  "disease_name": "Early Blight",
  "confidence": "94%",
  "severity": "Moderate",
  "recommendations": [
    "Remove heavily infected leaves and dispose away from the field",
    "Avoid overhead watering; switch to drip or base irrigation",
    "Apply recommended copper-based bio-fungicide or chlorothalonil spray"
  ],
  "weather_alert": "High humidity detected; avoid evening irrigation to prevent fungal spore dispersal."
}
Example: Ask the Agronomist
bash
curl -X POST "http://localhost:8000/api/ask-agronomist" \
  -H "Content-Type: application/json" \
  -d '{"question": "My tomato leaves are turning brown, what should I spray?"}'

Supports the same request in Urdu — responses are returned in the language asked.

Getting Started
Prerequisites
Python 3.11+
A free Gemini API key from Google AI Studio
Installation
bash
git clone https://github.com/musmancys/Agrova-Ai.git
cd Agrova-Ai/agrova

python -m pip install -r requirements.txt

cp .env.example .env
# add your GEMINI_API_KEY inside .env

uvicorn main:app --reload --port 8000

Visit http://localhost:8000 for the app, or http://localhost:8000/docs for the API playground.

Run Tests
bash
python -m pytest tests/ -v
Docker
bash
docker build -t agrova-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here agrova-backend
Deployment
Render — Push to GitHub, create a New Blueprint (auto-detects render.yaml), set GEMINI_API_KEY, deploy.
Railway — New Project → Deploy from GitHub (auto-detects Dockerfile/Procfile), set GEMINI_API_KEY.
Hugging Face Spaces — New Space (SDK: Docker), push repo, add GEMINI_API_KEY as a secret.
License

Released under the MIT License.

Authors:
Muhammad Usman — github.com/musmancys


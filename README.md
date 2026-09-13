Agrova AI

Full-Stack Agriculture Intelligence Platform

Agrova is a production-ready AI platform that gives smallholder farmers immediate access to crop disease diagnosis, bilingual agronomic advisory, and live weather insights — all through a single lightweight web application.

A farmer photographs a diseased leaf, and within seconds receives a structured diagnosis with treatment recommendations. They can ask follow-up questions in English or Urdu, and check localized weather conditions before deciding whether to irrigate or spray.

Table of Contents
Features
Tech Stack
Architecture
Project Structure
API Reference
Getting Started
Testing
Docker
Deployment
Roadmap
License
Author
Features

Crop Disease Detection Upload or capture a leaf photo through the browser. The image is sent to Gemini 2.5 Flash for multimodal analysis, which returns a structured diagnosis — crop name, disease, confidence score, severity level, and specific treatment recommendations — validated against a strict Pydantic schema.

Bilingual AI Agronomist A conversational assistant constrained to agricultural extension manuals and Integrated Pest Management (IPM) practices. Farmers can ask questions naturally in English or Urdu (اردو), with full right-to-left text support in the interface.

Live Weather Insights Real-time temperature, humidity, and rain probability pulled from the Open-Meteo API based on farm coordinates, helping farmers time irrigation and spraying decisions around weather conditions rather than guesswork.

Camera-Ready Frontend A responsive single-page interface with native device camera capture, gallery upload, and voice dictation via the Web Speech API — built to work well on the low-end Android devices common among target users.

Deployment-Ready by Default Ships with a Dockerfile, Procfile, and render.yaml, so the entire stack can be deployed to Render, Railway, or Hugging Face Spaces without additional configuration.

Tech Stack
Layer	Technology
Backend	Python 3.11, FastAPI, Uvicorn
Data validation	Pydantic
AI / ML	Google Gemini API (google-genai SDK, gemini-2.5-flash)
Frontend	HTML5, CSS3, vanilla JavaScript (no framework)
External data	Open-Meteo API (weather)
HTTP client	httpx
Testing	Pytest
Containerization	Docker
Hosting	Render, Railway, Hugging Face Spaces
Architecture
┌─────────────────┐        ┌──────────────────┐        ┌────────────────┐
│   Frontend SPA   │  HTTP  │  FastAPI Backend  │  API   │  Gemini 2.5     │
│  (HTML/CSS/JS)   │ ─────> │     (main.py)      │ ─────> │  Flash (AI)     │
└─────────────────┘        └──────────────────┘        └────────────────┘
                                     │
                                     │ HTTP
                                     ▼
                            ┌──────────────────┐
                            │  Open-Meteo API   │
                            │   (weather data)   │
                            └──────────────────┘

The frontend is served directly by FastAPI as a static file, so the entire application runs as a single deployable service with no separate frontend hosting required.

Project Structure
agrova/
├── main.py              FastAPI backend — routes, Gemini integration, weather proxy
├── requirements.txt     Python dependencies
├── Dockerfile            Production container definition
├── Procfile               Process command for Railway / Heroku
├── render.yaml             Render deployment blueprint
├── .env.example              Environment variable template
├── frontend/
│   └── index.html              Single-page UI: camera capture, chat, weather
├── tests/
│   └── test_api.py                Pytest suite covering all API endpoints
└── README.md
API Reference
Method	Endpoint	Description
GET	/api/health	Returns service status and AI configuration state
POST	/api/analyze-crop	Accepts a leaf image, returns a structured disease diagnosis
POST	/api/ask-agronomist	Accepts a natural-language farming question, returns advisory text
GET	/api/weather	Returns live weather for given coordinates
GET	/	Serves the frontend application

Interactive documentation is available at /docs (Swagger UI) and /redoc once the server is running.

Example — Crop Analysis

Request:

bash
curl -X POST "http://localhost:8000/api/analyze-crop" \
  -F "file=@leaf_sample.jpg"

Response:

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
Example — Ask the Agronomist

Request:

bash
curl -X POST "http://localhost:8000/api/ask-agronomist" \
  -H "Content-Type: application/json" \
  -d '{"question": "My tomato leaves are turning brown, what should I spray?"}'

The same endpoint accepts questions in Urdu and responds in the language the question was asked.

Getting Started
Prerequisites
Python 3.11 or later
A Gemini API key, available free at Google AI Studio
Installation
bash
git clone https://github.com/musmancys/Agrova-Ai.git
cd Agrova-Ai/agrova

python -m pip install -r requirements.txt

cp .env.example .env
# open .env and set GEMINI_API_KEY

uvicorn main:app --reload --port 8000

The application is available at http://localhost:8000, with API documentation at http://localhost:8000/docs.

Testing
bash
python -m pytest tests/ -v

The test suite covers the health check endpoint, frontend serving, weather retrieval, agronomist query handling, and crop image validation against the Gemini response schema.

Docker
bash
docker build -t agrova-backend .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here agrova-backend
Deployment

Render Push the repository to GitHub, then in Render select New → Blueprint and choose the repository. Render auto-detects render.yaml. Set GEMINI_API_KEY under Environment Variables and deploy.

Railway Create a new project and deploy from the GitHub repository. Railway auto-detects the Dockerfile or Procfile. Add GEMINI_API_KEY under Variables.

Hugging Face Spaces Create a new Space with SDK set to Docker, push the repository, and add GEMINI_API_KEY as a secret under Space settings.

Roadmap
Expand disease detection coverage to additional crop types common in South Asia
Add offline-first support for low-connectivity rural areas
Persist conversation and diagnosis history per user
License

Released under the MIT License. See LICENSE for details.

Author

Muhammad Usman          github.com/musmancys
Muhammad Ali            github.com/M-Ali-i
Muhammad Tayyab Umair   github.com/tayyabumairr
Muhammad Mueez          github.com/muhammad-mueez13
Minahil Nadeem          github.com/MinahilNadeemm


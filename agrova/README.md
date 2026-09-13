# Agrova AI · Full-Stack Agriculture Intelligence Platform

Agrova is a modern, production-ready AI platform designed to empower smallholder farmers with immediate crop disease detection, localized agronomic advisory, and live weather insights.

---

## 🌟 Highlights

- **Framework**: FastAPI (Python 3.11) with full CORS support and static asset serving.
- **Multimodal AI Engine**: Powered by Google's official `google-genai` SDK and `gemini-2.5-flash` for high-speed, accurate leaf disease diagnosis with guaranteed structured Pydantic schema output.
- **Bilingual Digital Agronomist**: Context-constrained to agricultural extension manuals and Integrated Pest Management (IPM), supporting natural conversation in both **English** and **Urdu (اردو)**.
- **Live Weather Integration**: Connects dynamically to the free **Open-Meteo API** for live temperature, humidity, and rain probability based on location coordinates (defaults to Punjab, Pakistan).
- **Interactive Web App**: Complete responsive frontend featuring camera capture (`capture="environment"`), gallery upload, live AI chat with Web Speech API voice dictation, and RTL support.
- **Cloud-Ready**: Includes `Dockerfile`, `Procfile`, `render.yaml`, and `requirements.txt` for instant 1-click deployment on Render, Railway, Hugging Face Spaces, or VPS.

---

## 📁 Repository Structure

```
agrova/
├── main.py                # FastAPI backend application & endpoints
├── requirements.txt       # Production dependencies
├── Dockerfile             # Multi-stage container definition
├── Procfile               # Cloud process command for Render/Railway/Heroku
├── render.yaml            # Render infrastructure blueprint
├── .env.example           # Environment variable template
├── .env                   # Local environment configuration
├── frontend/
│   └── index.html         # Integrated Agrova UI with live fetch hooks
├── tests/
│   └── test_api.py        # Automated test suite (pytest)
└── README.md              # Documentation and deployment guide
```

---

## 🚀 Quick Start (Local Development)

### 1. Clone or Open Workspace
Navigate to the project directory:
```bash
cd "C:\Users\Phantom Killer\.gemini\antigravity\scratch\agrova"
```

### 2. Configure Environment Variables
Create a `.env` file (copied from `.env.example`):
```ini
GEMINI_API_KEY=AIzaSyYourActualKeyHere
PORT=8000
```
> Obtain your Gemini API key for free at [Google AI Studio](https://aistudio.google.com/).

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Run the Application
```bash
uvicorn main:app --reload --port 8000
```
Open your browser and navigate to:
- **Web App**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 API Endpoints Reference

### 1. Multimodal Crop Analysis
- **Endpoint**: `POST /api/analyze-crop`
- **Content-Type**: `multipart/form-data`
- **Payload**: `file` (Image file: JPEG, PNG, WebP)
- **Description**: Inspects plant leaf imagery with `gemini-2.5-flash` and returns a structured diagnostic report.
- **Sample Curl**:
```bash
curl -X POST "http://localhost:8000/api/analyze-crop" \
  -F "file=@leaf_sample.jpg"
```
- **Response Format**:
```json
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
```

---

### 2. Agronomist Consultation (English & Urdu)
- **Endpoint**: `POST /api/ask-agronomist`
- **Content-Type**: `application/json`
- **Payload**:
```json
{
  "question": "My tomato leaves are turning brown, what should I spray?"
}
```
- **Response Format**:
```json
{
  "response": "Your tomato leaves may be suffering from Early Blight (Alternaria solani). 1. Prune affected bottom foliage. 2. Avoid wetting foliage during watering. 3. Apply a preventive copper oxychloride or neem oil spray early in the morning."
}
```
*Supports Urdu queries:*
```json
{
  "question": "ٹماٹر کے پتے پیلے ہو رہے ہیں، مجھے کیا دوا ڈالنی چاہیے؟"
}
```
*Returns advice in clear, supportive Urdu.*

---

### 3. Live Weather Analytics
- **Endpoint**: `GET /api/weather`
- **Query Params**:
  - `lat` (optional float, default `31.5497`)
  - `lon` (optional float, default `74.3436`)
  - `location_name` (optional string)
- **Sample Request**:
```bash
curl "http://localhost:8000/api/weather?lat=31.5497&lon=74.3436"
```
- **Response Format**:
```json
{
  "temperature": "28°C",
  "humidity": "72%",
  "rain_chance": "30%",
  "location": "Punjab, PK"
}
```

---

### 4. Health Check
- **Endpoint**: `GET /api/health`
- **Response Format**:
```json
{
  "status": "healthy",
  "service": "Agrova AI Backend",
  "model": "gemini-2.5-flash",
  "gemini_api_key_configured": true
}
```

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
python -m pytest tests/ -v
```

Output verifies:
- Health check and system metadata
- Frontend SPA serving (`index.html`)
- Live weather retrieval via Open-Meteo
- Agronomist query validation & Gemini model responses
- Crop pathology image upload validation & structured schema validation

---

## 🐳 Docker Deployment

Build and run the container locally:
```bash
# Build Docker image
docker build -t agrova-backend .

# Run container with environment variable
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key_here agrova-backend
```

---

## ☁️ Cloud Deployment Guides

### Option 1: Render (Recommended)
1. Push the repository to GitHub.
2. In Render, click **New > Blueprint** and select your repository. Render will automatically detect [`render.yaml`](./render.yaml).
3. Under Environment Variables in the Render dashboard, set `GEMINI_API_KEY`.
4. Click **Apply** to deploy.

### Option 2: Railway
1. Click **New Project > Deploy from GitHub repo**.
2. Railway detects the `Dockerfile` or `Procfile` automatically.
3. Under **Variables**, add `GEMINI_API_KEY`.
4. Your application will be live at `https://your-project.up.railway.app`.

### Option 3: Hugging Face Spaces
1. Create a new Space with SDK: **Docker**.
2. Push this repository to your Space.
3. In Space **Settings > Variables and secrets**, add `GEMINI_API_KEY` under Secrets.
4. The space will automatically build and host the app on port 8000.

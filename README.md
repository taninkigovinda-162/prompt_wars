<<<<<<< HEAD
# 🏛️ CivicGuide — Smart Election Assistant

[![CI Pipeline](https://github.com/GovindaSaiKiran/prompt_wars_project_two/actions/workflows/ci.yml/badge.svg)](https://github.com/GovindaSaiKiran/prompt_wars_project_two/actions)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Deployed on Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-4285F4?logo=google-cloud)](https://smart-election-assistant-488041159564.us-central1.run.app/)
[![Powered by Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-Powered-FF6F00?logo=google)](https://ai.google.dev/)

> **An AI-powered civic education platform that guides every Indian citizen through voter registration and the voting process — built with Google Gemini, Cloud Run, Firebase, and FastAPI.**

## 🌐 Live Demo

**👉 [https://smart-election-assistant-488041159564.us-central1.run.app/](https://smart-election-assistant-488041159564.us-central1.run.app/)**

---

## 🎯 Problem Statement

The electoral process is complex and overwhelming for first-time voters. Official resources are scattered across multiple government websites, and there's no single interactive tool that walks citizens through the entire journey — from registration to casting their vote — in plain, beginner-friendly language.

## 💡 Our Solution

**CivicGuide** is a premium SaaS-style election education platform that combines:
- An **AI chatbot** powered by Google Gemini 2.5 Flash for instant, ECI-compliant guidance
- **Interactive visual guides** — video tutorials, Google Slides walkthroughs, and a polling day simulator
- **One-click Google Calendar integration** for election day reminders
- A **modern glassmorphism UI** designed for accessibility and engagement

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Chatbot** | Real-time Q&A powered by Gemini 2.5 Flash with structured bullet-point responses |
| 📋 **Voter Registration Guide** | Step-by-step Form 6 walkthrough with embedded Google Slides |
| 🗳️ **Voting Day Simulator** | Interactive 4-step polling booth experience |
| 🎥 **Video Tutorials** | Embedded YouTube guides for registration and voting |
| 📅 **Calendar Integration** | One-click Google Calendar reminder for election day |
| 🔒 **Security** | Rate limiting, CSP headers, input validation, Firebase Auth |
| ♿ **Accessible** | ARIA labels, keyboard navigation, focus trapping, skip links |
| ⚡ **Efficient** | Response caching (TTL), debounced inputs, lazy-loaded media |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                  User Browser                     │
│          (HTML/CSS/JS + Firebase Auth)            │
└─────────────────────┬────────────────────────────┘
                      │ HTTPS / JSON
                      ▼
┌──────────────────────────────────────────────────┐
│            Google Cloud Run (Container)           │
│  ┌────────────────────────────────────────────┐  │
│  │  FastAPI Backend                           │  │
│  │  • /ask endpoint (rate-limited)            │  │
│  │  • /health endpoint                        │  │
│  │  • Security headers middleware             │  │
│  │  • Pydantic request validation             │  │
│  └────────┬──────────────────┬────────────────┘  │
│           │                  │                    │
│           ▼                  ▼                    │
│   Google Gemini API    Cloud Firestore            │
│   (AI Responses)       (Chat Logging)             │
└──────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — High-performance async Python web framework
- **Pydantic** — Request/response validation with type safety
- **SlowAPI** — IP-based rate limiting (10 req/min)
- **Google Gemini 2.5 Flash** — AI response generation
- **Firebase Admin SDK** — Authentication & Firestore logging
- **Google Cloud Logging** — Production-grade observability

### Frontend
- **Vanilla HTML/CSS/JS** — Zero-framework, maximum performance
- **Glassmorphism UI** — Modern, premium design aesthetic
- **Font Awesome 6** — Icon library
- **Google Fonts (Outfit)** — Professional typography

### Infrastructure
- **Google Cloud Run** — Serverless container hosting
- **Docker** — Containerized deployment
- **GitHub Actions** — CI/CD pipeline (lint + test)

---

## ☁️ Google Services Integration

| Service | Usage |
|---|---|
| **Gemini 2.5 Flash** | AI chatbot responses |
| **Cloud Run** | Production hosting |
| **Cloud Logging** | Structured log aggregation |
| **Firebase Auth** | Anonymous user authentication |
| **Cloud Firestore** | Chat history persistence |
| **Google Slides** | Embedded registration guide |
| **YouTube** | Embedded video tutorials |
| **Google Calendar** | Election day reminder links |
| **Google Fonts** | Typography (Outfit) |

---

## 🔒 Security Practices

- **Environment Variables** — API keys injected via Cloud Run, never committed
- **Rate Limiting** — 10 requests/minute per IP via SlowAPI
- **Content Security Policy** — Strict CSP headers on all responses
- **Input Validation** — Pydantic `min_length=1, max_length=500` with whitespace stripping
- **Prompt Injection Mitigation** — System prompt guards against override attempts
- **HSTS + X-Frame-Options** — Transport and framing security headers
- **Firebase Auth** — Token-based authentication with anonymous fallback

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/GovindaSaiKiran/prompt_wars_project_two.git
cd prompt_wars_project_two

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
echo "GEMINI_API_KEY=your_actual_key" > backend/.env

# 5. Run the server
cd backend
uvicorn app.main:app --reload --port 8000

# 6. Open in browser
# http://localhost:8000
```

---

## 🧪 Testing

```bash
# Run all tests
set GEMINI_API_KEY=mock_key_for_testing   # Windows
export GEMINI_API_KEY=mock_key_for_testing # Linux/Mac
pytest tests/ -v --tb=short
```

**Test Coverage:**
- Health endpoint validation
- AI service initialization (valid/invalid keys)
- Response generation and caching
- Input validation (empty, oversized, missing fields)
- Security header verification
- Firestore logging

---

## 📁 Project Structure

```
prompt_wars_project_two/
├── .github/workflows/ci.yml    # CI/CD pipeline
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app factory
│   │   ├── models/schemas.py   # Pydantic request/response models
│   │   ├── routes/routes.py    # API endpoints
│   │   ├── services/
│   │   │   ├── ai_service.py   # Gemini AI integration
│   │   │   └── db_service.py   # Firestore chat logging
│   │   └── utils/
│   │       ├── auth.py         # Firebase token verification
│   │       ├── config.py       # Pydantic settings
│   │       └── security.py     # Rate limiting setup
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Main SPA page
│   ├── style.css               # Core styles
│   ├── script.js               # Chat & UI logic
│   ├── app.js                  # App interactions
│   └── content.js              # Content modules
├── tests/                      # Pytest test suite
├── Dockerfile                  # Container configuration
└── README.md
```

---

## 🚀 Deployment (Cloud Run)

```bash
# Authenticate
gcloud auth login
gcloud config set project proven-serenity-494705-u8

# Deploy from source
gcloud run deploy smart-election-assistant \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --update-env-vars GEMINI_API_KEY="your-key-here"
```

---

## 🔮 Future Improvements

- 🌍 Multi-language support (Hindi, regional languages) via Gemini translation
- 📱 PWA support for offline usage
- 🗳️ Real-time ECI API integration for live voter roll lookup
- 📊 Admin analytics dashboard for chatbot usage insights

---

## 👥 Team

Built for hackathon evaluation — showcasing production-grade Google Cloud & AI integration.

---

<p align="center">
  <b>🇮🇳 Empowering Democracy Through Technology 🇮🇳</b>
</p>
=======
# new_war
>>>>>>> 21b6aece43e9ccbcbc49fc921475eea8003e4f86

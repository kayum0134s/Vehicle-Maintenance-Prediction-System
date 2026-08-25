# 🚗 Vehicle Maintenance Prediction System (VMPS)

> *AI-powered predictive vehicle diagnostics — powered by scikit-learn ML*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-orange?style=flat-square)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=flat-square)

----

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 AI Prediction Engine | Random Forest + Gradient Boosting + Decision Tree |
| 📊 Analytics Dashboard | Health trend, risk pie chart, failure probability |
| 🔐 Auth System | Login / Signup with session management |
| 📄 PDF Export | Full maintenance report via ReportLab |
| 🤖 AI Chatbot | Natural language maintenance Q&A |
| 🎤 Voice Input | Browser speech recognition for form filling |
| 🔔 Real-time Alerts | Critical/High severity alert panel |
| 🌙 Dark Mode | Toggle between dark and light themes |
| 📋 History | Full prediction history per vehicle |

---

## 🚀 Quick Start

### Option 1 — Double-click launcher
```
start.bat
```

### Option 2 — Manual
```bash
pip install -r requirements.txt
python app.py
```

Open: **http://localhost:5000**  
Login: **admin@vmps.ai** / **admin123**

----

## 📁 Project Structure

```
Sameerr/
├── app.py                    # Flask entry point
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
├── start.bat                 # Windows launcher
├── models/
│   ├── vehicle_model.py      # SQLAlchemy models (User, Vehicle, Prediction, Alert)
│   └── ml_engine.py          # scikit-learn ML engine
├── routes/
│   ├── auth.py               # Login / Signup / Logout
│   └── api.py                # REST API (vehicles, predictions, chatbot, PDF)
├── static/
│   ├── css/style.css         # Glassmorphism neon CSS
│   └── js/
│       ├── particles.js      # Canvas particle system
│       ├── charts.js         # Chart.js helpers
│       └── main.js           # Full app logic
└── templates/
    ├── login.html            # Login / Signup page
    └── index.html            # Dashboard SPA
```

---

## 🧠 ML Engine

| Model | Task |
|---|---|
| Random Forest Classifier | Predicts maintenance required (Yes/No) |
| Gradient Boosting Regressor | Predicts vehicle health score (0-100%) |
| Decision Tree Classifier | Identifies failure component |
| Rule-based Engine | Determines urgency level (LOW/MEDIUM/HIGH/CRITICAL) |

**Training data:** 5,000 synthetic vehicle records  
**Input features:** mileage, engine_temp, oil_quality, tire_pressure, brake_condition, battery_health, fuel_efficiency, service_history, days_since_service

---

## 🌐 REST API

| Endpoint | Method | Description |
|---|---|---|
| `/api/auth/login` | POST | Authenticate user |
| `/api/auth/register` | POST | Create account |
| `/api/vehicles` | GET/POST | List / Add vehicles |
| `/api/vehicles/<id>` | GET/PUT/DELETE | CRUD operations |
| `/api/predict/quick` | POST | Quick prediction (save + analyze) |
| `/api/vehicles/<id>/predict` | POST | Run prediction for saved vehicle |
| `/api/vehicles/<id>/predictions` | GET | Prediction history |
| `/api/alerts` | GET | Alert list |
| `/api/dashboard` | GET | Dashboard stats + trend data |
| `/api/vehicles/<id>/report` | GET | Download PDF report |
| `/api/chatbot` | POST | AI chatbot response |

---

## 🎨 Design System

- **Font:** Orbitron (headings) + Inter (body)
- **Colors:** Neon Blue `#00d4ff` · Electric Purple `#8b5cf6` · Neon Green `#06ffa5`
- **Style:** Glassmorphism · Dark void background · Animated particles
- **Charts:** Chart.js 4.4 with neon-themed line, doughnut, and bar charts

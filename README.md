# 🚗 Vehicle Maintenance Prediction System (VMPS)

> *AI-powered predictive vehicle diagnostics — powered by scikit-learn ML*

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?style=flat-square&logo=flask)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-orange?style=flat-square)
![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E?style=flat-square&logo=supabase)
![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?style=flat-square&logo=vercel)

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

---

## 🗄️ Supabase PostgreSQL Setup & Vercel Deployment Guide

### 1. Create a Supabase Project
1. Log in to [Supabase](https://supabase.com).
2. Click **New Project** and select an organization, name (e.g., `vmps-db`), database password, and preferred region.
3. Wait for the project initialization to complete.

### 2. Obtain Connection String
1. Go to **Project Settings** -> **Database** -> **Connection string**.
2. Select **URI** mode:
   - **Recommended for Vercel Serverless (Port 6543 - Transaction Pooler):**
     ```text
     postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
     ```
   - **Direct Connection (Port 5432):**
     ```text
     postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
     ```
3. Replace `[YOUR-PASSWORD]` with your actual database password. If your password contains special characters (like `@`, `#`, `%`), ensure they are URL-encoded.

### 3. Initialize or Migrate Schema in Supabase
Choose one of two quick methods:

#### Method A: Supabase Dashboard SQL Editor (Instant)
1. Open your Supabase Dashboard and navigate to the **SQL Editor** on the left navigation.
2. Open `supabase_schema.sql` from this repository, copy its contents, paste into the SQL Editor, and click **Run**.
3. All tables (`users`, `vehicles`, `predictions`, `alerts`) and indexes are created immediately.

#### Method B: Local CLI Initialization
With your `DATABASE_URL` configured in your local `.env`:
```bash
python manage_db.py init-db
python manage_db.py seed-demo
```

### 4. Migrate Existing Local SQLite Records to PostgreSQL
If you have records in `instance/vehicle_maintenance.db` that you want to migrate to Supabase:
```bash
# 1. Set your Supabase connection string temporarily
export DATABASE_URL="postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require"
# On Windows PowerShell:
# $env:DATABASE_URL="postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require"

# 2. Run the migration script
python manage_db.py migrate-from-sqlite
```
This script safely copies users, vehicles, predictions, and alerts while preserving primary keys, timestamps, and resetting PostgreSQL sequence counters.

### 5. Configure Vercel Environment Variables
In your Vercel Dashboard -> Your Project -> **Settings** -> **Environment Variables**, add:

| Variable | Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres.[REF]:[PASS]@[HOST]:6543/postgres?sslmode=require` | Supabase connection string |
| `SECRET_KEY` | `<strong-random-secret-key>` | Flask session secret |
| `DEBUG` | `False` | Disables debug mode in production |

*(Optional pool tuning variables: `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=2`, `DB_POOL_RECYCLE=300`)*

### 6. Local Development
```bash
# Install dependencies including PostgreSQL driver
pip install -r requirements.txt

# Option A: Run with local SQLite (when DATABASE_URL is not set)
python app.py

# Option B: Run with Supabase PostgreSQL
# Configure DATABASE_URL in .env
python app.py
```

### 7. Deploying to Vercel
```bash
# Deploy using Vercel CLI
vercel --prod
```
Or push your changes to your linked Git repository (GitHub/GitLab/Bitbucket), and Vercel will build and deploy automatically.

### 8. Troubleshooting Connection Failures
- **`prepared statement "..." does not exist`**:
  - Cause: Connecting to Supabase transaction pooler (port 6543) with prepared statements enabled.
  - Solution: Automatically handled! VMPS config sets `prepare_threshold=None` in `connect_args` for `postgresql+psycopg`.
- **`Tenant or user not found`**:
  - Cause: Incorrect user format on Supabase pooler.
  - Solution: When using port 6543, username must be `postgres.[PROJECT-REF]`, not just `postgres`.
- **`FATAL: password authentication failed`**:
  - Cause: Wrong database password or unencoded special characters in connection URI.
  - Solution: Reset password in Supabase Dashboard -> Database Settings, and URL-encode special characters in URI.
- **`OSError: [Errno 30] Read-only file system: '/var/task/instance'`**:
  - Cause: Missing `DATABASE_URL` on Vercel caused fallback to local SQLite.
  - Solution: Configure `DATABASE_URL` in Vercel project environment variables.

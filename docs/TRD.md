# Technical Requirements Document (TRD)

## Vehicle Maintenance Prediction System (VMPS)

---

| Field             | Details                                      |
|-------------------|----------------------------------------------|
| **Document ID**   | VMPS-TRD-001                                 |
| **Version**       | 1.0.0                                        |
| **Status**        | Final                                        |
| **Created**       | 2026-05-15                                   |
| **Author**        | Sameer                                       |
| **References PRD**| VMPS-PRD-001                                 |

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [System Architecture](#3-system-architecture)
4. [Database Schema](#4-database-schema)
5. [ML Engine Design](#5-ml-engine-design)
6. [REST API Specification](#6-rest-api-specification)
7. [Frontend Architecture](#7-frontend-architecture)
8. [Authentication & Security](#8-authentication--security)
9. [PDF Generation](#9-pdf-generation)
10. [Configuration & Environment](#10-configuration--environment)
11. [Project Structure](#11-project-structure)
12. [Dependencies](#12-dependencies)
13. [Deployment Guide](#13-deployment-guide)
14. [Known Limitations & Future Work](#14-known-limitations--future-work)

---

## 1. System Overview

VMPS is a **monolithic Flask web application** with a clear internal separation of concerns:

```
Browser (HTML/CSS/JS + Chart.js)
        │   HTTP/JSON
        ▼
Flask Application (app.py)
 ├── Auth Blueprint  (routes/auth.py)
 ├── API Blueprint   (routes/api.py)
 │        │
 │        ├── VehicleMLEngine  (models/ml_engine.py)
 │        └── SQLAlchemy ORM   (models/vehicle_model.py)
 │                  │
 │                  ▼
 │          SQLite Database (instance/vehicle_maintenance.db)
 └── Jinja2 Templates (templates/)
```

The application is **session-based** (not token-based). All API routes verify `session['user_id']` before serving data, ensuring strict user isolation.

---

## 2. Technology Stack

### Backend

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | 3.10+ |
| Web Framework | Flask | 3.0.3 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| Database | SQLite (via SQLAlchemy) | — |
| Auth Hashing | Werkzeug (PBKDF2-SHA256) | 3.0.3 |
| CORS | Flask-CORS | 4.0.1 |
| PDF Generation | ReportLab | 4.2.2 |
| Env Config | python-dotenv | 1.0.1 |

### Machine Learning

| Library | Version | Purpose |
|---------|---------|---------|
| scikit-learn | 1.5.0 | ML classifiers and regressors |
| numpy | 1.26.4 | Numerical computation |
| pandas | 2.2.2 | Data handling utilities |

### Frontend

| Technology | Purpose |
|-----------|---------|
| HTML5 / CSS3 | Structure & styling |
| Vanilla JavaScript (ES6+) | UI logic, API calls |
| Chart.js (CDN) | Interactive charts |
| Google Fonts: Orbitron + Rajdhani | Typography |
| CSS Custom Properties | Design token system |

---

## 3. System Architecture

### Request–Response Flow

```
User Action (e.g., "Analyze Vehicle")
        │
        ▼
[Frontend JS] fetch('/api/vehicles/<id>/predict', {method:'POST'})
        │
        ▼
[Flask API Blueprint] routes/api.py → predict()
        │  validates session['user_id']
        │  loads Vehicle from SQLite via ORM
        ▼
[VehicleMLEngine] ml_engine.predict(vehicle_data)
        │  _preprocess() → StandardScaler transform
        │  RandomForestClassifier → maintenance_required
        │  GradientBoostingRegressor → health_score
        │  DecisionTreeClassifier → failure_code
        │  _compute_urgency(), _get_risk_level()
        │  _get_recommendations() → costed action list
        ▼
[SQLAlchemy] Prediction + Alert records saved to SQLite
        │
        ▼
[JSON Response] → Frontend renders gauges, cards, alerts
```

### Blueprint Architecture

```
app.py (Application Factory)
  └── create_app()
       ├── Config  ←  config.py
       ├── db.init_app(app)
       ├── app.register_blueprint(auth)   ← routes/auth.py
       ├── app.register_blueprint(api)    ← routes/api.py
       ├── @app.route('/')   → index.html  (auth guard)
       └── @app.route('/login') → login.html
```

---

## 4. Database Schema

### Entity Relationship Overview

```
users (1) ──< vehicles (N) ──< predictions (N)
                            └──< alerts (N)
```

### Table: `users`

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `username` | VARCHAR(80) | UNIQUE, NOT NULL |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(200) | NOT NULL |
| `created_at` | DATETIME | DEFAULT `utcnow` |

### Table: `vehicles`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY | |
| `user_id` | INTEGER | FK → users.id, NOT NULL | Ownership |
| `vehicle_number` | VARCHAR(50) | NOT NULL | e.g., `MH-01-AB-1234` |
| `vehicle_model` | VARCHAR(100) | NOT NULL | |
| `manufacturer` | VARCHAR(100) | NOT NULL | |
| `mileage` | FLOAT | DEFAULT 0 | km |
| `engine_temp` | FLOAT | DEFAULT 90 | °C |
| `oil_quality` | FLOAT | DEFAULT 80 | % |
| `tire_pressure` | FLOAT | DEFAULT 32 | PSI |
| `brake_condition` | FLOAT | DEFAULT 80 | % |
| `battery_health` | FLOAT | DEFAULT 85 | % |
| `fuel_efficiency` | FLOAT | DEFAULT 30 | km/L |
| `service_history` | INTEGER | DEFAULT 1 | count of past services |
| `last_service_date` | VARCHAR(20) | nullable | ISO date string |
| `created_at` | DATETIME | DEFAULT `utcnow` | |
| `updated_at` | DATETIME | DEFAULT `utcnow` | auto-updates on save |

### Table: `predictions`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER | PRIMARY KEY |
| `vehicle_id` | INTEGER | FK → vehicles.id |
| `health_score` | FLOAT | 0–100 |
| `maintenance_required` | BOOLEAN | |
| `risk_level` | VARCHAR(20) | LOW / MEDIUM / HIGH / CRITICAL |
| `urgency` | VARCHAR(20) | LOW / MEDIUM / HIGH / CRITICAL |
| `failure_components` | TEXT | JSON array of component names |
| `recommendations` | TEXT | JSON array of recommendation objects |
| `estimated_cost` | FLOAT | USD |
| `accuracy` | FLOAT | ML confidence % |
| `created_at` | DATETIME | |

### Table: `alerts`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER | PRIMARY KEY |
| `vehicle_id` | INTEGER | FK → vehicles.id |
| `message` | VARCHAR(500) | |
| `severity` | VARCHAR(20) | INFO / WARNING / CRITICAL |
| `is_read` | BOOLEAN | DEFAULT False |
| `created_at` | DATETIME | |

---

## 5. ML Engine Design

### Class: `VehicleMLEngine`  (`models/ml_engine.py`)

#### Models Used

| Model | Algorithm | scikit-learn Class | Task |
|-------|-----------|-------------------|------|
| `rf_classifier` | Random Forest (100 trees, max_depth=8) | `RandomForestClassifier` | Binary: maintenance needed? |
| `gb_regressor` | Gradient Boosting (100 trees, lr=0.1) | `GradientBoostingRegressor` | Continuous: health score |
| `dt_classifier` | Decision Tree (max_depth=6) | `DecisionTreeClassifier` | Multi-class: failure component |
| `gb_classifier` | Gradient Boosting | `GradientBoostingClassifier` | Alternate failure label model |

---

### Algorithm Deep-Dive

This section documents every algorithm used in VMPS — from data preprocessing through ML inference to the post-prediction rule engine — explaining **how each works**, **why it was chosen**, and **how it is configured**.

---

#### Algorithm 1 — StandardScaler (Feature Preprocessing)

**Category:** Data Preprocessing  
**scikit-learn class:** `sklearn.preprocessing.StandardScaler`

**How it works:**

StandardScaler transforms each feature so that it has **zero mean (μ = 0)** and **unit variance (σ = 1)** using the formula:

```
z = (x - μ) / σ
```

Where `μ` is the mean and `σ` is the standard deviation of the feature computed from the training dataset.

**Why it is used in VMPS:**

The 9 input features span wildly different numerical ranges — `mileage` reaches 250,000 km while `service_history` is 0–20. Without scaling, distance-sensitive algorithms (and even tree-based ones using impurity measures) can be biased toward high-magnitude features. Standardisation ensures every feature contributes proportionally.

**Configuration:**

```python
self.scaler = StandardScaler()
X_scaled = self.scaler.fit_transform(X)   # Fit on training data
X_scaled = self.scaler.transform(X_input) # Transform at inference time
```

> The scaler is **fit only on training data** and reused at prediction time — preventing data leakage.

---

#### Algorithm 2 — Random Forest Classifier

**Task:** Binary classification — "Does this vehicle need maintenance?" (YES / NO)  
**scikit-learn class:** `sklearn.ensemble.RandomForestClassifier`

**How it works:**

Random Forest is an **ensemble of Decision Trees** trained using **Bootstrap Aggregation (Bagging)**:

1. **Bootstrap sampling:** Draw `n` random samples *with replacement* from the training dataset to create `T` different subsets.
2. **Tree construction:** Grow a full Decision Tree on each subset. At every split, only a **random subset of `√features`** is considered (feature randomness reduces correlation between trees).
3. **Voting:** For classification, each tree casts a vote. The class with the most votes wins.
4. **Probability output:** `predict_proba()` returns the fraction of trees that voted for each class — used in VMPS as the **maintenance probability** percentage.

```
Final prediction = majority vote across all T trees
Maintenance probability = (trees voting YES) / T × 100%
```

**Why Random Forest for this task:**

| Reason | Detail |
|--------|--------|
| Robustness | Averaging across 100 trees reduces overfitting on synthetic data |
| Probability output | `predict_proba()` gives maintenance probability %, not just YES/NO |
| Feature importance | Can identify which sensor readings most drive maintenance decisions |
| Non-linear boundaries | Captures complex interactions (e.g., high temp AND low oil = critical) |
| Resistant to outliers | Bagging reduces influence of anomalous training samples |

**Hyperparameters configured in VMPS:**

| Parameter | Value | Effect |
|-----------|-------|--------|
| `n_estimators` | 100 | 100 trees — balances accuracy vs. training speed |
| `max_depth` | 8 | Prevents over-deep trees that memorise noise |
| `random_state` | 42 | Reproducible results |
| `criterion` | `gini` (default) | Gini impurity for split quality |

**Usage in prediction pipeline:**

```python
maintenance_prob = self.rf_classifier.predict_proba(X)[0]
# maintenance_prob = [prob_NO, prob_YES]
maintenance_required = bool(maintenance_prob[1] > 0.4)   # Threshold: 40%
maintenance_probability = round(maintenance_prob[1] * 100, 1)
```

The threshold is set at **0.4** (rather than 0.5) to favour false positives — it is safer to flag a healthy vehicle for inspection than to miss a failing one.

---

#### Algorithm 3 — Gradient Boosting Regressor

**Task:** Continuous regression — predict the Vehicle Health Score (0–100)  
**scikit-learn class:** `sklearn.ensemble.GradientBoostingRegressor`

**How it works:**

Gradient Boosting builds trees **sequentially**, where each new tree corrects the residual errors of the previous ensemble:

1. **Initialise** with a constant prediction (mean of target values).
2. **Compute residuals:** `residual = actual_health - predicted_health`
3. **Fit a shallow tree** to the residuals (learning the error pattern).
4. **Update prediction:** `prediction += learning_rate × tree_output`
5. **Repeat** for `n_estimators` iterations.

```
F₀ = mean(y)
For m = 1 to M:
    rᵢ = yᵢ - Fₘ₋₁(xᵢ)       ← residuals
    hₘ = DecisionTree(X, r)    ← fit tree to residuals
    Fₘ = Fₘ₋₁ + η × hₘ        ← update (η = learning rate)
```

**Why Gradient Boosting for health score regression:**

| Reason | Detail |
|--------|--------|
| Non-linear relationships | Health degrades non-linearly with mileage and temperature |
| High accuracy on structured data | Consistently outperforms linear models on tabular sensor data |
| Handles mixed feature scales | Works with the standardised feature vector |
| Smooth output | Produces continuous scores across the full [5, 98] range |

**Hyperparameters configured in VMPS:**

| Parameter | Value | Effect |
|-----------|-------|--------|
| `n_estimators` | 100 | 100 boosting rounds |
| `learning_rate` | 0.1 | Shrinkage — prevents overfitting by scaling each tree's contribution |
| `random_state` | 42 | Reproducible |
| `loss` | `squared_error` (default) | Minimises MSE — appropriate for continuous health score target |

**Usage in prediction pipeline:**

```python
health_score = float(np.clip(self.gb_regressor.predict(X)[0], 5, 98))
```

Output is clipped to `[5, 98]` to avoid physically impossible values (a vehicle is never truly 0% or 100% health in practice).

---

#### Algorithm 4 — Decision Tree Classifier

**Task:** Multi-class classification — identify the primary failing component  
**scikit-learn class:** `sklearn.tree.DecisionTreeClassifier`

**Classes (6-class output):**

| Class Code | Component |
|-----------|-----------|
| 0 | All Systems Normal |
| 1 | Engine Overheating |
| 2 | Brake Wear Critical |
| 3 | Battery Failure Risk |
| 4 | Tire Pressure Abnormal |
| 5 | Oil Degradation |

**How it works:**

A Decision Tree recursively **splits the feature space** using the best threshold found at each node:

1. **At root:** Evaluate every possible split `(feature_j, threshold_t)`.
2. **Select the split** that maximises **information gain** (reduction in Gini impurity or entropy):
   ```
   Gain = Impurity(parent) - Σ (|child| / |parent|) × Impurity(child)
   ```
3. **Recurse** on each child node until `max_depth` is reached or the node is pure.
4. **Leaf nodes** contain the majority class label.

**Why Decision Tree for component failure detection:**

| Reason | Detail |
|--------|--------|
| Interpretability | The tree's decision path explains *why* a component is flagged |
| Fast inference | Single tree traversal — O(depth) = O(6) |
| Handles multi-class natively | No one-vs-rest decomposition needed |
| Matches rule-like domain knowledge | e.g., "if engine_temp > 115 → Engine failure" maps naturally to tree splits |
| Lightweight | Low memory footprint vs. ensemble methods |

**Hyperparameters configured in VMPS:**

| Parameter | Value | Effect |
|-----------|-------|--------|
| `max_depth` | 6 | Limits tree complexity — 6 levels sufficient for 6 component classes |
| `random_state` | 42 | Reproducible splits |
| `criterion` | `gini` (default) | Gini impurity for split selection |

**Usage in prediction pipeline:**

```python
failure_code = int(self.dt_classifier.predict(X)[0])
failure_component = self.COMPONENT_MAP.get(failure_code, 'Unknown')
```

---

#### Algorithm 5 — Gradient Boosting Classifier (Secondary)

**Task:** Alternate multi-class classification of failure components  
**scikit-learn class:** `sklearn.ensemble.GradientBoostingClassifier`

**How it works:**

Extends the Gradient Boosting framework (Algorithm 3) to classification using **softmax loss** for multi-class problems. Trains one set of boosted trees per class in a one-vs-rest fashion internally, then selects the class with highest predicted log-odds.

**Role in VMPS:**

Trained on the same failure label targets as the Decision Tree, providing a higher-accuracy alternative. Currently, `dt_classifier` is used for inference (for speed and interpretability), while `gb_classifier` is available for ensemble extension or A/B comparison.

**Hyperparameters:**

| Parameter | Value |
|-----------|-------|
| `n_estimators` | 100 |
| `random_state` | 42 |
| `learning_rate` | 0.1 (default) |

---

#### Algorithm 6 — Rule-Based Urgency Classification

**Category:** Domain Expert Rule Engine (post-ML)  
**Location:** `_compute_urgency()` in `ml_engine.py`

**How it works:**

After the ML models produce a health score, a **deterministic priority-tree** maps numeric thresholds to urgency labels. This is a structured **if-else cascade** prioritising CRITICAL conditions first:

```
if health < 30 OR engine_temp > 120 OR brake < 15 OR battery < 10:
    → CRITICAL
elif health < 50 OR engine_temp > 110 OR brake < 30 OR battery < 25:
    → HIGH
elif health < 70:
    → MEDIUM
else:
    → LOW
```

**Why rule-based (not ML) for urgency:**

Domain experts define safety thresholds precisely (e.g., brakes below 15% = immediate stop). Hard-coded rules ensure **no ML uncertainty** exists for life-safety classifications — a well-understood advantage of hybrid architectures.

---

#### Algorithm 7 — Rule-Based Recommendation Engine

**Category:** Expert System / Decision Rules  
**Location:** `_get_recommendations()` in `ml_engine.py`

**How it works:**

Iterates over each sensor reading and applies **independent threshold rules** to generate costed maintenance actions. Each rule produces a recommendation object:

```python
{ 'icon': str, 'action': str, 'priority': str, 'cost': int }
```

Rules are independent (multiple can fire simultaneously), producing a ranked list of actions sorted by severity. Total estimated cost is the sum of all non-INFO recommendation costs:

```python
estimated_cost = Σ rec['cost'] for rec where rec['priority'] != 'INFO'
```

**Why rule-based recommendations:**

| Reason | Detail |
|--------|--------|
| Domain transparency | Service technicians understand and can audit every threshold |
| Cost estimation | Fixed lookup table of standard repair costs |
| No training data needed | Works from day one without historical repair records |
| Explainability | User sees exactly why each action is recommended |

---

#### Algorithm 8 — Ensemble Confidence Scoring

**Category:** Model Meta-Analysis  
**Location:** `predict()` in `ml_engine.py`

**How it works:**

VMPS reports a **prediction accuracy/confidence score** derived from the Random Forest's class probability output:

```python
rf_conf = max(rf_classifier.predict_proba(X)[0])   # Max class probability [0.0–1.0]
accuracy = min(98.0, 85.0 + rf_conf * 13.0)        # Scaled to [85%–98%]
```

**Rationale for the formula:**
- A `rf_conf` of 1.0 (perfectly confident) → accuracy = 98%
- A `rf_conf` of 0.5 (uncertain) → accuracy = 91.5%
- Floors at 85% to reflect the model's inherent baseline accuracy on the training distribution
- Capped at 98% to avoid claiming perfect prediction

---

#### Summary: Algorithm Selection Matrix

| Algorithm | Type | Task | Why Chosen |
|-----------|------|------|-----------|
| StandardScaler | Preprocessing | Feature normalisation | Equalises feature scale for all models |
| Random Forest Classifier | Ensemble (Bagging) | Maintenance YES/NO | Robust, probability output, handles non-linearity |
| Gradient Boosting Regressor | Ensemble (Boosting) | Health Score (0–100) | High accuracy on structured regression tasks |
| Decision Tree Classifier | Single Model | Failure component ID | Fast, interpretable, multi-class native |
| Gradient Boosting Classifier | Ensemble (Boosting) | Failure component (alternate) | Higher accuracy alternative to Decision Tree |
| Rule-Based Urgency Engine | Expert System | Urgency classification | Safety-critical decisions need deterministic logic |
| Rule-Based Recommendation Engine | Expert System | Maintenance actions + costs | Transparent, auditable, no training data required |
| Ensemble Confidence Scoring | Meta-analysis | Prediction confidence % | Converts RF probability to user-friendly accuracy metric |

---

#### Input Feature Vector (9 dimensions)

| Index | Feature | Range | Unit |
|-------|---------|-------|------|
| 0 | `mileage` | 0–250,000 | km |
| 1 | `engine_temp` | 60–130 | °C |
| 2 | `oil_quality` | 0–100 | % |
| 3 | `tire_pressure` | 20–45 | PSI |
| 4 | `brake_condition` | 0–100 | % |
| 5 | `battery_health` | 0–100 | % |
| 6 | `fuel_efficiency` | 5–50 | km/L |
| 7 | `service_history` | 0–20 | count |
| 8 | `days_since_service` | 0–730 | days |

All features are **standardised** via `StandardScaler` (zero mean, unit variance) before inference.

#### Synthetic Training Dataset

Generated at application startup via `_generate_synthetic_dataset(n_samples=5000)`:

- **Health score formula** (weighted sum):
  ```
  health_score =
    (100 - mileage/2500) × 0.15   +   # mileage degradation
    (100 - clip((temp-90)×2, 0, 100)) × 0.15  +  # temp penalty
    oil_quality × 0.18            +
    (100 - |tire_pressure - 32| × 3) × 0.12  +
    brake_condition × 0.18        +
    battery_health × 0.12         +
    (fuel_efficiency / 50 × 100) × 0.10
  ```
  Clipped to range **[5, 98]**.

- **Maintenance label** (binary): `1` when any of:
  - `oil_quality < 30`
  - `brake_condition < 25`
  - `battery_health < 20`
  - `engine_temp > 110`
  - `days_since_service > 365`
  - `health_score < 40`

- **Component failure label** (6-class): deterministic rule assignments (Engine > Brakes > Battery > Tires > Oil > None).

#### Urgency Rules (post-prediction, rule-based override)

| Urgency | Condition |
|---------|-----------|
| CRITICAL | health < 30 OR engine_temp > 120 OR brake < 15 OR battery < 10 |
| HIGH | health < 50 OR engine_temp > 110 OR brake < 30 OR battery < 25 |
| MEDIUM | health < 70 |
| LOW | all else |

#### Recommendation Engine (`_get_recommendations`)

Rule-based system generating costed actions:

| Condition | Action | Priority | Est. Cost (USD) |
|-----------|--------|----------|-----------------|
| oil < 40% | Change engine oil immediately | CRITICAL | $80 |
| oil < 65% | Schedule oil change (2 weeks) | HIGH | $60 |
| brake < 30% | Replace brake pads urgently | CRITICAL | $250 |
| brake < 55% | Inspect brake pads | HIGH | $200 |
| battery < 25% | Replace battery immediately | CRITICAL | $180 |
| battery < 50% | Battery inspection | HIGH | $40 |
| \|pressure-32\| > 8 | Adjust tire pressure | MEDIUM | $10 |
| engine_temp > 110°C | Check coolant system | CRITICAL | $150 |
| engine_temp > 100°C | Monitor engine temperature | HIGH | $50 |
| fuel_eff < 15 km/L | Inspect injectors + air filter | MEDIUM | $120 |
| mileage > 100k & no recs | Full vehicle inspection | LOW | $200 |

#### Accuracy/Confidence Score

```python
rf_conf = max(rf_classifier.predict_proba(X)[0])   # [0.0 – 1.0]
accuracy = min(98.0, 85.0 + rf_conf * 13.0)        # range [85 – 98]%
```

---

## 6. REST API Specification

**Base URL:** `http://localhost:5000`  
**Auth:** Session cookie (`vmps_session`). All `/api/*` routes return `401` if session is absent.

---

### Authentication Routes (`routes/auth.py`)

#### `POST /api/register`
Register a new user.

**Request Body:**
```json
{ "username": "string", "email": "string", "password": "string" }
```
**Responses:**
- `201` — `{ "success": true, "user": { ... } }`
- `400` — `{ "error": "Username or email already exists" }`

---

#### `POST /api/login`
Log in and create a session.

**Request Body:**
```json
{ "email": "string", "password": "string" }
```
**Responses:**
- `200` — `{ "success": true, "username": "string" }`
- `401` — `{ "error": "Invalid credentials" }`

---

#### `POST /api/logout`
Destroy the session.

**Responses:**
- `200` — `{ "success": true }`

---

### Vehicle Routes (`routes/api.py`)

#### `GET /api/vehicles`
List all vehicles belonging to authenticated user.

**Response:**
```json
{
  "vehicles": [
    {
      "id": 1,
      "vehicle_number": "MH-01-AB-1234",
      "vehicle_model": "Model S",
      "manufacturer": "Tesla",
      "mileage": 45000,
      "engine_temp": 88.0,
      "oil_quality": 82.0,
      "tire_pressure": 33.0,
      "brake_condition": 79.0,
      "battery_health": 91.0,
      "fuel_efficiency": 35.0,
      "service_history": 4,
      "last_service_date": "2024-11-15",
      "created_at": "2026-05-14T12:00:00"
    }
  ]
}
```

---

#### `POST /api/vehicles`
Add a new vehicle and auto-run ML prediction.

**Request Body:** Vehicle telemetry fields (see schema).  
**Response:** `201` — `{ "success": true, "vehicle": {...}, "prediction": {...} }`

---

#### `GET /api/vehicles/<id>`
Get single vehicle by ID.

---

#### `PUT /api/vehicles/<id>`
Update vehicle telemetry fields.

---

#### `DELETE /api/vehicles/<id>`
Delete vehicle and cascade to predictions + alerts.

---

### Prediction Routes

#### `POST /api/vehicles/<id>/predict`
Run ML analysis on a saved vehicle.

**Response:**
```json
{
  "prediction": {
    "health_score": 91.2,
    "maintenance_required": false,
    "risk_level": "LOW",
    "urgency": "LOW",
    "failure_component": "All Systems Normal",
    "failure_code": 0,
    "recommendations": [
      { "icon": "✅", "action": "Vehicle is in excellent condition.", "priority": "INFO", "cost": 0 }
    ],
    "estimated_cost": 0.0,
    "accuracy": 97.3,
    "maintenance_probability": 8.4,
    "models_used": ["Random Forest", "Gradient Boosting", "Decision Tree"]
  }
}
```

---

#### `POST /api/predict/quick`
Run prediction on form data without a pre-existing vehicle record (creates vehicle in DB).

---

#### `GET /api/vehicles/<id>/predictions`
Get last 20 predictions for a vehicle (descending chronological).

---

### Dashboard Route

#### `GET /api/dashboard`
Returns fleet-wide KPI summary.

**Response:**
```json
{
  "total_vehicles": 4,
  "avg_health": 67.3,
  "critical_count": 2,
  "ok_count": 2,
  "trend": {
    "health": [85.0, 84.1, ...],
    "engine": [88.2, 91.0, ...],
    "battery": [80.5, 79.3, ...],
    "fuel": [30.1, 28.7, ...]
  },
  "risk_distribution": { "LOW": 1, "MEDIUM": 1, "HIGH": 1, "CRITICAL": 1 }
}
```

---

### Alert Routes

#### `GET /api/alerts`
Get last 20 alerts for the authenticated user's vehicles.

#### `POST /api/alerts/<id>/read`
Mark alert as read.

---

### Report Route

#### `GET /api/vehicles/<id>/report`
Download a PDF maintenance report for a vehicle.

**Response:** Binary PDF (`application/pdf`)  
**Content-Disposition:** `attachment; filename=VMPS_Report_<VehicleNumber>.pdf`

---

### Chatbot Route

#### `POST /api/chatbot`
Send a message to the AI maintenance assistant.

**Request Body:** `{ "message": "string" }`  
**Response:** `{ "reply": "string", "timestamp": "ISO string" }`

---

## 7. Frontend Architecture

### File Structure

```
templates/
  ├── index.html       # Main dashboard (authenticated)
  └── login.html       # Login / registration page

static/
  ├── js/
  │   └── particles.js # Canvas particle animation engine
  └── css/             # (inline styles in HTML templates)
```

### Dashboard Layout (`index.html`)

```
┌─────────────────────────────────────────────────────────────┐
│  VMPS HEADER (holographic logo, nav, user badge, logout)    │
├───────────────────────────┬─────────────────────────────────┤
│  LEFT PANEL               │  RIGHT PANEL                    │
│  ┌─────────────────────┐  │  ┌──────────────────────────┐   │
│  │ Add Vehicle Form    │  │  │ KPI Tiles (4 cards)      │   │
│  │ (9 telemetry inputs)│  │  └──────────────────────────┘   │
│  └─────────────────────┘  │  ┌──────────────────────────┐   │
│  ┌─────────────────────┐  │  │ Line Chart (health trend)│   │
│  │ Vehicle List Cards  │  │  └──────────────────────────┘   │
│  │ (health gauge,      │  │  ┌──────────────────────────┐   │
│  │  risk badge,        │  │  │ Doughnut (risk distrib.) │   │
│  │  action buttons)    │  │  └──────────────────────────┘   │
│  └─────────────────────┘  │  ┌──────────────────────────┐   │
│                           │  │ Alert Feed               │   │
│                           │  └──────────────────────────┘   │
│                           │  ┌──────────────────────────┐   │
│                           │  │ AI Chatbot               │   │
│                           │  └──────────────────────────┘   │
└───────────────────────────┴─────────────────────────────────┘
```

### Key JavaScript Modules (inline in `index.html`)

| Function | Purpose |
|----------|---------|
| `loadDashboard()` | Fetch `/api/dashboard`, update KPIs + charts |
| `loadVehicles()` | Fetch `/api/vehicles`, render vehicle cards |
| `renderVehicleCard(v, pred)` | Build vehicle card HTML with gauge + badges |
| `drawGauge(canvas, score)` | Canvas-based radial health gauge |
| `analyzeVehicle()` | POST to `/api/predict/quick`, show results modal |
| `deleteVehicle(id)` | DELETE vehicle, refresh list |
| `loadAlerts()` | Fetch `/api/alerts`, render alert feed |
| `sendChatMessage()` | POST to `/api/chatbot`, append chat bubble |
| `initCharts()` | Initialise Chart.js line + doughnut charts |
| `updateCharts(data)` | Update charts with fresh dashboard data |

### CSS Design Tokens

```css
/* Core palette */
--bg-primary:     #0a0f1e;   /* Deep navy */
--bg-secondary:   #0d1426;
--accent-cyan:    #00d4ff;   /* Primary neon */
--accent-purple:  #8b5cf6;   /* Secondary neon */
--accent-green:   #00ff88;
--accent-orange:  #ff6b35;

/* Glass cards */
--glass-bg:       rgba(13, 20, 38, 0.8);
--glass-border:   rgba(0, 212, 255, 0.2);
--glass-blur:     blur(20px);

/* Typography */
--font-display:   'Orbitron', monospace;
--font-body:      'Rajdhani', sans-serif;
```

---

## 8. Authentication & Security

### Password Storage
- Hashed using **Werkzeug** `generate_password_hash()` — PBKDF2 with SHA-256, 260,000 iterations by default.
- Verification via `check_password_hash()` — constant-time comparison.

### Session Management
- Flask **server-side session** backed by a signed cookie (`SECRET_KEY` in `.env`).
- Cookie flags: `SameSite=Lax`, `HttpOnly` (Flask default).
- `session['user_id']` and `session['username']` stored on successful login.
- `session.clear()` on logout.

### API Authorization Pattern
```python
def get_current_user_id():
    return session.get('user_id')   # Returns None if unauthenticated

# Applied to every API endpoint:
user_id = get_current_user_id()
if not user_id:
    return jsonify({'error': 'Unauthorized'}), 401
```

### Data Isolation
All DB queries are scoped to `user_id`:
```python
Vehicle.query.filter_by(user_id=user_id)
```
Prevents cross-user data access.

### CORS
Flask-CORS configured with `supports_credentials=True` to allow session cookies from same-origin frontend.

---

## 9. PDF Generation

**Library:** ReportLab 4.2.2  
**Route:** `GET /api/vehicles/<id>/report`

### Document Structure

1. **Title block** — Product name + generation timestamp
2. **Vehicle Information Table** — 12-row two-column table (Field / Value)
3. **AI Prediction Results Table** — Health score, maintenance flag, risk level, urgency, failure component, cost, accuracy
4. **Recommended Actions** — Bullet list with priority and estimated cost per action

### Styling
- Title: `#00d4ff` (cyan) / 20pt
- Section headings: `#8b5cf6` (purple) / 14pt
- Table headers: dark background (`#0a0f1e`) with neon text
- Row alternation: white / light grey

### Fallback Handling
If `reportlab` is not installed, returns:
```json
{ "error": "ReportLab not installed. Run: pip install reportlab" }
```
with HTTP `500`.

---

## 10. Configuration & Environment

### `config.py`

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'vmps-2095-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///vehicle_maintenance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
```

### `.env` (example)

```env
SECRET_KEY=your-production-secret-key-here
DATABASE_URL=sqlite:///vehicle_maintenance.db
DEBUG=True
```

> [!WARNING]
> Never commit `.env` to version control. The `.env` file is included in `.gitignore`.

### Database Location

SQLite database is stored at:
```
instance/vehicle_maintenance.db
```
(Flask `instance/` folder — auto-created by SQLAlchemy on first run.)

---

## 11. Project Structure

```
Sameerr/
├── app.py                    # Application factory + demo seeder
├── config.py                 # Environment-based configuration
├── requirements.txt          # Python dependencies
├── start.bat                 # Windows quick-start script
├── .env                      # Local environment variables (git-ignored)
│
├── models/
│   ├── __init__.py
│   ├── vehicle_model.py      # SQLAlchemy ORM models (User, Vehicle, Prediction, Alert)
│   └── ml_engine.py          # VehicleMLEngine — training + inference
│
├── routes/
│   ├── __init__.py
│   ├── auth.py               # /api/register, /api/login, /api/logout
│   └── api.py                # All vehicle, prediction, alert, dashboard, chatbot routes
│
├── templates/
│   ├── index.html            # Glassmorphism dashboard
│   └── login.html            # Login / registration page
│
├── static/
│   └── js/
│       └── particles.js      # Canvas particle animation system
│
├── instance/
│   └── vehicle_maintenance.db  # SQLite database (auto-created)
│
└── docs/
    ├── PRD.md                # Product Requirements Document
    └── TRD.md                # This document
```

---

## 12. Dependencies

### Python (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `flask` | 3.0.3 | Web framework |
| `flask-cors` | 4.0.1 | Cross-Origin Resource Sharing |
| `flask-sqlalchemy` | 3.1.1 | ORM for SQLite |
| `flask-login` | 0.6.3 | Session utilities |
| `flask-bcrypt` | 1.0.1 | (Available; auth uses Werkzeug hashing) |
| `scikit-learn` | 1.5.0 | Random Forest, GBM, Decision Tree |
| `numpy` | 1.26.4 | Numerical arrays |
| `pandas` | 2.2.2 | Data utilities |
| `python-dotenv` | 1.0.1 | `.env` loader |
| `Werkzeug` | 3.0.3 | WSGI utilities + password hashing |
| `reportlab` | 4.2.2 | PDF report generation |

### Frontend (CDN, no npm required)

| Library | Source | Purpose |
|---------|--------|---------|
| Chart.js 4.x | `cdn.jsdelivr.net` | Interactive charts |
| Google Fonts: Orbitron | `fonts.googleapis.com` | Display typography |
| Google Fonts: Rajdhani | `fonts.googleapis.com` | Body typography |

---

## 13. Deployment Guide

### Local Development

```bash
# 1. Clone / navigate to project
cd Sameerr

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

App runs at **http://localhost:5000**  
Demo credentials: `admin@vmps.ai` / `admin123`

### Windows Quick Start

Double-click `start.bat` — activates venv (if present), installs dependencies, and launches Flask.

### Production (Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

> [!IMPORTANT]
> For production, set `DEBUG=False` and use a strong, unique `SECRET_KEY` in `.env`. Consider migrating from SQLite to PostgreSQL for multi-user deployments beyond 500 vehicles.

---

## 14. Known Limitations & Future Work

| Area | Current Limitation | Recommended Improvement |
|------|--------------------|------------------------|
| **ML Training Data** | Synthetic dataset (5,000 samples) | Replace with real OBD-II telemetry data |
| **ML Retraining** | Models retrain from scratch on every app start | Persist trained models with `joblib` / `pickle` |
| **Database** | SQLite — single-file, no concurrency | Migrate to PostgreSQL for production |
| **Health Trends** | Randomly generated mock data | Compute from real historical `predictions` table |
| **Chatbot** | Simple keyword matching | Integrate LLM API (GPT-4o / Gemini) |
| **Authentication** | No password reset / email verification | Add SMTP-based password recovery |
| **Session Storage** | Server-side cookie (single process) | Use Redis-backed session for multi-worker |
| **Mobile UI** | Not optimised for mobile | Add responsive breakpoints / PWA support |
| **Alerting** | In-app alerts only | Add email / SMS push notifications |
| **API Auth** | Session-based only | Add JWT support for external API consumers |

---

*End of Technical Requirements Document*

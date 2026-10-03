# AI-Based Blood Donor Availability Prediction and Intelligent Matching System

A B.Tech Artificial Intelligence & Data Science student project.

> ⚠️ **This is a demonstration / academic project.** It uses 100% synthetic
> (fictional) data, does not provide medical advice, does not make final
> donor-eligibility decisions, and does not replace doctors, hospitals, or
> blood banks. See [Ethical & Privacy Considerations](#ethical--privacy-considerations).

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Objectives](#objectives)
3. [Features](#features)
4. [Architecture](#architecture)
5. [Technology Stack](#technology-stack)
6. [Dataset Description](#dataset-description)
7. [ML Methodology](#ml-methodology)
8. [Model Evaluation](#model-evaluation)
9. [Database Setup](#database-setup)
10. [Installation (Windows + VS Code)](#installation-windows--vs-code)
11. [Environment Variables](#environment-variables)
12. [Running the Application](#running-the-application)
13. [API Documentation](#api-documentation)
14. [Project Structure](#project-structure)
15. [Demo Flow (5-10 minutes)](#demo-flow-5-10-minutes)
16. [Testing](#testing)
17. [Limitations](#limitations)
18. [Future Enhancements](#future-enhancements)
19. [Ethical & Privacy Considerations](#ethical--privacy-considerations)
20. [Project Documentation](#project-documentation)

---

## Problem Statement

During a blood emergency, a hospital or patient usually already knows the
required blood group. The harder, more time-critical problem is: **which
eligible donors are actually likely to be available and respond quickly?**
A simple donor directory/search is not enough - it doesn't tell a
coordinator who to call *first*.

## Objectives

- Predict the **probability that a given donor will respond** to a given
  emergency blood request, using a trained ML model.
- Combine that probability with blood-group compatibility, distance,
  historical behaviour, current availability, and request urgency into a
  single, **configurable, intelligent ranking score**.
- Provide a complete, runnable, end-to-end system (data → ML → API → UI)
  that a hospital coordinator could interact with in a demo setting.
- Do all of this **without using any real donor's personal data**.

## Features

- Synthetic dataset generator (6,000+ donors, 1,200+ historical emergency
  requests, 30,000+ simulated donor responses) - reproducible via a fixed
  random seed.
- Full ML pipeline: Logistic Regression, Random Forest, and XGBoost
  candidates, compared on Accuracy/Precision/Recall/F1/ROC-AUC, with the
  best model selected by ROC-AUC and probability-calibrated.
- Isolated, documented **blood compatibility module** (standard ABO/Rh rules).
- Configurable **eligibility rules** (age, days since last donation, status).
- Configurable, weighted **donor ranking algorithm** (not hard-coded weights).
- Emergency request form with a Leaflet/OpenStreetMap location picker.
- One-click AI matching: compatible donors → eligible donors → ranked list.
- Donor search/filter page with ad-hoc ranking (no request record required).
- Donor management table (browsable, filterable, no contact info exposed).
- Prediction playground page with plain-language factor explanations.
- Dashboard with KPI cards and Chart.js visualisations.
- Analytics page: response rate by blood group/urgency, response-time
  distribution, and the ML model's own evaluation metrics.
- Simulated "Notify Donor" button (no real SMS/email is ever sent).
- Simple demo admin login (bcrypt-hashed password, signed session cookie).
- User-friendly error handling across the API (400/404/422/500 all return
  clean JSON messages instead of stack traces).
- Automated test suite (pytest) covering compatibility, distance,
  eligibility, ranking, ML inference, and API endpoints.

## Architecture

```
                    ┌─────────────────────────┐
                    │   Browser (Bootstrap +   │
                    │   vanilla JS + Chart.js  │
                    │   + Leaflet/OSM)         │
                    └────────────┬─────────────┘
                                 │ HTTP (JSON + HTML)
                    ┌────────────▼─────────────┐
                    │       FastAPI app         │
                    │  routes/ (donors, requests│
                    │  match, predict, dashboard│
                    │  notify, auth, pages)     │
                    └──┬───────────┬────────────┘
                       │           │
        ┌──────────────▼───┐   ┌───▼─────────────────┐
        │  services/        │   │  app/ml/            │
        │  compatibility.py │   │  predict_service.py │
        │  eligibility.py   │   │      │              │
        │  distance.py      │   │      ▼              │
        │  ranking.py       │   │  ml/predict.py       │
        │  notification.py  │   │  ml/features.py      │
        └──────────────┬───┘   │  models/trained_model│
                       │       │      .joblib          │
        ┌──────────────▼───────┴──────┐
        │   SQLAlchemy ORM (models/)  │
        │   SQLite (default) /        │
        │   PostgreSQL (optional)     │
        └──────────────────────────────┘
                       ▲
                       │  seeded from
        ┌──────────────┴───────────────┐
        │ data/raw/*.csv (synthetic,   │
        │ generated by                 │
        │ ml/generate_dataset.py)      │
        └───────────────────────────────┘
```

**Data flow for an emergency request:**

1. User submits a request (blood group, units, urgency, location) via
   `/request` → `POST /api/requests`.
2. `POST /api/match/{request_id}` is called:
   a. `services/compatibility.py` finds blood-compatible donor groups.
   b. `services/eligibility.py` filters to "potentially eligible" donors
      using configurable demo rules.
   c. `services/distance.py` computes haversine distance to each donor.
   d. `app/ml/predict_service.py` calls the trained model for each
      candidate's response probability.
   e. `services/ranking.py` combines all signals into a single 0-100
      overall score using configurable weights.
   f. Results are persisted to the `matches` table and returned, ranked.
3. The UI renders the ranked table with a "Notify Donor" button
   (simulated - see [Ethical & Privacy Considerations](#ethical--privacy-considerations)).

## Technology Stack

| Layer          | Technology                                              |
|----------------|----------------------------------------------------------|
| Backend        | Python 3.11+, FastAPI, Uvicorn                          |
| ML             | Pandas, NumPy, Scikit-learn, XGBoost, Joblib             |
| Database       | SQLite (default, zero setup) or PostgreSQL (via SQLAlchemy) |
| Frontend       | HTML, CSS, JavaScript, Bootstrap 5                       |
| Visualization  | Chart.js                                                 |
| Maps           | Leaflet + OpenStreetMap tiles (no paid API, no credit card) |
| Auth           | bcrypt password hashing + signed session cookies         |
| Testing        | Pytest, FastAPI TestClient                               |

## Dataset Description

All data is **synthetic and fictional**, generated by
`ml/generate_dataset.py` with a fixed random seed (42) for reproducibility.

| File                          | Rows (default) | Description |
|--------------------------------|----------------|--------------|
| `data/raw/donors.csv`          | 6,000          | Fictional donor master records |
| `data/raw/donation_history.csv`| ~24,000        | Past donation events per donor |
| `data/raw/emergency_requests.csv` | 1,200       | Historical emergency blood requests |
| `data/raw/donor_response_history.csv` | ~30,000 | Simulated donor responses to requests (ML training source) |

`donors.csv` columns: `donor_id, name, age, gender, blood_group, city,
latitude, longitude, last_donation_date, total_donations,
previous_requests_received, previous_requests_responded,
average_response_time_minutes, availability_preference,
current_availability, donor_status`.

To regenerate with a different size:

```bash
python ml/generate_dataset.py --donors 8000 --requests 1500
```

## ML Methodology

**Target variable:** `will_respond` (1 = donor responded to the emergency
request in the simulated history, 0 = did not).

**Features used:** age, total donations, previous requests received, previous
response rate, average historical response time, current availability,
distance to the request (km), urgency (ordinal), units required, hour of
day, day of week, and whether the donor is blood-group O- (the universal
donor - a clinically relevant, non-sensitive fact).

**Pipeline (`ml/train.py`):**

1. Load and join `donors.csv`, `emergency_requests.csv`, and
   `donor_response_history.csv`.
2. Clean data / handle missing values.
3. Feature engineering (`ml/features.py` - shared between training and
   inference so both use identical transformations).
4. Stratified 80/20 train/test split (the label is imbalanced).
5. Train three candidate models: Logistic Regression, Random Forest, XGBoost.
6. Evaluate each with Accuracy, Precision, Recall, F1, ROC-AUC, and a
   confusion matrix.
7. Select the best model **by ROC-AUC**, not raw accuracy.
8. Calibrate the winning model's probabilities (Platt/sigmoid scaling via
   `CalibratedClassifierCV`).
9. Save the calibrated pipeline with Joblib + a `model_metadata.json`
   file recording every metric.

### Why not just optimise for accuracy?

Because most donor/request pairs in the simulated history do **not** end
in a response, a model that always predicts "will not respond" could
still score a deceptively high accuracy while being completely useless
for prioritisation. Instead:

- **Recall** matters because missing a donor who would have responded
  could cost time in a real emergency.
- **Precision** matters because a coordinator needs to trust a "likely to
  respond" label before spending effort contacting that donor.
- **ROC-AUC** matters because the ranking module uses the raw probability
  score directly (not a single threshold), so we need a model that ranks
  donors well across all thresholds.
- **Calibration** matters because the ranking formula treats the model's
  output as a genuine 0-1 probability and blends it with other 0-1
  factors (distance, response rate, etc.) - a well-calibrated score keeps
  that blend meaningful, not just well-ordered.

## Model Evaluation

Metrics from a representative training run (yours may vary slightly due
to sampling, but should be broadly similar since the data generator uses
a fixed seed):

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | 0.70 | 0.87 | 0.70 | 0.78 | 0.78 |
| Random Forest | 0.73 | 0.86 | 0.74 | 0.80 | 0.79 |
| XGBoost | 0.72 | 0.87 | 0.73 | 0.79 | 0.79 |
| **Random Forest (calibrated, selected)** | 0.77 | 0.80 | 0.92 | 0.86 | 0.79 |

The three candidates are extremely close on ROC-AUC (0.78-0.79), so which one
is selected as "best" can vary slightly between training runs/environments -
this is expected and fine; the calibration and ranking logic work the same
regardless of which candidate wins. Your own run may select XGBoost instead
of Random Forest, for example - check `models/model_metadata.json` and the
Analytics page for the exact numbers from your run.

Exact numbers are saved to `models/model_metadata.json` after every
training run and are also displayed live on the **Analytics** page.

## Database Setup

The project defaults to **SQLite** so it runs with zero database setup.
The database layer is built on SQLAlchemy and is fully modular, so
switching to PostgreSQL later only requires changing environment
variables - no code changes.

### Tables

`donors`, `donation_history`, `emergency_requests`, `donor_responses`,
`matches`, `admin_users`, `prediction_logs`, `notification_logs`.

See `app/models/db_models.py` for the full SQLAlchemy schema (primary
keys, foreign keys, indexes). Key relationships:

- `donors.donor_id` ← referenced by `donation_history`, `donor_responses`,
  `matches` (one donor → many donations/responses/matches).
- `emergency_requests.request_id` ← referenced by `donor_responses`,
  `matches` (one request → many responses/matches).

**ER diagram (description):**

```
donors (1) ───< donation_history (many)
donors (1) ───< donor_responses (many) >─── (1) emergency_requests
donors (1) ───< matches (many) >─── (1) emergency_requests
admin_users (standalone - demo login)
prediction_logs (standalone - audit log of every /api/predict call)
notification_logs (standalone - audit log of every simulated notify)
```

### Using PostgreSQL instead of SQLite (optional)

1. Install PostgreSQL and create a database, e.g. `blood_donor_ai`.
2. `pip install psycopg2-binary` (uncomment the line in `requirements.txt`).
3. In your `.env` file, set:
   ```
   DB_MODE=postgresql
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=blood_donor_ai
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=<your password>
   ```
4. Run the app as normal - tables are created automatically on startup.

## Installation (Windows + VS Code)

```bash
# 1. Check Python is installed (3.11+ recommended)
python --version

# 2. Clone / open the project folder in VS Code, then open a terminal:
cd blood-donor-ai

# 3. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy the environment template
copy .env.example .env

# 6. Generate the synthetic dataset
python ml\generate_dataset.py

# 7. Train the ML model
python ml\train.py

# 8. Start the application
python run.py
```

Then open **http://127.0.0.1:8000** in your browser.

(macOS/Linux users: use `source venv/bin/activate` in step 3 and
`python ml/generate_dataset.py` with forward slashes.)

## Environment Variables

See `.env.example` for the full list. Defaults work out of the box for
SQLite. Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DB_MODE` | `sqlite` | `sqlite` or `postgresql` |
| `SQLITE_PATH` | `./data/processed/blood_donor.db` | SQLite file location |
| `SECRET_KEY` | demo value | Used to sign session cookies |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / `admin123` | Demo admin account created on first run |

## Running the Application

```bash
python run.py
```

This starts Uvicorn on `http://127.0.0.1:8000` with auto-reload enabled.
On first run, the app automatically creates database tables and loads
the synthetic CSV data (you only need to generate the CSVs once with
`ml/generate_dataset.py`).

## API Documentation

Interactive Swagger docs are auto-generated by FastAPI at
**http://127.0.0.1:8000/docs** once the server is running.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/blood-groups` | List valid blood groups |
| GET | `/api/donors` | List/filter donors |
| GET | `/api/donors/{donor_id}` | Get one donor |
| POST | `/api/requests` | Create an emergency request |
| GET | `/api/requests` | List requests (filter by status/urgency) |
| GET | `/api/requests/{request_id}` | Get one request |
| POST | `/api/match/{request_id}` | Run AI matching for a request (persists results) |
| GET | `/api/search-donors` | Ad-hoc ranked donor search (no request record needed) |
| POST | `/api/predict` | Standalone response-probability prediction |
| GET | `/api/dashboard/stats` | Dashboard KPI + chart data |
| GET | `/api/dashboard/analytics` | Deeper analytics + model metrics |
| POST | `/api/notify/{donor_id}` | Simulated donor notification |
| POST | `/api/login` / `/api/logout` / `/api/me` | Demo admin auth |

## Project Structure

```text
blood-donor-ai/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, error handlers
│   ├── config.py                # Environment-driven configuration
│   ├── database.py               # SQLAlchemy engine/session
│   ├── seed.py                   # Loads CSVs into DB on first run
│   ├── models/db_models.py       # ORM models (8 tables)
│   ├── schemas/schemas.py        # Pydantic request/response schemas
│   ├── routes/                   # donors, requests, match, predict,
│   │                             # dashboard, notify, auth, pages
│   ├── services/                 # compatibility, eligibility, distance,
│   │                             # ranking, notification (+ JSON configs)
│   ├── ml/predict_service.py     # Thin FastAPI-facing wrapper over ml/
│   ├── utils/security.py         # Password hashing + session tokens
│   └── templates/                # Jinja2 HTML pages (Bootstrap)
├── static/
│   ├── css/style.css
│   └── js/                       # per-page JS + shared helpers
├── data/
│   ├── raw/                      # generated synthetic CSVs
│   └── processed/                # SQLite DB file lives here
├── ml/
│   ├── generate_dataset.py       # synthetic data generator
│   ├── features.py               # shared feature engineering
│   ├── train.py                  # training pipeline
│   └── predict.py                # framework-agnostic inference
├── models/
│   ├── trained_model.joblib      # saved calibrated model
│   └── model_metadata.json       # metrics + feature list
├── tests/                        # pytest suite (54 tests)
├── requirements.txt
├── .env.example
├── run.py
└── README.md
```

## Demo Flow (5-10 minutes)

1. **Dashboard** (`/`) - point out the KPI cards (total donors, available
   now, active/critical requests) and the blood-group / availability /
   urgency charts. Mention all data is synthetic.
2. **Emergency Request** (`/request`) - fill in a request (e.g. O+, 2
   units, Critical, click a point on the map near "Coimbatore Central").
   Submit it. Show the automatically-generated ranked donor table and
   explain the columns (distance, response probability, expected speed,
   overall score). Click "Notify Donor" on the top result and show it
   flips to "Notified ✓" (explain this is simulated, no real message sent).
3. **Find Donors** (`/search`) - show the same ranking engine used ad-hoc:
   change the blood group, drag the distance slider, toggle "available
   only", and re-run the search to show the ranking changing live.
4. **Prediction** (`/predict`) - manually enter donor characteristics
   (e.g. high previous response rate, low distance, available) and show
   the probability output plus the plain-language contributing factors.
   Then flip a couple of values (far away, unavailable) and re-predict to
   show the probability drop.
5. **Donor Management** (`/donors`) - filter donors by blood group/city to
   show the underlying donor database, noting no contact info is shown.
6. **Request History** (`/history`) - show historical requests and their
   statuses; click "View Matches" on one to jump back into `/search`.
7. **Analytics** (`/analytics`) - show response rate by blood group and
   urgency, the response-time distribution, and the ML model's own
   evaluation metrics (accuracy/precision/recall/F1/ROC-AUC) pulled
   straight from the last training run.
8. **About** (`/about`) - wrap up by reading the "What this system does
   NOT do" section aloud - this is a good place to address questions
   about medical liability and data privacy from evaluators.

## Testing

```bash
pytest tests/ -v
```

54 tests covering: blood compatibility rules, haversine distance
calculations, eligibility filtering, the ranking algorithm, ML inference
(skipped gracefully if you haven't run `ml/train.py` yet), and full API
integration tests (donor/request CRUD, matching, prediction, dashboard
stats, auth, error handling, and all 9 HTML pages) - run against an
isolated, throwaway SQLite database so your real demo data is never
touched by the test suite.

## Limitations

- Distance is a straight-line ("as the crow flies") haversine calculation,
  not real road/travel time.
- The "eligibility" layer applies simple, configurable demo rules only -
  it is not a substitute for a blood bank's actual medical screening.
- The synthetic dataset's realism is limited by the assumptions in
  `ml/generate_dataset.py`; a real deployment would need real
  (privacy-compliant, consented) historical data.
- "Notify Donor" is fully simulated - no SMS/email/push integration is
  included, and none should be added without proper consent flows and a
  licensed provider.
- The demo admin login is intentionally simple and is not hardened for
  production (no rate limiting, no CSRF protection, no HTTPS enforcement).

## Future Enhancements

- Blood demand forecasting (time-series model per blood group) as an
  additional, separate module.
- SHAP-based feature importance visualisations on the Prediction page.
- Real-time notifications via a licensed SMS/push provider, with donor
  opt-in/consent management.
- Role-based access control (hospital staff vs. blood bank vs. admin).
- Integration with real (authorized, consented) blood bank inventory systems.
- Road-network-based ETA instead of straight-line distance.

## Ethical & Privacy Considerations

- **No real personal data** is used anywhere in this project. All donor
  names, locations, ages, and histories are synthetically generated by
  `ml/generate_dataset.py` using a fixed random seed - none of it refers
  to real people.
- The system **never exposes donor contact information** through the UI
  or API.
- "Notify Donor" is a **simulated** action only - clicking it records an
  entry in the `notification_logs` table but sends no real message.
- All AI outputs are framed as **probabilistic estimates for
  prioritisation/assistance only** - never as guarantees of donor
  behaviour, and every match result carries an explicit disclaimer.
- The eligibility module **never makes a final medical decision** - every
  result is labelled "potentially eligible based on configured demo
  rules; medical eligibility must be confirmed by the blood bank."
- A real-world deployment of a system like this would require: clinical
  validation, informed consent from donors, strict data-privacy controls
  (e.g. India's DPDP Act / HIPAA-equivalent regulations depending on
  jurisdiction), security auditing, and integration with authorized
  healthcare systems and blood banks - none of which are in scope for
  this academic demo.

## Project Documentation

### Abstract

Blood emergencies require fast identification of donors who are not just
compatible, but *likely to respond in time*. This project presents an
AI-based system that predicts a donor's probability of responding to a
specific emergency blood request and combines that prediction with
blood-group compatibility, geographic distance, historical behaviour, and
request urgency into a single, configurable ranking score. The system is
implemented as a full-stack FastAPI + Bootstrap application backed by a
calibrated XGBoost classifier, trained entirely on a reproducible,
synthetic dataset to avoid any real personal data.

### Existing System

Most existing blood-donor platforms are essentially searchable directories
filtered by blood group and location. They do not account for the
likelihood that a matched donor will actually respond, leaving hospital
staff to contact donors in an arbitrary or purely distance-based order,
which can waste critical time during emergencies.

### Proposed System

The proposed system adds a machine-learning layer on top of a standard
compatibility/eligibility/distance pipeline: a calibrated classifier
predicts each compatible, eligible donor's probability of responding, and
a transparent, configurable ranking formula combines that probability
with distance, historical reliability, current availability, and
request urgency to produce a single prioritised list for hospital staff.

### Methodology

See [ML Methodology](#ml-methodology) above for the full pipeline
(data generation → cleaning → feature engineering → model comparison →
calibration → persistence → API integration).

### System Architecture

See [Architecture](#architecture) above.

### Modules

Blood Compatibility, Donor Eligibility, Distance Calculation, ML
Prediction, Intelligent Ranking, Emergency Request Management, Donor
Search/Management, Notification (simulated), Dashboard/Analytics,
Authentication.

### Dataset

See [Dataset Description](#dataset-description) above.

### Algorithms

Logistic Regression, Random Forest, and XGBoost were compared; the
best-performing model by ROC-AUC (typically XGBoost in this dataset) was
selected and probability-calibrated using Platt/sigmoid scaling.

### Results

See [Model Evaluation](#model-evaluation) above - the calibrated model
achieves ROC-AUC ≈ 0.79 and recall ≈ 0.92 on held-out synthetic test data.

### Advantages

- Goes beyond simple filtering to a genuine likelihood-based
  prioritisation of donors.
- Fully transparent, configurable ranking weights (no hidden "black box"
  scoring).
- Zero-setup local development (SQLite by default) with a clear path to
  PostgreSQL for larger deployments.
- No real personal data used anywhere in the demo.

### Limitations

See [Limitations](#limitations) above.

### Future Scope

See [Future Enhancements](#future-enhancements) above.

### Conclusion

This project demonstrates how a machine-learning response-prediction
model can be combined with rule-based compatibility, eligibility, and
distance logic to build a more intelligent blood-donor matching system
than a simple directory search - while being explicit, at every step,
that its outputs are probabilistic aids for human decision-makers, not
replacements for medical judgement.

"""
main.py
=======
FastAPI application entrypoint. Wires together the database, routes, and
static/template file serving. Run via `python run.py` from the project root.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db, SessionLocal
from app import seed
from app.routes import donors, requests, match, predict, dashboard, notify, auth, pages

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    init_db()
    db = SessionLocal()
    try:
        seed.seed_if_empty(db)
    finally:
        db.close()
    yield
    # --- shutdown (nothing to clean up in this demo) ---


app = FastAPI(
    title="AI-Based Blood Donor Availability Prediction and Intelligent Matching System",
    description=(
        "A student/demo project. This system does NOT provide medical advice, "
        "does NOT determine final donor eligibility, and does NOT replace doctors, "
        "hospitals, or blood banks. All predictions are probabilistic estimates for "
        "prioritisation/assistance only. All data is synthetic/demo data."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---- Error handling: user-friendly JSON error messages ----

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    raise exc


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic v2 error dicts can include a raw exception object under
    # "ctx" (for custom validators that raise ValueError) which is not
    # JSON serializable - convert it to a plain string before returning.
    safe_errors = []
    for err in exc.errors():
        err = dict(err)
        ctx = err.get("ctx")
        if isinstance(ctx, dict) and "error" in ctx:
            err["ctx"] = {**ctx, "error": str(ctx["error"])}
        safe_errors.append(err)
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request data", "details": safe_errors},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(exc)}"})
    raise exc


# ---- Static files ----
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ---- API routes ----
app.include_router(donors.router)
app.include_router(requests.router)
app.include_router(match.router)
app.include_router(predict.router)
app.include_router(dashboard.router)
app.include_router(notify.router)
app.include_router(auth.router)

# ---- HTML page routes ----
app.include_router(pages.router)

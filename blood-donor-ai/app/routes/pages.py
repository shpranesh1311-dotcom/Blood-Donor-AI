"""
routes/pages.py
================
Serves the server-rendered HTML pages (Bootstrap + vanilla JS frontend).
Each page is a thin Jinja2 template shell; all data is fetched client-side
from the JSON API defined in the other route modules.
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(tags=["pages"])

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/")
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"active_page": "dashboard"})


@router.get("/request")
def request_page(request: Request):
    return templates.TemplateResponse(request, "request.html", {"active_page": "request"})


@router.get("/search")
def search_page(request: Request):
    return templates.TemplateResponse(request, "search.html", {"active_page": "search"})


@router.get("/donors")
def donors_page(request: Request):
    return templates.TemplateResponse(request, "donors.html", {"active_page": "donors"})


@router.get("/predict")
def predict_page(request: Request):
    return templates.TemplateResponse(request, "predict.html", {"active_page": "predict"})


@router.get("/history")
def history_page(request: Request):
    return templates.TemplateResponse(request, "history.html", {"active_page": "history"})


@router.get("/analytics")
def analytics_page(request: Request):
    return templates.TemplateResponse(request, "analytics.html", {"active_page": "analytics"})


@router.get("/about")
def about_page(request: Request):
    return templates.TemplateResponse(request, "about.html", {"active_page": "about"})


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"active_page": "login"})

"""
routes/auth.py
===============
Minimal demo admin login. Passwords are hashed with bcrypt; sessions are
simple signed cookies. See app/utils/security.py for details and caveats.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import AdminUser
from app.schemas.schemas import LoginIn
from app.utils.security import verify_password, create_session_token, verify_session_token

router = APIRouter(prefix="/api", tags=["auth"])

SESSION_COOKIE_NAME = "blood_donor_session"


@router.post("/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_session_token(user.username)
    response.set_cookie(key=SESSION_COOKIE_NAME, value=token, httponly=True, max_age=3600 * 8)
    return {"message": "Login successful", "username": user.username}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Logged out"}


@router.get("/me")
def me(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    username = verify_session_token(token) if token else None
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"username": username}

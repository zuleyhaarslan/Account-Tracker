from fastapi import APIRouter, Request, Depends, Form, responses, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import User, Account, UpdateLog
from database.crypto import encrypt_password
from web.auth import hash_password, verify_password, set_auth_cookie, clear_auth_cookie, get_current_user, COOKIE_NAME
from engine.browser_session import remove_session_cookies
import datetime
from pathlib import Path

router = APIRouter()

# Locate the template layout workspace directory folder bounds
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

@router.get("/")
async def root_redirect(request: Request):
    if request.cookies.get(COOKIE_NAME):
        return responses.RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
async def handle_login(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    
    # Simple self-provisioning trick: If zero accounts exist on boot, create the first input user profile automatically
    if not user and db.query(User).count() == 0:
        user = User(username=username, hashed_password=hash_password(password))
        db.add(user)
        db.commit()
    elif not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid localized access combination."})
        
    response = responses.RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    set_auth_cookie(response, user.username)
    return response

@router.get("/logout")
async def handle_logout():
    response = responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    clear_auth_cookie(response)
    return response

@router.get("/dashboard")
async def dashboard_view(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except:
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    accounts = db.query(Account).filter(Account.user_id == user.id).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "accounts": accounts, "user": user})

@router.get("/manage")
async def manage_page(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except:
        return responses.RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("manage.html", {"request": request, "user": user})

@router.post("/accounts/add")
async def add_account(
    request: Request,
    platform_name: str = Form(...),
    target_url: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    
    # Standard security practice: encrypt target passwords at-rest immediately
    encrypted_pwd = encrypt_password(password)
    
    new_account = Account(
        user_id=user.id,
        platform_name=platform_name,
        target_url=target_url,
        username=username,
        encrypted_password=encrypted_pwd
    )
    db.add(new_account)
    db.commit()
    return responses.RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/accounts/{account_id}/clear-badge")
async def clear_badge(account_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user.id).first()
    if account:
        account.has_update = False
        db.commit()
    return responses.RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/accounts/{account_id}/delete")
async def delete_account(account_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user.id).first()
    if account:
        db.delete(account)
        db.commit()
        await remove_session_cookies(account_id)
    return responses.RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
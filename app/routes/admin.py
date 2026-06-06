"""Routes d'administration des utilisateurs.

Toutes les routes sont réservées aux administrateurs (Depends(require_admin)).

GET  /admin/users              → liste des utilisateurs + formulaire d'ajout
POST /admin/users              → créer un utilisateur
POST /admin/users/{id}/delete  → supprimer un utilisateur (sauf soi-même)
POST /admin/users/{id}/toggle  → basculer le rôle admin
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_admin
from app.models.user import User
from app.services.auth import hash_password, validate_password_strength

router = APIRouter(prefix="/admin", tags=["admin"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Page de gestion des utilisateurs (réservée aux admins)."""
    users = session.exec(select(User).order_by(User.created_at)).all()
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {"users": users, "current_user": current_user, "error": None},
    )


@router.post("/users", response_class=HTMLResponse)
def create_user(
    request: Request,
    username:     str  = Form(...),
    display_name: str  = Form(""),
    password:     str  = Form(...),
    is_admin:     bool = Form(False),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Crée un nouvel utilisateur (admin seulement)."""
    username = username.strip().lower()

    errors: list[str] = []
    if len(username) < 3:
        errors.append("L'identifiant doit faire au moins 3 caractères.")

    # Vérification de la robustesse du mot de passe.
    pwd_errors = validate_password_strength(password)
    if pwd_errors:
        errors.append("Mot de passe trop faible — il lui manque : " + ", ".join(pwd_errors) + ".")

    # Vérifier que l'identifiant n'est pas déjà pris.
    if session.exec(select(User).where(User.username == username)).first():
        errors.append(f"L'identifiant « {username} » est déjà utilisé.")

    if errors:
        users = session.exec(select(User).order_by(User.created_at)).all()
        return templates.TemplateResponse(
            request,
            "admin/users.html",
            {"users": users, "current_user": current_user, "error": " ".join(errors)},
            status_code=422,
        )

    new_user = User(
        username=username,
        display_name=display_name.strip() or username,
        hashed_password=hash_password(password),
        is_admin=is_admin,
    )
    session.add(new_user)
    session.commit()

    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{user_id}/delete")
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Supprime un utilisateur. Un admin ne peut pas se supprimer lui-même."""
    if user_id == current_user.id:
        # Refus silencieux : on ne peut pas se supprimer soi-même.
        return RedirectResponse(url="/admin/users", status_code=303)

    user = session.get(User, user_id)
    if user:
        session.delete(user)
        session.commit()

    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Bascule le rôle admin d'un utilisateur (sauf soi-même)."""
    if user_id == current_user.id:
        return RedirectResponse(url="/admin/users", status_code=303)

    user = session.get(User, user_id)
    if user:
        user.is_admin = not user.is_admin
        session.add(user)
        session.commit()

    return RedirectResponse(url="/admin/users", status_code=303)

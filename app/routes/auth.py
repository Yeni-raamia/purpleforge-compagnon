"""Routes d'authentification.

GET  /login          → page de connexion (formulaire)
POST /login          → vérification des identifiants → session → redirection
POST /logout         → destruction de la session → /login
GET  /setup          → page de création du premier compte admin (si aucun user)
POST /setup          → création du compte admin → connexion automatique → /campaigns/
GET  /account        → page de profil / changement de mot de passe
POST /account/password → traitement changement de mot de passe
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_user
from app.models.user import User
from app.services.auth import hash_password, verify_password, validate_password_strength

router = APIRouter(tags=["auth"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ── /login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Affiche la page de connexion."""
    # Si l'utilisateur est déjà connecté, on le redirige directement.
    if request.session.get("user_id"):
        return RedirectResponse(url="/campaigns/", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next_url: str = Form(default=""),
    session: Session = Depends(get_session),
):
    """Vérifie les identifiants ; crée la session en cas de succès."""
    # Recherche de l'utilisateur par son identifiant (insensible à la casse).
    user = session.exec(
        select(User).where(User.username == username.strip().lower())
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"error": "Identifiant ou mot de passe incorrect."},
            status_code=401,
        )

    # Connexion réussie : on enregistre les infos en session (cookie signé).
    request.session["user_id"]  = user.id
    request.session["username"] = user.username

    # On redirige vers l'URL demandée initialement, ou vers les campagnes.
    destination = next_url.strip() or "/campaigns/"
    return RedirectResponse(url=destination, status_code=303)


# ── /logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
def logout(request: Request):
    """Détruit la session et redirige vers /login."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# ── /setup ─────────────────────────────────────────────────────────────────────

@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, session: Session = Depends(get_session)):
    """Page de création du premier compte (accessible seulement s'il n'y a aucun user)."""
    # S'il existe déjà au moins un utilisateur, le setup est désactivé.
    if session.exec(select(User)).first():
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "auth/setup.html", {"error": None})


@router.post("/setup", response_class=HTMLResponse)
def setup(
    request: Request,
    username:     str = Form(...),
    display_name: str = Form(""),
    password:     str = Form(...),
    password2:    str = Form(...),
    session: Session = Depends(get_session),
):
    """Crée le premier administrateur et le connecte automatiquement."""
    # Sécurité : si des utilisateurs existent déjà, on refuse.
    if session.exec(select(User)).first():
        return RedirectResponse(url="/login", status_code=303)

    # Validations.
    errors: list[str] = []
    username = username.strip().lower()
    if len(username) < 3:
        errors.append("L'identifiant doit faire au moins 3 caractères.")

    # Vérification de la robustesse du mot de passe.
    pwd_errors = validate_password_strength(password)
    if pwd_errors:
        errors.append("Mot de passe trop faible — il lui manque : " + ", ".join(pwd_errors) + ".")

    if password != password2:
        errors.append("Les deux mots de passe ne correspondent pas.")

    if errors:
        return templates.TemplateResponse(
            request,
            "auth/setup.html",
            {"error": " ".join(errors)},
            status_code=422,
        )

    # Création du premier administrateur.
    admin = User(
        username=username,
        display_name=display_name.strip() or username,
        hashed_password=hash_password(password),
        is_admin=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)

    # Connexion automatique après la création.
    request.session["user_id"]  = admin.id
    request.session["username"] = admin.username

    return RedirectResponse(url="/campaigns/", status_code=303)


# ── /account ───────────────────────────────────────────────────────────────────

@router.get("/account", response_class=HTMLResponse)
def account_page(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de profil : affiche les infos et le formulaire de changement de mot de passe."""
    return templates.TemplateResponse(
        request,
        "auth/account.html",
        {"current_user": current_user, "success": None, "error": None},
    )


@router.post("/account/password", response_class=HTMLResponse)
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password:     str = Form(...),
    new_password2:    str = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Traite le changement de mot de passe."""

    def render(error=None, success=None, status_code=200):
        return templates.TemplateResponse(
            request,
            "auth/account.html",
            {"current_user": current_user, "error": error, "success": success},
            status_code=status_code,
        )

    # 1. Vérifier l'ancien mot de passe.
    if not verify_password(current_password, current_user.hashed_password):
        return render(error="Mot de passe actuel incorrect.", status_code=401)

    # 2. Robustesse du nouveau mot de passe.
    pwd_errors = validate_password_strength(new_password)
    if pwd_errors:
        return render(
            error="Nouveau mot de passe trop faible — il lui manque : " + ", ".join(pwd_errors) + ".",
            status_code=422,
        )

    # 3. Confirmation.
    if new_password != new_password2:
        return render(error="Les deux nouveaux mots de passe ne correspondent pas.", status_code=422)

    # 4. Mise à jour en base.
    # On recharge l'utilisateur depuis la session DB pour avoir un objet rattaché.
    db_user = session.get(User, current_user.id)
    db_user.hashed_password = hash_password(new_password)
    session.add(db_user)
    session.commit()

    return render(success="Mot de passe modifié avec succès ✓")

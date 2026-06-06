"""Point d'entrée de l'application PurpleForge Compagnon.

Initialise la base de données, le middleware de session et enregistre
toutes les routes au démarrage.
"""

import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database import create_db_and_tables, engine
import app.models  # noqa: F401 — importe User + Campaign + Technique pour create_all
from app.dependencies import NotAuthenticated, NotAdmin
from app.routes import auth       as auth_router
from app.routes import admin      as admin_router
from app.routes import campaigns  as campaigns_router
from app.routes import techniques as techniques_router
from app.routes import dashboard  as dashboard_router
from app.routes import search     as search_router

# ── Chemins ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
SECRET_KEY_FILE = DATA_DIR / ".secret_key"


def _load_or_create_secret() -> str:
    """Charge la clé secrète depuis data/.secret_key, ou en crée une.

    La clé est persistée sur disque pour que les sessions survivent aux
    redémarrages du serveur. Sans ça, chaque relance invaliderait les cookies.
    """
    DATA_DIR.mkdir(exist_ok=True)
    if SECRET_KEY_FILE.exists():
        key = SECRET_KEY_FILE.read_text().strip()
        if key:
            return key
    # Génération d'une clé aléatoire sécurisée (256 bits).
    key = secrets.token_hex(32)
    SECRET_KEY_FILE.write_text(key)
    return key


# ── Lifespan (démarrage / arrêt) ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crée la base SQLite et ses tables au démarrage."""
    create_db_and_tables()
    yield


# ── Création de l'application ──────────────────────────────────────────────────
app = FastAPI(title="PurpleForge Compagnon", lifespan=lifespan)

# ── Session middleware (cookie signé, persistant 7 jours) ─────────────────────
# IMPORTANT : doit être ajouté avant les routes pour que request.session soit
# disponible dans les dépendances et les routes.
app.add_middleware(
    SessionMiddleware,
    secret_key=_load_or_create_secret(),
    session_cookie="purpleforge_session",
    max_age=60 * 60 * 24 * 7,    # 7 jours en secondes
    same_site="lax",
    https_only=False,             # mettre True en production HTTPS
)

# ── Templates et fichiers statiques ───────────────────────────────────────────
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ── Enregistrement des routers ────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(search_router.router)
app.include_router(dashboard_router.router)
app.include_router(campaigns_router.router)
app.include_router(techniques_router.router)


# ── Gestionnaires d'exceptions d'authentification ─────────────────────────────

@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    """Redirige vers /login si l'utilisateur n'est pas connecté.

    Pour les requêtes HTMX, on utilise l'en-tête HX-Redirect (HTMX ne suit
    pas les 303 normaux envoyés en réponse à hx-post/hx-get).
    """
    if request.headers.get("hx-request"):
        return Response(status_code=200, headers={"HX-Redirect": "/login"})
    return Response(status_code=303, headers={"Location": "/login"})


@app.exception_handler(NotAdmin)
async def not_admin_handler(request: Request, exc: NotAdmin):
    """Redirige vers /campaigns/ si l'utilisateur n'est pas admin."""
    if request.headers.get("hx-request"):
        return Response(status_code=200, headers={"HX-Redirect": "/campaigns/"})
    return Response(status_code=303, headers={"Location": "/campaigns/"})


# ── Middleware de redirection setup (premier lancement) ───────────────────────

@app.middleware("http")
async def setup_redirect_middleware(request: Request, call_next):
    """Si aucun utilisateur n'existe, redirige vers /setup.

    Exceptions : les ressources statiques, /setup et /login eux-mêmes
    ne doivent pas être interceptés (boucle infinie sinon).
    """
    path = request.url.path

    # On laisse passer : static, setup, login, favicon.
    bypass = (
        path.startswith("/static")
        or path in ("/setup", "/login")
        or path.startswith("/favicon")
    )
    if bypass:
        return await call_next(request)

    # Vérification rapide : y a-t-il au moins un utilisateur en base ?
    from sqlmodel import Session, select
    from app.models.user import User

    with Session(engine) as db_session:
        has_users = db_session.exec(select(User)).first()

    if not has_users:
        return Response(status_code=303, headers={"Location": "/setup"})

    return await call_next(request)


# ── Page d'accueil ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Page d'accueil publique."""
    return templates.TemplateResponse(request, "home.html")

"""Point d'entrée de l'application PurpleForge Compagnon.

Pour l'instant (Phase 0), il sert une page d'accueil
et initialise la base de données SQLite au démarrage.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import create_db_and_tables
import app.models  # noqa: F401 — importe Campaign + TechniqueEntry pour que create_all les connaisse
from app.routes import campaigns as campaigns_router

# Dossier de base = le dossier "app" où se trouve ce fichier.
# On s'en sert pour retrouver "templates" et "static" de façon fiable,
# quel que soit l'endroit d'où on lance l'appli.
BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Code exécuté au démarrage (avant le yield) et à l'arrêt (après).
    Ici : on crée la base SQLite et ses tables au démarrage.
    """
    create_db_and_tables()  # crée purpleforge.db s'il n'existe pas encore
    yield  # l'appli tourne ici ; à l'arrêt, on passerait le code de nettoyage


# Création de l'application FastAPI, avec le gestionnaire de démarrage/arrêt.
app = FastAPI(title="PurpleForge Compagnon", lifespan=lifespan)

# On branche le moteur de gabarits Jinja2 sur le dossier "app/templates".
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# On expose le dossier "app/static" (CSS, images) à l'URL "/static".
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# On enregistre les routes des campagnes (préfixe /campaigns).
app.include_router(campaigns_router.router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Page d'accueil : affiche le gabarit home.html."""
    # Nouvelle écriture (Starlette récent) : "request" en premier argument,
    # puis le nom du gabarit, puis le contexte (les données passées au gabarit).
    return templates.TemplateResponse(request, "home.html")

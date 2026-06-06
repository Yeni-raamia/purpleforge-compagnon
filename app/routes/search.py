"""Routes de recherche globale.

GET /search?q=...        → page de résultats complète
GET /search/quick?q=...  → fragment HTMX pour le dropdown de la nav
"""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session

from app.database import get_session
from app.dependencies import require_user
from app.models.user import User
from app.services.search import search, highlight

router = APIRouter(tags=["search"])

BASE_DIR  = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# On expose highlight comme filtre Jinja2 pour l'utiliser dans les templates.
templates.env.globals["highlight"] = highlight


@router.get("/search", response_class=HTMLResponse)
def search_page(
    request: Request,
    q: str = Query(default=""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de résultats de recherche complète."""
    results = search(q, session) if q.strip() else {"query": q, "total": 0, "campaign_hits": []}

    return templates.TemplateResponse(
        request,
        "search.html",
        {"results": results, "q": q, "current_user": current_user},
    )


@router.get("/search/quick", response_class=HTMLResponse)
def search_quick(
    request: Request,
    q: str = Query(default=""),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Fragment HTMX : dropdown de résultats rapides dans la nav.

    Retourne au maximum 5 résultats par campagne, sans pagination.
    Appelé par le champ de recherche de base.html en temps réel.
    """
    results = search(q, session) if len(q.strip()) >= 2 else {"query": q, "total": 0, "campaign_hits": []}

    return templates.TemplateResponse(
        request,
        "partials/search_dropdown.html",
        {"results": results, "q": q},
    )

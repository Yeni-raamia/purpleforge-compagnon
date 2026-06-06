"""Route du tableau de bord global.

GET /dashboard → vue d'ensemble de toutes les campagnes avec statistiques agrégées.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session

from app.database import get_session
from app.dependencies import require_user
from app.models.user import User
from app.services.dashboard import compute_dashboard

router = APIRouter(tags=["dashboard"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Tableau de bord : statistiques globales sur toutes les campagnes."""
    stats = compute_dashboard(session)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"stats": stats, "current_user": current_user},
    )

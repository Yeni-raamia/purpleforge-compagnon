"""Routes des statistiques globales."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app.dependencies import require_user
from app.models.user import User
from app.services.stats import compute_global_stats

router = APIRouter(prefix="/stats", tags=["stats"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", response_class=HTMLResponse)
def stats_page(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Page de statistiques globales : évolution, tactiques, top techniques."""
    stats = compute_global_stats(session)
    return templates.TemplateResponse(
        request,
        "stats.html",
        {"stats": stats, "current_user": current_user},
    )

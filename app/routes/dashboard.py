"""Routes globales : tableau de bord et remédiation cross-campagnes.

GET /dashboard   → vue d'ensemble de toutes les campagnes
GET /remediation → board kanban global de toutes les techniques « à construire »
"""

from datetime import date as _date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import require_user
from app.models.campaign import Campaign
from app.models.technique import TechniqueEntry, TechniqueStatus
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


@router.get("/remediation", response_class=HTMLResponse)
def global_remediation(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_user),
):
    """Board de remédiation global : toutes les techniques « à construire »,
    toutes campagnes confondues, regroupées en trois colonnes Kanban.
    """
    # Toutes les techniques « à construire » triées par attaque_id
    a_construire = session.exec(
        select(TechniqueEntry)
        .where(TechniqueEntry.status == TechniqueStatus.a_construire)
        .order_by(TechniqueEntry.attack_id)
    ).all()

    # Index des campagnes pour affichage dans les cartes
    campaigns = session.exec(select(Campaign)).all()
    camp_by_id = {c.id: c for c in campaigns}

    # Nombre de campagnes qui ont au moins une technique à construire
    camp_ids_actives = {t.campaign_id for t in a_construire}

    # Groupement par statut de remédiation
    board = {
        "en_cours": [t for t in a_construire if t.remediation_status == "en_cours"],
        "bloque":   [t for t in a_construire if t.remediation_status == "bloque"],
        "termine":  [t for t in a_construire if t.remediation_status == "termine"],
    }

    total      = len(a_construire)
    nb_termine = len(board["termine"])
    pct_done   = round(nb_termine * 100 / total) if total > 0 else 0

    return templates.TemplateResponse(
        request,
        "remediation_global.html",
        {
            "board":           board,
            "camp_by_id":      camp_by_id,
            "nb_camps":        len(camp_ids_actives),
            "total":           total,
            "pct_done":        pct_done,
            "today":           _date.today().isoformat(),
            "current_user":    current_user,
        },
    )

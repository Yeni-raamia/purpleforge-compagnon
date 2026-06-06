"""Routes liées aux techniques d'une campagne.

Gère :
- GET  /campaigns/{id}/techniques/{tech_id}/sigma → fragment HTMX : règles Sigma
- POST /campaigns/{id}/techniques/{tech_id}       → fragment HTMX : carte mise à jour
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from app.database import get_session
from app.models.technique import TechniqueEntry, TechniqueStatus
from app.services.sigma import get_rules_for_technique

router = APIRouter(prefix="/campaigns", tags=["techniques"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/{campaign_id}/techniques/{tech_id}/sigma", response_class=HTMLResponse)
def get_sigma_rules(
    campaign_id: int,
    tech_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    """Retourne un fragment HTML avec les règles Sigma pour cette technique.

    Appelé par HTMX au clic sur « Voir les détections ».
    Premier appel : déclenche le téléchargement SigmaHQ (~30s).
    Appels suivants : instantanés.
    """
    technique = session.get(TechniqueEntry, tech_id)
    if not technique or technique.campaign_id != campaign_id:
        return HTMLResponse("<p>Technique introuvable.</p>", status_code=404)

    rules = get_rules_for_technique(technique.attack_id)

    return templates.TemplateResponse(
        request,
        "campaigns/partials/sigma_rules.html",
        {"technique": technique, "rules": rules},
    )


@router.post("/{campaign_id}/techniques/{tech_id}", response_class=HTMLResponse)
def update_technique(
    campaign_id: int,
    tech_id: int,
    request: Request,
    status: str = Form(...),
    blue_note: str = Form(""),
    session: Session = Depends(get_session),
):
    """Met à jour le statut et la note blue team d'une technique.

    Retourne un fragment HTML (carte mise à jour) remplacé par HTMX.
    """
    technique = session.get(TechniqueEntry, tech_id)
    if not technique or technique.campaign_id != campaign_id:
        return HTMLResponse("<p>Technique introuvable.</p>", status_code=404)

    # Mise à jour des champs.
    try:
        technique.status = TechniqueStatus(status)
    except ValueError:
        pass  # on garde l'ancien statut si la valeur est invalide
    technique.blue_note = blue_note.strip()

    session.add(technique)
    session.commit()
    session.refresh(technique)

    # On retourne la carte mise à jour (HTMX la substitue à l'ancienne).
    return templates.TemplateResponse(
        request,
        "campaigns/partials/technique_card.html",
        {"technique": technique, "campaign_id": campaign_id},
    )
